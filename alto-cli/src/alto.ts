import { existsSync } from "node:fs";
import { join } from "node:path";
import type {
  Options as SDKOptions,
  SDKMessage,
  SDKUserMessage,
  Query,
} from "@anthropic-ai/claude-agent-sdk";
import {
  loadAgents,
  type OrchestratorMode,
  type AgentDefinition,
} from "./config/agents.js";
import { loadConfig, getCurrentMode, setCurrentMode, loadSystemPrompt } from "./config/loader.js";
import { buildHooks } from "./config/hooks.js";
import { SessionManager } from "./session/manager.js";
import {
  createInputGenerator,
  type ReplCommand,
} from "./repl/input.js";
import {
  printHeader,
  printStatus,
  printModeSwitch,
  printSessionResume,
  printSessionStart,
  printAssistant,
  printResultSummary,
  printError,
  printSuccess,
  printHelp,
} from "./repl/output.js";

type QueryFunction = (args: {
  prompt: string | AsyncIterable<SDKUserMessage>;
  options?: SDKOptions;
}) => Query;

export interface AltoOptions {
  projectDir?: string;
  mode?: OrchestratorMode;
}

/**
 * Main ALTO CLI orchestrator class.
 */
export class Alto {
  private projectDir: string;
  private currentMode: OrchestratorMode;
  private sessionManager: SessionManager;
  private abortController: AbortController | null = null;
  private query: QueryFunction | null = null;

  constructor(options: AltoOptions = {}) {
    this.projectDir = options.projectDir ?? process.cwd();
    this.currentMode = options.mode ?? getCurrentMode(this.projectDir);
    this.sessionManager = new SessionManager(this.projectDir);
  }

  /**
   * Initialize the SDK query function.
   */
  private async initSDK(): Promise<void> {
    if (this.query) return;

    try {
      // Dynamic import of SDK
      const sdk = await import("@anthropic-ai/claude-agent-sdk");
      this.query = sdk.query;
    } catch (err) {
      throw new Error(
        `Failed to load @anthropic-ai/claude-agent-sdk: ${err}`
      );
    }
  }

  /**
   * Build SDK options for the current mode.
   */
  private buildOptions(): SDKOptions {
    const config = loadConfig(this.projectDir);

    // Always use this.currentMode for system prompt to ensure consistency
    // (config.systemPrompt might be loaded from a different mode if file was stale)
    const systemPrompt = loadSystemPrompt(this.projectDir, this.currentMode);

    // Debug: show what mode and system prompt is being used
    if (process.env.ALTO_DEBUG) {
      console.error(`[ALTO DEBUG] Mode from orchestrator.json: ${config.orchestrator.orchestrator}`);
      console.error(`[ALTO DEBUG] Mode from this.currentMode: ${this.currentMode}`);
      console.error(`[ALTO DEBUG] System prompt length: ${systemPrompt.length} chars`);
      console.error(`[ALTO DEBUG] System prompt first 200 chars: ${systemPrompt.substring(0, 200)}`);
    }

    // Get agents directory - try .claude/agents/ first (deployed), then agents/ (source repo)
    let agentsDir = join(this.projectDir, ".claude", "agents");
    if (!existsSync(agentsDir)) {
      agentsDir = join(this.projectDir, "agents");
    }

    // Load agents filtered by mode
    const agents = loadAgents(agentsDir, this.currentMode);

    // Build hooks for mode
    const hooks = buildHooks(this.projectDir, this.currentMode);

    // Get session ID for resume
    const sessionId = this.sessionManager.getSessionId(this.currentMode);

    // Create abort controller
    this.abortController = new AbortController();

    const options: SDKOptions = {
      cwd: this.projectDir,
      systemPrompt: {
        type: "preset",
        preset: "claude_code",
        append: systemPrompt,
      },
      agents,
      hooks,
      settingSources: ["project", "local"],
      tools: { type: "preset", preset: "claude_code" },
      abortController: this.abortController,
    };

    if (sessionId) {
      options.resume = sessionId;
      printSessionResume(this.currentMode, sessionId);
    } else {
      printSessionStart(this.currentMode);
    }

    return options;
  }

  /**
   * Handle internal ALTO commands.
   * Returns true to continue, false to exit.
   */
  private async handleCommand(cmd: ReplCommand): Promise<boolean> {
    switch (cmd.type) {
      case "switch":
        await this.switchMode(cmd.mode);
        return true;

      case "status":
        const sessionId = this.sessionManager.getSessionId(this.currentMode);
        printStatus(this.currentMode, sessionId);
        return true;

      case "clear":
        this.sessionManager.clear(this.currentMode);
        printSuccess(`Cleared session for ${this.currentMode} mode`);
        return true;

      case "exit":
        return false;

      default:
        return true;
    }
  }

  /**
   * Switch to a different orchestrator mode.
   */
  async switchMode(newMode: OrchestratorMode): Promise<void> {
    if (newMode === this.currentMode) {
      printSuccess(`Already in ${newMode} mode`);
      return;
    }

    printModeSwitch(this.currentMode, newMode);

    // Interrupt current query if running
    if (this.abortController) {
      this.abortController.abort();
    }

    // Update mode
    const oldMode = this.currentMode;
    this.currentMode = newMode;
    setCurrentMode(this.projectDir, newMode);

    printHeader(this.currentMode);
  }

  /**
   * Run the REPL loop with streaming SDK interaction.
   */
  async run(): Promise<void> {
    await this.initSDK();

    if (!this.query) {
      printError("SDK not initialized");
      return;
    }

    printHeader(this.currentMode);
    printHelp();

    // Create input generator
    const inputGen = createInputGenerator(
      this.currentMode,
      this.handleCommand.bind(this)
    );

    // Build options and start query
    const options = this.buildOptions();

    try {
      const queryResult = this.query({
        prompt: inputGen,
        options,
      });

      // Process messages from SDK
      for await (const message of queryResult) {
        await this.handleMessage(message);
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // Normal abort during mode switch
        return;
      }
      printError(`SDK error: ${err}`);
    }
  }

  /**
   * Handle a message from the SDK.
   */
  private async handleMessage(message: SDKMessage): Promise<void> {
    switch (message.type) {
      case "system":
        if (message.subtype === "init" && message.session_id) {
          // Save session ID after initialization
          this.sessionManager.save(this.currentMode, message.session_id);
        }
        break;

      case "assistant":
        // Extract text content from assistant message
        const content = this.extractTextContent(message.message?.content);
        if (content) {
          printAssistant(content);
        }
        break;

      case "result":
        if (message.subtype === "success") {
          if (message.num_turns && message.duration_ms !== undefined) {
            printResultSummary(
              message.num_turns,
              message.duration_ms,
              message.total_cost_usd ?? 0
            );
          }
        } else if (message.is_error) {
          // Error subtypes have 'errors' array instead of 'result'
          const errorMsg = "errors" in message && Array.isArray(message.errors)
            ? message.errors.join("; ")
            : "Unknown error";
          printError(errorMsg);
        }
        break;

      default:
        // Ignore other message types for now
        break;
    }
  }

  /**
   * Extract text content from message content (may be string or content blocks).
   */
  private extractTextContent(content: unknown): string {
    if (typeof content === "string") {
      return content;
    }

    if (Array.isArray(content)) {
      return content
        .filter(
          (block): block is { type: "text"; text: string } =>
            typeof block === "object" &&
            block !== null &&
            block.type === "text" &&
            typeof block.text === "string"
        )
        .map((block) => block.text)
        .join("");
    }

    return "";
  }

  /**
   * Run a single prompt (non-interactive mode).
   */
  async runOnce(prompt: string): Promise<string> {
    await this.initSDK();

    if (!this.query) {
      throw new Error("SDK not initialized");
    }

    const options = this.buildOptions();

    let result = "";

    const queryResult = this.query({
      prompt,
      options,
    });

    for await (const message of queryResult) {
      if (message.type === "system" && message.subtype === "init") {
        if (message.session_id) {
          this.sessionManager.save(this.currentMode, message.session_id);
        }
      } else if (message.type === "result" && message.subtype === "success") {
        result = message.result ?? "";
      }
    }

    return result;
  }

  /**
   * Get current mode.
   */
  getMode(): OrchestratorMode {
    return this.currentMode;
  }

  /**
   * Get project directory.
   */
  getProjectDir(): string {
    return this.projectDir;
  }
}

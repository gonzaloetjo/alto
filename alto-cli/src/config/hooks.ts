import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import type {
  HookEvent,
  HookInput,
  HookCallback,
  HookCallbackMatcher,
  HookJSONOutput,
} from "@anthropic-ai/claude-agent-sdk";
import type { OrchestratorMode } from "./agents.js";

/**
 * Hook definitions per mode.
 * - setup: Minimal hooks (session-start for context)
 * - build: Full hooks (all validation, recording, arbiter)
 * - dev: Minimal hooks (no arbiter or heavy validation)
 */
const HOOK_CONFIG: Record<
  OrchestratorMode,
  Record<HookEvent, string[]>
> = {
  setup: {
    SessionStart: ["session-start.py"],
    SessionEnd: ["session-summary.py"],
    PostToolUse: [],
    PreToolUse: [],
    PostToolUseFailure: [],
    Notification: [],
    UserPromptSubmit: [],
    Stop: [],
    SubagentStart: [],
    SubagentStop: [],
    PreCompact: [],
    PermissionRequest: [],
  },
  build: {
    SessionStart: ["session-start.py"],
    SessionEnd: ["session-summary.py"],
    PostToolUse: [
      "tool-record.py",
      "usage-record.py",
      "changelog-check.py",
      "skill-validate.py",
      "verify-dynamic.py",
    ],
    PreToolUse: [],
    PostToolUseFailure: [],
    Notification: [],
    UserPromptSubmit: [],
    Stop: [],
    SubagentStart: [],
    SubagentStop: ["handoff-validate.py", "arbiter-scheduler.py"],
    PreCompact: [],
    PermissionRequest: ["permission-record.py"],
  },
  dev: {
    SessionStart: ["session-start.py"],
    SessionEnd: ["session-summary.py"],
    PostToolUse: ["tool-use-record.py"],
    PreToolUse: [],
    PostToolUseFailure: [],
    Notification: [],
    UserPromptSubmit: [],
    Stop: [],
    SubagentStart: [],
    SubagentStop: [],
    PreCompact: [],
    PermissionRequest: [],
  },
};

/**
 * Spawn a Python hook script and communicate via stdin/stdout.
 */
async function spawnPythonHook(
  hookPath: string,
  input: HookInput,
  projectDir: string,
  signal: AbortSignal
): Promise<HookJSONOutput> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new Error("Aborted"));
      return;
    }

    const proc = spawn("python3", [hookPath], {
      cwd: projectDir,
      env: {
        ...process.env,
        CLAUDE_PROJECT_DIR: projectDir,
      },
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      if (code !== 0) {
        // Hook failed, but we don't want to block execution
        console.error(`Hook ${hookPath} exited with code ${code}: ${stderr}`);
        resolve({ continue: true });
        return;
      }

      // Parse stdout as JSON or treat as system message
      const trimmed = stdout.trim();
      if (!trimmed) {
        resolve({ continue: true });
        return;
      }

      try {
        const result = JSON.parse(trimmed) as HookJSONOutput;
        resolve(result);
      } catch {
        // If not JSON, treat as system message
        resolve({
          continue: true,
          systemMessage: trimmed,
        });
      }
    });

    proc.on("error", (err) => {
      console.error(`Failed to spawn hook ${hookPath}:`, err);
      resolve({ continue: true });
    });

    // Handle abort
    const abortHandler = () => {
      proc.kill("SIGTERM");
      reject(new Error("Aborted"));
    };
    signal.addEventListener("abort", abortHandler, { once: true });

    // Write input to stdin
    proc.stdin.write(JSON.stringify(input));
    proc.stdin.end();
  });
}

/**
 * Create a HookCallback that spawns a Python hook script.
 */
function createHookCallback(
  hookName: string,
  hooksDir: string,
  projectDir: string
): HookCallback {
  const hookPath = join(hooksDir, hookName);

  return async (
    input: HookInput,
    _toolUseID: string | undefined,
    options: { signal: AbortSignal }
  ): Promise<HookJSONOutput> => {
    if (!existsSync(hookPath)) {
      console.warn(`Hook not found: ${hookPath}`);
      return { continue: true };
    }

    return spawnPythonHook(hookPath, input, projectDir, options.signal);
  };
}

/**
 * Build hooks configuration for the SDK based on orchestrator mode.
 */
export function buildHooks(
  projectDir: string,
  mode: OrchestratorMode
): Partial<Record<HookEvent, HookCallbackMatcher[]>> {
  // Try .claude/hooks first (deployed), then hooks/ (source repo)
  let hooksDir = join(projectDir, ".claude", "hooks");
  if (!existsSync(hooksDir)) {
    hooksDir = join(projectDir, "hooks");
  }

  if (!existsSync(hooksDir)) {
    return {};
  }

  const config = HOOK_CONFIG[mode];
  const hooks: Partial<Record<HookEvent, HookCallbackMatcher[]>> = {};

  for (const [event, hookFiles] of Object.entries(config)) {
    if (hookFiles.length === 0) continue;

    const callbacks: HookCallback[] = hookFiles
      .filter((hookName) => existsSync(join(hooksDir, hookName)))
      .map((hookName) => createHookCallback(hookName, hooksDir, projectDir));

    if (callbacks.length > 0) {
      hooks[event as HookEvent] = [{ hooks: callbacks }];
    }
  }

  return hooks;
}

/**
 * Get matchers for PostToolUse hooks based on mode.
 */
export function getPostToolUseMatchers(
  mode: OrchestratorMode
): Record<string, string[]> {
  if (mode === "build") {
    return {
      "Write|Edit": ["changelog-check.py", "skill-validate.py"],
      "Edit:*.ts|Edit:*.tsx": ["verify-dynamic.py"],
    };
  }
  return {};
}

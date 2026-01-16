import { type OrchestratorMode } from "./config/agents.js";
export interface AltoOptions {
    projectDir?: string;
    mode?: OrchestratorMode;
}
/**
 * Main ALTO CLI orchestrator class.
 */
export declare class Alto {
    private projectDir;
    private currentMode;
    private sessionManager;
    private abortController;
    private query;
    constructor(options?: AltoOptions);
    /**
     * Initialize the SDK query function.
     */
    private initSDK;
    /**
     * Build SDK options for the current mode.
     */
    private buildOptions;
    /**
     * Handle internal ALTO commands.
     * Returns true to continue, false to exit.
     */
    private handleCommand;
    /**
     * Switch to a different orchestrator mode.
     */
    switchMode(newMode: OrchestratorMode): Promise<void>;
    /**
     * Run the REPL loop with streaming SDK interaction.
     */
    run(): Promise<void>;
    /**
     * Handle a message from the SDK.
     */
    private handleMessage;
    /**
     * Extract text content from message content (may be string or content blocks).
     */
    private extractTextContent;
    /**
     * Run a single prompt (non-interactive mode).
     */
    runOnce(prompt: string): Promise<string>;
    /**
     * Get current mode.
     */
    getMode(): OrchestratorMode;
    /**
     * Get project directory.
     */
    getProjectDir(): string;
}
//# sourceMappingURL=alto.d.ts.map
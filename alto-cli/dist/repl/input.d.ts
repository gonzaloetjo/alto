import type { SDKUserMessage } from "@anthropic-ai/claude-agent-sdk";
import type { OrchestratorMode } from "../config/agents.js";
export type { SDKUserMessage };
export interface SwitchCommand {
    type: "switch";
    mode: OrchestratorMode;
}
export interface StatusCommand {
    type: "status";
}
export interface ExitCommand {
    type: "exit";
}
export interface ClearCommand {
    type: "clear";
}
export type ReplCommand = SwitchCommand | StatusCommand | ExitCommand | ClearCommand;
/**
 * Create an async generator that yields user messages from stdin.
 * Handles internal /switch, /status, /exit commands.
 */
export declare function createInputGenerator(currentMode: OrchestratorMode, onCommand: (cmd: ReplCommand) => Promise<boolean>): AsyncGenerator<SDKUserMessage, void, unknown>;
/**
 * Simple readline prompt for single input.
 */
export declare function promptUser(question: string): Promise<string>;
//# sourceMappingURL=input.d.ts.map
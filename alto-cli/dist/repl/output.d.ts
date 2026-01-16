import type { OrchestratorMode } from "../config/agents.js";
declare const colors: {
    reset: string;
    bold: string;
    dim: string;
    red: string;
    green: string;
    yellow: string;
    blue: string;
    magenta: string;
    cyan: string;
    white: string;
};
/**
 * Print a styled message.
 */
export declare function print(message: string, color?: keyof typeof colors): void;
/**
 * Print a header with mode indicator.
 */
export declare function printHeader(mode: OrchestratorMode): void;
/**
 * Print a status message.
 */
export declare function printStatus(mode: OrchestratorMode, sessionId: string | undefined): void;
/**
 * Print help for internal commands.
 */
export declare function printHelp(): void;
/**
 * Print mode switch message.
 */
export declare function printModeSwitch(from: OrchestratorMode, to: OrchestratorMode): void;
/**
 * Print session info.
 */
export declare function printSessionResume(mode: OrchestratorMode, sessionId: string): void;
/**
 * Print session start.
 */
export declare function printSessionStart(mode: OrchestratorMode): void;
/**
 * Print error message.
 */
export declare function printError(message: string): void;
/**
 * Print warning message.
 */
export declare function printWarning(message: string): void;
/**
 * Print success message.
 */
export declare function printSuccess(message: string): void;
/**
 * Print assistant message.
 */
export declare function printAssistant(content: string): void;
/**
 * Print tool use indicator.
 */
export declare function printToolUse(toolName: string, description?: string): void;
/**
 * Format cost in USD.
 */
export declare function formatCost(costUsd: number): string;
/**
 * Print result summary.
 */
export declare function printResultSummary(numTurns: number, durationMs: number, costUsd: number): void;
export {};
//# sourceMappingURL=output.d.ts.map
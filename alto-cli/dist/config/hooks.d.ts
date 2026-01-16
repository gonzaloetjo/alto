import type { HookEvent, HookCallbackMatcher } from "@anthropic-ai/claude-agent-sdk";
import type { OrchestratorMode } from "./agents.js";
/**
 * Build hooks configuration for the SDK based on orchestrator mode.
 */
export declare function buildHooks(projectDir: string, mode: OrchestratorMode): Partial<Record<HookEvent, HookCallbackMatcher[]>>;
/**
 * Get matchers for PostToolUse hooks based on mode.
 */
export declare function getPostToolUseMatchers(mode: OrchestratorMode): Record<string, string[]>;
//# sourceMappingURL=hooks.d.ts.map
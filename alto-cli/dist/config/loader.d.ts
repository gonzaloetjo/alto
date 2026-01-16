import type { OrchestratorMode } from "./agents.js";
export interface OrchestratorConfig {
    orchestrator: OrchestratorMode;
    updated_at?: string;
}
export interface PlanningConfig {
    require_approval: boolean;
    replan_strategy: "auto" | "fixed" | "none";
    fixed_batch_size: number;
    architect_model: "opus" | "sonnet";
    planner_model: "opus" | "sonnet";
}
export interface ArbiterConfig {
    max_lines_changed_without_human: number;
    max_files_changed_without_human: number;
    token_checkpoint_interval: number;
    task_checkpoint_interval: number;
    high_risk_bash_prefixes: string[];
}
export interface AltoConfig {
    orchestrator: OrchestratorConfig;
    planning: PlanningConfig;
    arbiter: ArbiterConfig;
    systemPrompt: string;
}
/**
 * Load the system prompt template for a specific mode.
 */
export declare function loadSystemPrompt(projectDir: string, mode: OrchestratorMode): string;
/**
 * Load all ALTO configuration from the project directory.
 */
export declare function loadConfig(projectDir: string): AltoConfig;
/**
 * Get the current orchestrator mode.
 */
export declare function getCurrentMode(projectDir: string): OrchestratorMode;
/**
 * Update the orchestrator mode.
 */
export declare function setCurrentMode(projectDir: string, mode: OrchestratorMode): void;
//# sourceMappingURL=loader.d.ts.map
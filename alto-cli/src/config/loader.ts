import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";
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

const DEFAULT_PLANNING_CONFIG: PlanningConfig = {
  require_approval: true,
  replan_strategy: "auto",
  fixed_batch_size: 5,
  architect_model: "opus",
  planner_model: "opus",
};

const DEFAULT_ARBITER_CONFIG: ArbiterConfig = {
  max_lines_changed_without_human: 2000,
  max_files_changed_without_human: 50,
  token_checkpoint_interval: 100000,
  task_checkpoint_interval: 3,
  high_risk_bash_prefixes: [
    "rm -rf /",
    "sudo rm",
    "dd if=",
    "mkfs",
    "> /dev/",
  ],
};

function loadJsonFile<T>(filePath: string, defaultValue: T): T {
  try {
    if (!existsSync(filePath)) {
      return defaultValue;
    }
    const content = readFileSync(filePath, "utf-8");
    return JSON.parse(content) as T;
  } catch {
    return defaultValue;
  }
}

/**
 * Load the system prompt template for a specific mode.
 */
export function loadSystemPrompt(
  projectDir: string,
  mode: OrchestratorMode
): string {
  // Try .claude/templates/ first (deployed consumer project)
  const deployedPath = join(projectDir, ".claude", "templates", `CLAUDE.md.${mode}`);
  if (existsSync(deployedPath)) {
    if (process.env.ALTO_DEBUG) {
      console.error(`[ALTO DEBUG] Loading template from: ${deployedPath}`);
    }
    return readFileSync(deployedPath, "utf-8");
  }

  // Try templates/ (ALTO source repo)
  const sourcePath = join(projectDir, "templates", `CLAUDE.md.${mode}`);
  if (existsSync(sourcePath)) {
    if (process.env.ALTO_DEBUG) {
      console.error(`[ALTO DEBUG] Loading template from: ${sourcePath}`);
    }
    return readFileSync(sourcePath, "utf-8");
  }

  // Minimal fallback
  if (process.env.ALTO_DEBUG) {
    console.error(`[ALTO DEBUG] Template not found, using fallback for mode: ${mode}`);
    console.error(`[ALTO DEBUG] Tried: ${deployedPath}`);
    console.error(`[ALTO DEBUG] Tried: ${sourcePath}`);
  }
  return `# ALTO ${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode\n\nYou are operating in ${mode} mode.`;
}

/**
 * Load all ALTO configuration from the project directory.
 */
export function loadConfig(projectDir: string): AltoConfig {
  const runsDir = join(projectDir, "runs");

  // Load orchestrator mode
  const orchestrator = loadJsonFile<OrchestratorConfig>(
    join(runsDir, "orchestrator.json"),
    { orchestrator: "setup" }
  );

  // Load planning config
  const planning = loadJsonFile<PlanningConfig>(
    join(runsDir, "planning-config.json"),
    DEFAULT_PLANNING_CONFIG
  );

  // Load arbiter config
  const arbiter = loadJsonFile<ArbiterConfig>(
    join(runsDir, "arbiter", "config.json"),
    DEFAULT_ARBITER_CONFIG
  );

  // Load system prompt for current mode
  const systemPrompt = loadSystemPrompt(projectDir, orchestrator.orchestrator);

  return {
    orchestrator,
    planning,
    arbiter,
    systemPrompt,
  };
}

/**
 * Get the current orchestrator mode.
 */
export function getCurrentMode(projectDir: string): OrchestratorMode {
  const configPath = join(projectDir, "runs", "orchestrator.json");
  const config = loadJsonFile<OrchestratorConfig>(configPath, {
    orchestrator: "setup",
  });
  if (process.env.ALTO_DEBUG) {
    console.error(`[ALTO DEBUG] getCurrentMode: reading ${configPath}`);
    console.error(`[ALTO DEBUG] getCurrentMode: orchestrator = ${config.orchestrator}`);
  }
  return config.orchestrator;
}

/**
 * Update the orchestrator mode.
 */
export function setCurrentMode(
  projectDir: string,
  mode: OrchestratorMode
): void {
  const runsDir = join(projectDir, "runs");

  // Ensure runs directory exists
  mkdirSync(runsDir, { recursive: true });

  const configPath = join(runsDir, "orchestrator.json");
  const config: OrchestratorConfig = {
    orchestrator: mode,
    updated_at: new Date().toISOString(),
  };

  writeFileSync(configPath, JSON.stringify(config, null, 2), "utf-8");
}

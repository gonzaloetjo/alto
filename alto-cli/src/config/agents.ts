import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { parseFrontmatter } from "../utils/frontmatter.js";

export type OrchestratorMode = "setup" | "build" | "dev";

export interface AgentFrontmatter {
  name: string;
  description: string;
  tools?: string | string[];  // Can be comma-separated string or array
  model?: "sonnet" | "opus" | "haiku";
  permissionMode?: "default" | "acceptEdits" | "bypassPermissions" | "plan";
  skills?: string;
}

export interface AgentDefinition {
  description: string;
  tools?: string[];
  prompt: string;
  model?: "sonnet" | "opus" | "haiku" | "inherit";
}

/**
 * Mode-based agent filtering rules:
 * - setup: Only alto-feature-finder (for codebase exploration)
 * - build: All agents except alto-dev
 * - dev: Only alto-dev
 */
const AGENT_MODE_FILTER: Record<OrchestratorMode, (name: string) => boolean> = {
  setup: (name) => name === "alto-feature-finder",
  build: (name) => name !== "alto-dev",
  dev: (name) => name === "alto-dev",
};

/**
 * Parse a single agent markdown file into an AgentDefinition.
 */
export function parseAgentFile(filePath: string): {
  name: string;
  definition: AgentDefinition;
} | null {
  let content: string;
  try {
    content = readFileSync(filePath, "utf-8");
  } catch {
    return null;
  }

  const { data, content: promptContent } =
    parseFrontmatter<AgentFrontmatter>(content);

  if (!data.name || !data.description) {
    return null;
  }

  const definition: AgentDefinition = {
    description: data.description,
    prompt: promptContent,
  };

  // Parse tools - can be array or comma-separated string
  if (data.tools) {
    if (Array.isArray(data.tools)) {
      definition.tools = data.tools;
    } else {
      definition.tools = data.tools
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
    }
  }

  // Map model
  if (data.model) {
    definition.model = data.model;
  }

  return {
    name: data.name,
    definition,
  };
}

/**
 * Load all agents from a directory and filter by mode.
 */
export function loadAgents(
  agentsDir: string,
  mode: OrchestratorMode
): Record<string, AgentDefinition> {
  const agents: Record<string, AgentDefinition> = {};
  const filter = AGENT_MODE_FILTER[mode];

  let files: string[];
  try {
    files = readdirSync(agentsDir).filter((f) => f.endsWith(".md"));
  } catch {
    console.error(`Failed to read agents directory: ${agentsDir}`);
    return agents;
  }

  for (const file of files) {
    const filePath = join(agentsDir, file);
    const result = parseAgentFile(filePath);

    if (result && filter(result.name)) {
      agents[result.name] = result.definition;
    }
  }

  return agents;
}

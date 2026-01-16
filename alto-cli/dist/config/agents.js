import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { parseFrontmatter } from "../utils/frontmatter.js";
/**
 * Mode-based agent filtering rules:
 * - setup: Only alto-feature-finder (for codebase exploration)
 * - build: All agents except alto-dev
 * - dev: Only alto-dev
 */
const AGENT_MODE_FILTER = {
    setup: (name) => name === "alto-feature-finder",
    build: (name) => name !== "alto-dev",
    dev: (name) => name === "alto-dev",
};
/**
 * Parse a single agent markdown file into an AgentDefinition.
 */
export function parseAgentFile(filePath) {
    let content;
    try {
        content = readFileSync(filePath, "utf-8");
    }
    catch {
        return null;
    }
    const { data, content: promptContent } = parseFrontmatter(content);
    if (!data.name || !data.description) {
        return null;
    }
    const definition = {
        description: data.description,
        prompt: promptContent,
    };
    // Parse tools - can be array or comma-separated string
    if (data.tools) {
        if (Array.isArray(data.tools)) {
            definition.tools = data.tools;
        }
        else {
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
export function loadAgents(agentsDir, mode) {
    const agents = {};
    const filter = AGENT_MODE_FILTER[mode];
    let files;
    try {
        files = readdirSync(agentsDir).filter((f) => f.endsWith(".md"));
    }
    catch {
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
//# sourceMappingURL=agents.js.map
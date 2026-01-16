export type OrchestratorMode = "setup" | "build" | "dev";
export interface AgentFrontmatter {
    name: string;
    description: string;
    tools?: string | string[];
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
 * Parse a single agent markdown file into an AgentDefinition.
 */
export declare function parseAgentFile(filePath: string): {
    name: string;
    definition: AgentDefinition;
} | null;
/**
 * Load all agents from a directory and filter by mode.
 */
export declare function loadAgents(agentsDir: string, mode: OrchestratorMode): Record<string, AgentDefinition>;
//# sourceMappingURL=agents.d.ts.map
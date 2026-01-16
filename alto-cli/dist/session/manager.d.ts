import type { OrchestratorMode } from "../config/agents.js";
export interface SessionInfo {
    id: string;
    mode: OrchestratorMode;
    createdAt: string;
    lastAccessedAt: string;
}
/**
 * Manages per-mode session persistence.
 * Sessions are stored in runs/sessions/{mode}.json
 */
export declare class SessionManager {
    private sessionsDir;
    constructor(projectDir: string);
    /**
     * Ensure the sessions directory exists.
     */
    private ensureDir;
    /**
     * Get the path to a session file for a mode.
     */
    private getSessionPath;
    /**
     * Get session info for a mode, or null if no session exists.
     */
    get(mode: OrchestratorMode): SessionInfo | null;
    /**
     * Get session ID for a mode, or undefined if no session exists.
     * This is the value to pass to SDK's `resume` option.
     */
    getSessionId(mode: OrchestratorMode): string | undefined;
    /**
     * Save session info for a mode.
     */
    save(mode: OrchestratorMode, sessionId: string): void;
    /**
     * Update last accessed time for a session.
     */
    touch(mode: OrchestratorMode): void;
    /**
     * Clear session for a mode (useful when starting fresh).
     */
    clear(mode: OrchestratorMode): void;
    /**
     * Clear all sessions.
     */
    clearAll(): void;
    /**
     * Get all existing sessions.
     */
    getAll(): Map<OrchestratorMode, SessionInfo>;
}
//# sourceMappingURL=manager.d.ts.map
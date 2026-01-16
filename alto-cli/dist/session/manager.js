import { existsSync, mkdirSync, readFileSync, writeFileSync, unlinkSync } from "node:fs";
import { join } from "node:path";
/**
 * Manages per-mode session persistence.
 * Sessions are stored in runs/sessions/{mode}.json
 */
export class SessionManager {
    sessionsDir;
    constructor(projectDir) {
        this.sessionsDir = join(projectDir, "runs", "sessions");
    }
    /**
     * Ensure the sessions directory exists.
     */
    ensureDir() {
        if (!existsSync(this.sessionsDir)) {
            mkdirSync(this.sessionsDir, { recursive: true });
        }
    }
    /**
     * Get the path to a session file for a mode.
     */
    getSessionPath(mode) {
        return join(this.sessionsDir, `${mode}.json`);
    }
    /**
     * Get session info for a mode, or null if no session exists.
     */
    get(mode) {
        const sessionPath = this.getSessionPath(mode);
        if (!existsSync(sessionPath)) {
            return null;
        }
        try {
            const content = readFileSync(sessionPath, "utf-8");
            return JSON.parse(content);
        }
        catch {
            return null;
        }
    }
    /**
     * Get session ID for a mode, or undefined if no session exists.
     * This is the value to pass to SDK's `resume` option.
     */
    getSessionId(mode) {
        const session = this.get(mode);
        return session?.id;
    }
    /**
     * Save session info for a mode.
     */
    save(mode, sessionId) {
        this.ensureDir();
        const existing = this.get(mode);
        const now = new Date().toISOString();
        const session = {
            id: sessionId,
            mode,
            createdAt: existing?.createdAt ?? now,
            lastAccessedAt: now,
        };
        const sessionPath = this.getSessionPath(mode);
        writeFileSync(sessionPath, JSON.stringify(session, null, 2), "utf-8");
    }
    /**
     * Update last accessed time for a session.
     */
    touch(mode) {
        const session = this.get(mode);
        if (session) {
            this.save(mode, session.id);
        }
    }
    /**
     * Clear session for a mode (useful when starting fresh).
     */
    clear(mode) {
        const sessionPath = this.getSessionPath(mode);
        if (existsSync(sessionPath)) {
            unlinkSync(sessionPath);
        }
    }
    /**
     * Clear all sessions.
     */
    clearAll() {
        const modes = ["setup", "build", "dev"];
        for (const mode of modes) {
            this.clear(mode);
        }
    }
    /**
     * Get all existing sessions.
     */
    getAll() {
        const modes = ["setup", "build", "dev"];
        const sessions = new Map();
        for (const mode of modes) {
            const session = this.get(mode);
            if (session) {
                sessions.set(mode, session);
            }
        }
        return sessions;
    }
}
//# sourceMappingURL=manager.js.map
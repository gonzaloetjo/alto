import { existsSync, mkdirSync, readFileSync, writeFileSync, unlinkSync } from "node:fs";
import { join } from "node:path";
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
export class SessionManager {
  private sessionsDir: string;

  constructor(projectDir: string) {
    this.sessionsDir = join(projectDir, "runs", "sessions");
  }

  /**
   * Ensure the sessions directory exists.
   */
  private ensureDir(): void {
    if (!existsSync(this.sessionsDir)) {
      mkdirSync(this.sessionsDir, { recursive: true });
    }
  }

  /**
   * Get the path to a session file for a mode.
   */
  private getSessionPath(mode: OrchestratorMode): string {
    return join(this.sessionsDir, `${mode}.json`);
  }

  /**
   * Get session info for a mode, or null if no session exists.
   */
  get(mode: OrchestratorMode): SessionInfo | null {
    const sessionPath = this.getSessionPath(mode);

    if (!existsSync(sessionPath)) {
      return null;
    }

    try {
      const content = readFileSync(sessionPath, "utf-8");
      return JSON.parse(content) as SessionInfo;
    } catch {
      return null;
    }
  }

  /**
   * Get session ID for a mode, or undefined if no session exists.
   * This is the value to pass to SDK's `resume` option.
   */
  getSessionId(mode: OrchestratorMode): string | undefined {
    const session = this.get(mode);
    return session?.id;
  }

  /**
   * Save session info for a mode.
   */
  save(mode: OrchestratorMode, sessionId: string): void {
    this.ensureDir();

    const existing = this.get(mode);
    const now = new Date().toISOString();

    const session: SessionInfo = {
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
  touch(mode: OrchestratorMode): void {
    const session = this.get(mode);
    if (session) {
      this.save(mode, session.id);
    }
  }

  /**
   * Clear session for a mode (useful when starting fresh).
   */
  clear(mode: OrchestratorMode): void {
    const sessionPath = this.getSessionPath(mode);
    if (existsSync(sessionPath)) {
      unlinkSync(sessionPath);
    }
  }

  /**
   * Clear all sessions.
   */
  clearAll(): void {
    const modes: OrchestratorMode[] = ["setup", "build", "dev"];
    for (const mode of modes) {
      this.clear(mode);
    }
  }

  /**
   * Get all existing sessions.
   */
  getAll(): Map<OrchestratorMode, SessionInfo> {
    const modes: OrchestratorMode[] = ["setup", "build", "dev"];
    const sessions = new Map<OrchestratorMode, SessionInfo>();

    for (const mode of modes) {
      const session = this.get(mode);
      if (session) {
        sessions.set(mode, session);
      }
    }

    return sessions;
  }
}

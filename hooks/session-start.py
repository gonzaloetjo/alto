#!/usr/bin/env python3
"""
SessionStart hook for LCA protocol.

Provides minimal context injection on session start:
- Arbiter alerts (BLOCKED state warning) - critical, needs immediate attention
- One-line state summary - saves a tool call

Does NOT duplicate:
- Git status (already provided by Claude Code)
- Full state.json reading (CLAUDE.md instructs Claude to read it)
- Handoff content (CLAUDE.md instructs Claude to read it)

Also logs session starts to runs/sessions/starts.jsonl for auditing.
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_json(p: Path, default=None):
    """Load JSON file with fallback."""
    if default is None:
        default = {}
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def get_git_branch(cwd: Path) -> str:
    """Get current git branch name."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(cwd),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""


def main():
    hook = json.load(sys.stdin)
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    runs = project_dir / "runs"

    # Load LCA state
    state = load_json(runs / "state.json")
    if not state:
        # No LCA protocol active - skip context injection
        return

    # Check for arbiter pending (BLOCKED state)
    arbiter_pending = (runs / "arbiter" / "pending.json").exists()
    arbiter_decision = load_json(runs / "arbiter" / "decision.json")

    phase = state.get("phase", "UNKNOWN")
    completed = state.get("completed_task_ids", [])

    # Build context message - ONLY what Claude wouldn't get otherwise
    context_parts = []

    # 1. BLOCKED/arbiter alerts (critical - needs immediate attention)
    if phase == "BLOCKED" or arbiter_pending or arbiter_decision.get("needs_human"):
        context_parts.append("## LCA ARBITER ALERT")
        context_parts.append("")
        if arbiter_pending:
            context_parts.append("- `runs/arbiter/pending.json` exists - run arbiter check")
        if arbiter_decision.get("needs_human"):
            reason = arbiter_decision.get("reason", "see decision.json")
            context_parts.append(f"- Human review required: {reason}")
        if phase == "BLOCKED":
            context_parts.append("- Phase is BLOCKED - see `runs/notes.md` for details")
        context_parts.append("")

    # 2. Minimal state summary (one line) - only if protocol is active
    if state.get("protocol") == "lca-v1":
        task_info = f", task={state['current_task_id']}" if state.get("current_task_id") else ""
        role_info = f", role={state['current_role']}" if state.get("current_role") else ""
        context_parts.append(f"[LCA: phase={phase}{task_info}{role_info}, completed={len(completed)}]")
        context_parts.append("")

    # Log session start for auditing
    git_branch = get_git_branch(project_dir)
    log_dir = runs / "sessions"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_record = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "session_id": hook.get("session_id"),
        "is_resume": hook.get("resume", False),
        "phase": phase,
        "current_task_id": state.get("current_task_id"),
        "current_role": state.get("current_role"),
        "completed_tasks": len(completed),
        "git_branch": git_branch,
        "arbiter_pending": arbiter_pending,
    }
    with (log_dir / "starts.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_record, ensure_ascii=False) + "\n")

    # Output context for Claude to see
    if context_parts:
        print("\n".join(context_parts))


if __name__ == "__main__":
    main()

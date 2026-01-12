#!/usr/bin/env python3
"""
Stop hook: writes session summary for easier resume.

Creates runs/sessions/<session_id>-summary.md with:
- Session metadata
- Files modified (from tool log)
- Current LCA state
- Last actions

This summary can be referenced by SessionStart on resume.
"""
import json
import os
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


def get_recent_tool_actions(tool_log: Path, limit: int = 20) -> list[dict]:
    """Get recent tool actions from log."""
    if not tool_log.exists():
        return []

    actions = []
    try:
        with tool_log.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    actions.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []

    return actions[-limit:]


def extract_files_modified(actions: list[dict]) -> list[str]:
    """Extract unique files modified from tool actions."""
    files = set()
    for action in actions:
        tool = action.get("tool_name", "")
        if tool in ("Edit", "Write"):
            path = action.get("file_path", "")
            if path:
                files.add(path)
        elif tool == "Bash":
            cmd = action.get("command", "")
            # Detect file-creating commands
            if any(x in cmd for x in ["touch ", "mkdir ", "cp ", "mv "]):
                files.add(f"(bash) {cmd[:50]}")
    return sorted(files)


def format_actions_summary(actions: list[dict]) -> str:
    """Format recent actions as readable summary."""
    lines = []
    for action in actions[-10:]:  # Last 10 only
        tool = action.get("tool_name", "?")
        success = "✓" if action.get("success", True) else "✗"

        if tool == "Bash":
            cmd = action.get("command", "")[:60]
            is_check = action.get("is_check_command", False)
            check_mark = " (check)" if is_check else ""
            lines.append(f"  {success} Bash: {cmd}{check_mark}")
        elif tool in ("Edit", "Write"):
            path = action.get("file_path", "")
            # Shorten path
            if len(path) > 50:
                path = "..." + path[-47:]
            lines.append(f"  {success} {tool}: {path}")
        else:
            lines.append(f"  {success} {tool}")

    return "\n".join(lines) if lines else "  (no recent actions)"


def main():
    hook = json.load(sys.stdin)

    session_id = hook.get("session_id", "unknown")
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    runs = project_dir / "runs"

    # Load state
    state = load_json(runs / "state.json")
    if not state.get("protocol"):
        # Not an LCA project, skip
        return

    # Get recent tool actions
    actions = get_recent_tool_actions(runs / "tools" / "usage.jsonl")
    files_modified = extract_files_modified(actions)

    # Build summary
    now = datetime.utcnow().isoformat() + "Z"
    phase = state.get("phase", "UNKNOWN")
    task_id = state.get("current_task_id")
    role = state.get("current_role")
    completed = state.get("completed_task_ids", [])

    summary_lines = [
        f"# Session Summary",
        f"",
        f"**Session ID:** `{session_id}`",
        f"**Ended:** {now}",
        f"",
        f"## LCA State",
        f"",
        f"- **Phase:** `{phase}`",
        f"- **Current Task:** `{task_id or 'none'}`",
        f"- **Current Role:** `{role or 'none'}`",
        f"- **Completed Tasks:** {len(completed)}",
        f"",
    ]

    if files_modified:
        summary_lines.extend([
            f"## Files Modified",
            f"",
        ])
        for f in files_modified[:15]:  # Limit to 15
            summary_lines.append(f"- `{f}`")
        if len(files_modified) > 15:
            summary_lines.append(f"- ... and {len(files_modified) - 15} more")
        summary_lines.append("")

    summary_lines.extend([
        f"## Recent Actions",
        f"",
        format_actions_summary(actions),
        f"",
    ])

    # Check for any failures
    failures = [a for a in actions if not a.get("success", True)]
    if failures:
        summary_lines.extend([
            f"## Failures Detected",
            f"",
            f"{len(failures)} tool executions failed in this session.",
            f"Check `runs/tools/usage.jsonl` for details.",
            f"",
        ])

    # Write summary
    sessions_dir = runs / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    summary_path = sessions_dir / f"{session_id}-summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    # Also update a "latest" symlink/file for easy access
    latest_path = sessions_dir / "latest-summary.md"
    latest_path.write_text("\n".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    main()

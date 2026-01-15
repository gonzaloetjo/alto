#!/usr/bin/env python3
"""
Stop hook: writes session summary for easier resume.

Creates runs/sessions/<session_id>-summary.md with:
- Session metadata
- Files modified (from tool log)
- Current ALTO state
- Last actions
- Handoff summaries (for cross-session context)

This summary can be referenced by SessionStart on resume.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from hook_utils import log_event, safe_hook


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


def check_changelog_reminder(files_modified: list[str]) -> list[str]:
    """Check if key files were modified without CHANGELOG update.

    Returns reminder lines if documentation may need updating.
    """
    # Key file patterns that should trigger CHANGELOG reminder
    key_patterns = [
        "templates/CLAUDE.md",
        "devenv.nix",
        "agents/",
        "hooks/",
        "skills/",
        "ARCHITECTURE.md",
    ]

    changelog_modified = any("CHANGELOG.md" in f for f in files_modified)
    key_files_modified = []

    for f in files_modified:
        for pattern in key_patterns:
            if pattern in f:
                key_files_modified.append(f)
                break

    if key_files_modified and not changelog_modified:
        return [
            "## Documentation Reminder",
            "",
            "Key files were modified without CHANGELOG update:",
            "",
        ] + [f"- `{f}`" for f in key_files_modified[:5]] + [
            "",
            "**Consider updating:**",
            "- `CHANGELOG.md` (if user-facing change)",
            "- `docs/dev/session-*.md` (if closing issues)",
            "",
        ]

    return []


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


def get_handoff_summaries(handoffs_dir: Path, completed_tasks: list[str]) -> list[dict]:
    """Extract summaries from handoff files for completed tasks.

    Aggregates handoffs at session end for cross-session context.
    """
    summaries = []

    for task_id in completed_tasks[-10:]:  # Last 10 tasks max
        handoff_path = handoffs_dir / f"{task_id}.md"
        if not handoff_path.exists():
            continue

        try:
            content = handoff_path.read_text(encoding="utf-8")

            # Extract summary section (between ## Summary and next ##)
            summary_text = ""
            in_summary = False
            for line in content.splitlines():
                if line.lower().startswith("## summary"):
                    in_summary = True
                    continue
                elif line.startswith("## ") and in_summary:
                    break
                elif in_summary:
                    summary_text += line + "\n"

            # Extract files section
            files = []
            in_files = False
            for line in content.splitlines():
                if "## files" in line.lower():
                    in_files = True
                    continue
                elif line.startswith("## ") and in_files:
                    break
                elif in_files and line.strip().startswith("- "):
                    files.append(line.strip()[2:].strip("`"))

            summaries.append({
                "task_id": task_id,
                "summary": summary_text.strip()[:200],  # Truncate
                "files": files[:5],  # Max 5 files
            })
        except Exception:
            continue

    return summaries


def format_handoff_section(summaries: list[dict]) -> list[str]:
    """Format handoff summaries for the session summary."""
    if not summaries:
        return []

    lines = [
        "## Task Handoffs",
        "",
        "Summary of completed tasks (for cross-session context):",
        "",
    ]

    for s in summaries:
        lines.append(f"### {s['task_id']}")
        if s["summary"]:
            lines.append(f"{s['summary'][:150]}...")
        if s["files"]:
            lines.append(f"Files: {', '.join(f'`{f}`' for f in s['files'][:3])}")
        lines.append("")

    return lines


@safe_hook("session-summary")
def main():
    hook = json.load(sys.stdin)

    session_id = hook.get("session_id", "unknown")
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    runs = project_dir / "runs"

    # Load state
    state = load_json(runs / "state.json")
    if not state.get("protocol"):
        # Not an ALTO project, skip
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
        f"## ALTO State",
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

    # Add handoff summaries for cross-session context
    if completed:
        handoff_summaries = get_handoff_summaries(runs / "handoffs", completed)
        summary_lines.extend(format_handoff_section(handoff_summaries))

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

    # Check for CHANGELOG reminder
    changelog_reminder = check_changelog_reminder(files_modified)
    if changelog_reminder:
        summary_lines.extend(changelog_reminder)

    # Write summary
    sessions_dir = runs / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    summary_path = sessions_dir / f"{session_id}-summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    # Also update a "latest" symlink/file for easy access
    latest_path = sessions_dir / "latest-summary.md"
    latest_path.write_text("\n".join(summary_lines), encoding="utf-8")

    # Log to unified event log
    log_event(
        "session_end",
        {
            "files_modified_count": len(files_modified),
            "files_modified": files_modified[:10],  # First 10
            "completed_tasks_count": len(completed),
            "failures_count": len(failures),
            "has_changelog_reminder": bool(changelog_reminder),
        },
        project_dir=project_dir,
        session_id=session_id,
    )


if __name__ == "__main__":
    main()

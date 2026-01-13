#!/usr/bin/env python3
"""
SubagentStop hook: validates handoff completeness after role agents finish.

Deterministic validation:
- Handoff file exists
- Required sections present
- Files touched are in allowed paths
- State consistency

Returns error JSON to block if validation fails.
"""
import json
import os
import sys
from pathlib import Path

from hook_utils import safe_hook


def load_state(project_dir: Path) -> dict:
    """Load ALTO state."""
    state_file = project_dir / "runs" / "state.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_tool_usage(project_dir: Path) -> list[dict]:
    """Load tool usage records from current session."""
    usage_file = project_dir / "runs" / "tools" / "usage.jsonl"
    if not usage_file.exists():
        return []
    records = []
    try:
        for line in usage_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    except Exception:
        pass
    return records


def validate_handoff(project_dir: Path, task_id: str) -> list[str]:
    """Validate handoff file exists and has required sections."""
    errors = []
    handoff_path = project_dir / "runs" / "handoffs" / f"task-{task_id}.md"

    if not handoff_path.exists():
        errors.append(f"Missing handoff: runs/handoffs/task-{task_id}.md")
        return errors

    content = handoff_path.read_text(encoding="utf-8")

    # Required sections (case-insensitive check)
    required_sections = {
        "summary": ["## summary", "## task summary", "# summary"],
        "files": ["## files", "## files touched", "## files changed"],
        "verify": ["## verify", "## verification", "## how to verify"],
    }

    content_lower = content.lower()
    for section_name, patterns in required_sections.items():
        if not any(p in content_lower for p in patterns):
            errors.append(f"Handoff missing section: {section_name}")

    # Check handoff isn't empty/stub
    if len(content.strip()) < 100:
        errors.append("Handoff appears incomplete (< 100 chars)")

    return errors


def validate_file_locations(project_dir: Path, task_id: str, allowed_paths: list[str]) -> list[str]:
    """Validate files touched are in allowed paths."""
    errors = []

    if not allowed_paths:
        return errors  # No restrictions configured

    # Get files touched from tool usage
    records = load_tool_usage(project_dir)
    task_records = [r for r in records if r.get("task_id") == task_id]

    touched_files = set()
    for record in task_records:
        if record.get("tool_name") in ("Write", "Edit"):
            file_path = record.get("file_path", "")
            if file_path:
                touched_files.add(file_path)

    # Check each file against allowed paths
    for file_path in touched_files:
        rel_path = file_path
        # Convert to relative if absolute
        try:
            rel_path = str(Path(file_path).relative_to(project_dir))
        except ValueError:
            pass

        # Check if path matches any allowed pattern
        allowed = False
        for pattern in allowed_paths:
            if pattern.endswith("/**"):
                prefix = pattern[:-3]
                if rel_path.startswith(prefix):
                    allowed = True
                    break
            elif rel_path == pattern or rel_path.startswith(pattern + "/"):
                allowed = True
                break

        if not allowed:
            errors.append(f"File outside allowed_paths: {rel_path}")

    # Check protocol files weren't touched
    protocol_files = ["CLAUDE.md", "ARCHITECTURE.md", ".claude/"]
    for file_path in touched_files:
        rel_path = str(file_path)
        try:
            rel_path = str(Path(file_path).relative_to(project_dir))
        except ValueError:
            pass

        for protected in protocol_files:
            if rel_path == protected or rel_path.startswith(protected):
                errors.append(f"Protected file modified: {rel_path}")

    return errors


def validate_state_consistency(project_dir: Path, state: dict, task_id: str) -> list[str]:
    """Validate state.json is consistent."""
    errors = []

    current_task = state.get("current_task_id")
    if current_task and current_task != task_id:
        errors.append(f"State mismatch: current_task_id={current_task}, expected={task_id}")

    phase = state.get("phase")
    valid_phases = ["PLANNING", "EXECUTING", "REVIEWING", "BLOCKED"]
    if phase and phase not in valid_phases:
        errors.append(f"Invalid phase in state: {phase}")

    return errors


@safe_hook("handoff-validate")
def main():
    hook_input = json.load(sys.stdin)

    # Only validate after role agents (not system agents)
    agent_name = hook_input.get("agent_name", "")
    system_agents = ["alto-arbiter", "alto-gitops", "alto-reviewer"]
    if agent_name in system_agents:
        # Skip validation for system agents
        return

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    state = load_state(project_dir)

    task_id = state.get("current_task_id")
    if not task_id:
        # No active task, skip validation
        return

    # Collect all validation errors
    errors = []

    # 1. Validate handoff
    errors.extend(validate_handoff(project_dir, task_id))

    # 2. Validate file locations (if allowed_paths configured)
    allowed_paths = state.get("allowed_paths", [])
    errors.extend(validate_file_locations(project_dir, task_id, allowed_paths))

    # 3. Validate state consistency
    errors.extend(validate_state_consistency(project_dir, state, task_id))

    # Output result
    if errors:
        # Return error to block continuation
        result = {
            "status": "VIOLATION",
            "task_id": task_id,
            "errors": errors,
            "message": f"Handoff validation failed: {len(errors)} issue(s) found",
        }
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)
    else:
        # Validation passed - silent success
        pass


if __name__ == "__main__":
    main()

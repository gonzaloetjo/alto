#!/usr/bin/env python3
"""
PostToolUse hook: auto-creates handoff template when current_handoff is set in state.json.

Triggers on Edit/Write to state.json. Creates template only if:
1. current_handoff path is set in state.json
2. The handoff file doesn't already exist
"""
import json
import os
import sys
from pathlib import Path

from hook_utils import safe_hook

TEMPLATE = '''# Handoff: {task_id}

## Summary
<!-- What was accomplished -->

## Files Touched
<!-- List files modified -->

## How to Verify
<!-- Commands or manual checks -->
'''


@safe_hook("handoff-template")
def main():
    hook_input = json.load(sys.stdin)
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only trigger on Edit/Write
    if tool_name not in ("Edit", "Write"):
        return

    # Only trigger for state.json
    file_path = tool_input.get("file_path", "")
    if not file_path.endswith("state.json"):
        return

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    state_file = project_dir / "runs" / "state.json"

    if not state_file.exists():
        return

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return

    handoff_path = state.get("current_handoff")
    if not handoff_path:
        return

    # Resolve full path
    full_path = project_dir / handoff_path

    # Don't overwrite existing handoff
    if full_path.exists():
        return

    # Get task_id for template
    task_id = state.get("current_task_id", "unknown")

    # Create parent directory if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Write template
    full_path.write_text(TEMPLATE.format(task_id=task_id), encoding="utf-8")


if __name__ == "__main__":
    main()

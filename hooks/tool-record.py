#!/usr/bin/env python3
"""
PostToolUse hook: logs tool executions with outcomes.

Replaces PreToolUse logging - captures everything in one place:
- What tool was called
- What input was given
- What the result was
- Success/failure status

Writes to runs/tools/usage.jsonl tagged with current task/role.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def load_state(project_dir: Path) -> dict:
    """Load LCA state."""
    p = project_dir / "runs" / "state.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def extract_exit_code(tool_result: str) -> int | None:
    """Try to extract exit code from Bash tool result."""
    if not tool_result:
        return None
    # Bash tool typically shows exit code in output
    # Look for common patterns
    if "exit code" in tool_result.lower():
        for line in tool_result.splitlines():
            if "exit code" in line.lower():
                parts = line.split()
                for p in parts:
                    if p.isdigit():
                        return int(p)
    return None


def is_check_command(tool_input: dict) -> bool:
    """Detect if this is a check_command execution."""
    cmd = tool_input.get("command", "")
    check_patterns = ["make check", "pytest", "npm test", "npm run test", "npm run build"]
    return any(p in cmd for p in check_patterns)


def main():
    hook = json.load(sys.stdin)

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    state = load_state(project_dir)

    tool_name = hook.get("tool_name", "")
    tool_input = hook.get("tool_input", {})
    tool_result = hook.get("tool_result", "")

    # Determine success - tool_result being present usually means success
    # For Bash, check for error indicators
    is_error = False
    if tool_name == "Bash":
        error_indicators = ["error:", "Error:", "ERROR", "failed", "Failed", "FAILED", "exit code 1", "command not found"]
        is_error = any(ind in str(tool_result) for ind in error_indicators)

    # Build record
    record = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "tool_name": tool_name,
        "tool_use_id": hook.get("tool_use_id"),
        "session_id": hook.get("session_id"),
        # LCA context
        "task_id": state.get("current_task_id"),
        "role": state.get("current_role"),
        "phase": state.get("phase"),
        # Outcome
        "success": not is_error,
    }

    # For Bash, include command (but truncate long results)
    if tool_name == "Bash":
        record["command"] = tool_input.get("command", "")[:500]
        record["is_check_command"] = is_check_command(tool_input)

        # Include truncated result for errors or check commands
        if is_error or record["is_check_command"]:
            result_str = str(tool_result)[:1000]
            record["result_preview"] = result_str

    # For file operations, just log the path
    elif tool_name in ("Read", "Write", "Edit"):
        record["file_path"] = tool_input.get("file_path", "")

    # Write log
    out_dir = project_dir / "runs" / "tools"
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "usage.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

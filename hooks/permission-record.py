#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def load_state(project_dir: Path):
    p = project_dir / "runs" / "state.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def main():
    hook = json.load(sys.stdin)

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    state = load_state(project_dir)

    out_dir = project_dir / "runs" / "permissions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "requests.jsonl"

    record = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "hook_event_name": hook.get("hook_event_name"),
        "session_id": hook.get("session_id"),
        "permission_mode": hook.get("permission_mode"),
        "current_task_id": state.get("current_task_id"),
        "current_role": state.get("current_role"),
    }

    # PermissionRequest typically includes tool_name + tool_input (similar to PreToolUse),
    # Notification includes message + notification_type.
    for k in ["tool_name", "tool_input", "tool_use_id", "notification_type", "message", "cwd", "transcript_path"]:
        if k in hook:
            record[k] = hook.get(k)

    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()

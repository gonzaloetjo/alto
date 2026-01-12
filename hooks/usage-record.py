#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def read_jsonl_last_usage(transcript_path: str):
    p = Path(os.path.expanduser(transcript_path))
    if not p.exists():
        return None

    last_usage = None
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            usage = (obj.get("message") or {}).get("usage")
            if isinstance(usage, dict):
                last_usage = usage
    return last_usage

def safe_int(x):
    try:
        return int(x)
    except Exception:
        return 0

def main():
    hook = json.load(sys.stdin)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    state_path = Path(project_dir) / "runs" / "state.json"

    state = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    transcript_path = hook.get("transcript_path")
    usage = read_jsonl_last_usage(transcript_path) if transcript_path else None

    out_dir = Path(project_dir) / "runs" / "usage"
    out_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "hook_event_name": hook.get("hook_event_name"),
        "session_id": hook.get("session_id"),
        "permission_mode": hook.get("permission_mode"),
        "transcript_path": transcript_path,

        # tie usage to your orchestration state
        "current_task_id": state.get("current_task_id"),
        "current_role": state.get("current_role"),
    }

    if isinstance(usage, dict):
        record["usage"] = {
            "input_tokens": safe_int(usage.get("input_tokens")),
            "output_tokens": safe_int(usage.get("output_tokens")),
            "cache_read_input_tokens": safe_int(usage.get("cache_read_input_tokens") or usage.get("cache_read_tokens")),
            "cache_creation_input_tokens": safe_int(usage.get("cache_creation_input_tokens") or usage.get("cache_creation_tokens")),
        }

    with (out_dir / "usage.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()

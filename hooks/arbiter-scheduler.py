#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

DEFAULT_CFG = {
    "protocol": "lca-arbiter-v1",
    "trigger_after_tokens": 100000,
    "trigger_after_minutes": 20,
    "trigger_after_tasks": 1,
    "max_files_changed_without_human": 25,
    "max_lines_changed_without_human": 800,
    "max_permission_prompts_between_checkpoints": 3,
    "high_risk_bash_prefixes": ["rm ", "sudo ", "curl ", "wget ", "ssh ", "scp ", "dd "],
    "stop_run_on_human_needed": True,
}

def sh(cmd: list[str], cwd: Path) -> str:
    try:
        return subprocess.check_output(cmd, cwd=str(cwd), stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""

def load_json(p: Path, default):
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def sum_tokens(usage_file: Path) -> int:
    if not usage_file.exists():
        return 0
    total = 0
    with usage_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            usage = obj.get("usage") or {}
            total += int(usage.get("input_tokens") or 0)
            total += int(usage.get("output_tokens") or 0)
            total += int(usage.get("cache_read_input_tokens") or 0)
            total += int(usage.get("cache_creation_input_tokens") or 0)
    return total

def git_numstat(cwd: Path) -> dict:
    out1 = sh(["git", "diff", "--numstat"], cwd)
    out2 = sh(["git", "diff", "--numstat", "--staged"], cwd)
    added = removed = files = 0

    def parse(blob: str):
        nonlocal added, removed, files
        for line in blob.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            a, r, _path = parts[0], parts[1], parts[2]
            if a != "-" and r != "-":
                added += int(a)
                removed += int(r)
            files += 1

    if out1:
        parse(out1)
    if out2:
        parse(out2)

    return {"files": files, "lines_added": added, "lines_removed": removed}

def count_since(jsonl_file: Path, since_epoch: int) -> int:
    """Count records in a JSONL file since a given epoch."""
    if not jsonl_file.exists():
        return 0
    n = 0
    with jsonl_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            ts = obj.get("ts", "")
            try:
                epoch = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
            except Exception:
                continue
            if epoch > since_epoch:
                n += 1
    return n

def main():
    hook = json.load(sys.stdin)
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))

    runs = project_dir / "runs"
    state = load_json(runs / "state.json", {})

    # Hard rule: never schedule mid-task
    if state.get("phase") != "BETWEEN_TASKS":
        return

    arb_dir = runs / "arbiter"
    arb_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_json(arb_dir / "config.json", DEFAULT_CFG)
    arb_state = load_json(arb_dir / "state.json", {"last_checkpoint_epoch": 0, "last_checkpoint_tokens": 0})

    now_epoch = int(time.time())
    total_tokens = sum_tokens(runs / "usage" / "usage.jsonl")
    dt_tokens = total_tokens - int(arb_state.get("last_checkpoint_tokens") or 0)

    # Handle first-run case: if epoch is 0, treat as just happened (no time elapsed)
    last_checkpoint_epoch = int(arb_state.get("last_checkpoint_epoch") or 0)
    if last_checkpoint_epoch == 0:
        dt_minutes = 0.0  # First run, no time elapsed since "last checkpoint"
    else:
        dt_minutes = (now_epoch - last_checkpoint_epoch) / 60.0

    # Task-based trigger: check if N tasks completed since last checkpoint
    tasks_completed = len(state.get("completed_task_ids") or [])
    tasks_at_last = int(arb_state.get("last_checkpoint_tasks") or 0)
    tasks_since = tasks_completed - tasks_at_last

    # Trigger if ANY threshold exceeded
    token_threshold_exceeded = dt_tokens >= int(cfg.get("trigger_after_tokens", 100000))
    time_threshold_exceeded = dt_minutes >= float(cfg.get("trigger_after_minutes", 20))
    task_threshold_exceeded = tasks_since >= int(cfg.get("trigger_after_tasks", 1))

    if not (token_threshold_exceeded or time_threshold_exceeded or task_threshold_exceeded):
        return

    # Snapshot for arbiter agent
    snapshot = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "hook_event_name": hook.get("hook_event_name"),
        "current_task_id": state.get("current_task_id"),
        "completed_task_ids_count": tasks_completed,
        "tokens_total": total_tokens,
        "tokens_since_last_checkpoint": dt_tokens,
        "minutes_since_last_checkpoint": round(dt_minutes, 1),
        "tasks_since_last_checkpoint": tasks_since,
        "trigger_reason": "tokens" if token_threshold_exceeded else ("time" if time_threshold_exceeded else "tasks"),
        "git": {
            "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], project_dir),
            "head": sh(["git", "rev-parse", "HEAD"], project_dir),
            "status_porcelain_lines": len(sh(["git", "status", "--porcelain"], project_dir).splitlines()),
            "diff_stat": sh(["git", "diff", "--stat"], project_dir),
        },
        "diff_metrics": git_numstat(project_dir),
        "tool_invocations_since_last_checkpoint": count_since(
            runs / "tools" / "usage.jsonl",
            int(arb_state.get("last_checkpoint_epoch") or 0),
        ),
        "permission_prompts_since_last_checkpoint": count_since(
            runs / "permissions" / "requests.jsonl",
            int(arb_state.get("last_checkpoint_epoch") or 0),
        ),
        "thresholds": {
            "max_files_changed_without_human": cfg["max_files_changed_without_human"],
            "max_lines_changed_without_human": cfg["max_lines_changed_without_human"],
            "max_permission_prompts_between_checkpoints": cfg["max_permission_prompts_between_checkpoints"],
        },
    }

    (arb_dir / "pending.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Hook utilities for ALTO.
Provides error handling, logging, and common patterns for hooks.
"""

import json
import sys
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable


def get_project_dir() -> Path:
    """Get the project directory from environment or current working directory."""
    import os
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))


def log_error(error: Exception, hook_name: str, context: dict[str, Any] | None = None) -> None:
    """Log an error to runs/errors.jsonl for debugging.

    Args:
        error: The exception that occurred
        hook_name: Name of the hook that failed
        context: Additional context (input data, state, etc.)
    """
    project_dir = get_project_dir()
    errors_file = project_dir / "runs" / "errors.jsonl"

    # Ensure runs directory exists
    errors_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "hook": hook_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context or {},
    }

    try:
        with open(errors_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        # If we can't log, print to stderr as fallback
        print(f"[ALTO] Hook error ({hook_name}): {error}", file=sys.stderr)


def safe_hook(hook_name: str) -> Callable:
    """Decorator that wraps a hook's main function with error handling.

    Usage:
        @safe_hook("session-start")
        def main():
            # hook logic here
            pass

    Benefits:
        - Catches all exceptions
        - Logs errors to runs/errors.jsonl
        - Prints user-friendly message to stderr
        - Returns exit code 0 so Claude Code continues
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                log_error(e, hook_name, {
                    "args": [str(a) for a in args],
                    "kwargs": {k: str(v) for k, v in kwargs.items()},
                })

                # Print friendly message
                print(f"[ALTO] {hook_name} hook encountered an error: {e}", file=sys.stderr)
                print(f"[ALTO] Details logged to runs/errors.jsonl", file=sys.stderr)

                # Return gracefully (don't crash Claude Code)
                return None
        return wrapper
    return decorator


def read_json_safe(path: Path, default: Any = None) -> Any:
    """Safely read a JSON file, returning default if it fails."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        pass
    return default


def write_json_safe(path: Path, data: Any) -> bool:
    """Safely write a JSON file, returning success status."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return True
    except IOError:
        return False


def get_state(project_dir: Path | None = None) -> dict:
    """Read runs/state.json safely."""
    if project_dir is None:
        project_dir = get_project_dir()
    return read_json_safe(project_dir / "runs" / "state.json", {})


def is_debug_mode(project_dir: Path | None = None) -> bool:
    """Check if ALTO debug mode is enabled.

    Reads runs/debug-config.json to determine if debug logging is active.
    """
    if project_dir is None:
        project_dir = get_project_dir()
    config = read_json_safe(project_dir / "runs" / "debug-config.json", {})
    return config.get("debug", False)


# =============================================================================
# Event Logging - Unified log for meta-development analysis
# =============================================================================

# Event types for the unified event log
EVENT_TYPES = [
    "agent_dispatch",      # Agent was called
    "agent_complete",      # Agent finished
    "handoff",             # Handoff between agents
    "decision",            # Plan approval, code acceptance, etc.
    "phase_change",        # Orchestrator phase transition
    "verification",        # Typecheck, lint, test result
    "arbiter_checkpoint",  # Arbiter review point
    "tool_use",            # Tool execution (summary)
    "session_start",       # Session began
    "session_end",         # Session ended
    "error",               # Error occurred
]


def log_event(
    event_type: str,
    data: dict[str, Any],
    project_dir: Path | None = None,
    session_id: str | None = None,
) -> bool:
    """Log an event to runs/logs/events.jsonl (only in debug mode).

    Args:
        event_type: One of EVENT_TYPES
        data: Event-specific data
        project_dir: Project directory (defaults to CLAUDE_PROJECT_DIR)
        session_id: Optional session ID to include

    Returns:
        True if logged successfully, False if debug mode disabled

    Example:
        log_event("agent_dispatch", {
            "agent": "alto-backend",
            "task_id": "task-001",
            "reason": "implement backend task",
        })
    """
    if project_dir is None:
        project_dir = get_project_dir()

    # Only log if debug mode is enabled
    if not is_debug_mode(project_dir):
        return False

    logs_dir = project_dir / "runs" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Get current ALTO state for context
    state = get_state(project_dir)

    event = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        "session_id": session_id,
        # ALTO context
        "task_id": state.get("current_task_id"),
        "role": state.get("current_role"),
        "phase": state.get("phase"),
        # Event-specific data
        **data,
    }

    try:
        with (logs_dir / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return True
    except IOError:
        return False


def get_events(
    project_dir: Path | None = None,
    event_type: str | None = None,
    limit: int = 100,
    session_id: str | None = None,
) -> list[dict]:
    """Read events from runs/logs/events.jsonl.

    Args:
        project_dir: Project directory
        event_type: Filter by event type
        limit: Max events to return (most recent)
        session_id: Filter by session ID

    Returns:
        List of event dicts, most recent last
    """
    if project_dir is None:
        project_dir = get_project_dir()

    events_file = project_dir / "runs" / "logs" / "events.jsonl"
    if not events_file.exists():
        return []

    events = []
    try:
        with events_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    # Apply filters
                    if event_type and event.get("event") != event_type:
                        continue
                    if session_id and event.get("session_id") != session_id:
                        continue
                    events.append(event)
                except json.JSONDecodeError:
                    continue
    except IOError:
        return []

    return events[-limit:]


def get_session_metrics(
    project_dir: Path | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Calculate metrics from events for a session.

    Returns:
        Dict with token totals, agent counts, durations, success rates
    """
    if project_dir is None:
        project_dir = get_project_dir()

    events = get_events(project_dir, session_id=session_id, limit=10000)

    metrics = {
        "total_tokens": {"input": 0, "output": 0},
        "agent_calls": {},
        "tool_calls": {},
        "decisions": [],
        "errors": 0,
        "verifications": {"passed": 0, "failed": 0},
    }

    for event in events:
        event_type = event.get("event")

        if event_type == "agent_complete":
            agent = event.get("agent", "unknown")
            metrics["agent_calls"][agent] = metrics["agent_calls"].get(agent, 0) + 1
            tokens = event.get("tokens", {})
            metrics["total_tokens"]["input"] += tokens.get("input", 0)
            metrics["total_tokens"]["output"] += tokens.get("output", 0)

        elif event_type == "tool_use":
            tool = event.get("tool_name", "unknown")
            metrics["tool_calls"][tool] = metrics["tool_calls"].get(tool, 0) + 1

        elif event_type == "decision":
            metrics["decisions"].append({
                "type": event.get("decision_type"),
                "decision": event.get("decision"),
            })

        elif event_type == "verification":
            if event.get("success"):
                metrics["verifications"]["passed"] += 1
            else:
                metrics["verifications"]["failed"] += 1

        elif event_type == "error":
            metrics["errors"] += 1

    return metrics


def health_check(project_dir: Path | None = None) -> dict[str, Any]:
    """Run basic health checks on ALTO setup.

    Returns:
        Dict with check results and any issues found
    """
    if project_dir is None:
        project_dir = get_project_dir()

    issues = []
    checks = {}

    # Check runs directory
    runs_dir = project_dir / "runs"
    checks["runs_dir_exists"] = runs_dir.exists()
    if not checks["runs_dir_exists"]:
        issues.append("runs/ directory missing")

    # Check objective.md
    objective = project_dir / "objective.md"
    checks["objective_exists"] = objective.exists()
    if checks["objective_exists"]:
        content = objective.read_text(encoding="utf-8")
        checks["objective_has_content"] = "NEW_PROJECT" not in content and len(content) > 100
        if not checks["objective_has_content"]:
            issues.append("objective.md needs to be filled out")
    else:
        issues.append("objective.md missing")

    # Check state.json
    state = get_state(project_dir)
    checks["state_exists"] = bool(state)
    checks["state_valid"] = "phase" in state if state else False

    # Check for recent errors
    errors_file = runs_dir / "errors.jsonl"
    if errors_file.exists():
        try:
            lines = errors_file.read_text(encoding="utf-8").strip().split("\n")
            recent_errors = len([l for l in lines[-10:] if l.strip()])
            checks["recent_errors"] = recent_errors
            if recent_errors > 5:
                issues.append(f"{recent_errors} recent errors in runs/errors.jsonl")
        except Exception:
            pass

    return {
        "healthy": len(issues) == 0,
        "checks": checks,
        "issues": issues,
    }

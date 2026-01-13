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

#!/usr/bin/env python3
"""
PostToolUse hook: validates phase transitions in state.json.

Triggers on Write/Edit to runs/state.json. Validates:
- Phase is a known valid phase
- Transition from previous phase is allowed
- Logs phase transitions for debugging

Returns error JSON to block invalid transitions.
"""
import json
import os
import sys
from pathlib import Path

from hook_utils import log_event, safe_hook

# Valid phases
VALID_PHASES = [
    "ARCHITECTURE",
    "PLANNING",
    "IN_TASK",
    "BETWEEN_TASKS",
    "BLOCKED",
    "COMPLETED",
    "DEBUG",
]

# Valid phase transitions (from -> [valid next phases])
# None means initial state (no previous phase)
VALID_TRANSITIONS = {
    None: ["ARCHITECTURE"],  # Initial state can only go to ARCHITECTURE
    "ARCHITECTURE": ["PLANNING", "BLOCKED"],
    "PLANNING": ["IN_TASK", "BETWEEN_TASKS", "BLOCKED"],
    "IN_TASK": ["BETWEEN_TASKS", "BLOCKED"],
    "BETWEEN_TASKS": ["IN_TASK", "PLANNING", "COMPLETED", "BLOCKED"],
    "BLOCKED": ["ARCHITECTURE", "PLANNING", "IN_TASK", "BETWEEN_TASKS"],  # After human input
    "COMPLETED": ["DEBUG", "ARCHITECTURE"],  # DEBUG or new feature
    "DEBUG": ["COMPLETED"],
}


def get_previous_phase(project_dir: Path) -> str | None:
    """Get the previous phase from state backup or tracking file."""
    # We track the last known phase in a separate file to detect transitions
    tracker_file = project_dir / "runs" / ".phase-tracker"
    if tracker_file.exists():
        try:
            return tracker_file.read_text(encoding="utf-8").strip() or None
        except Exception:
            return None
    return None


def save_current_phase(project_dir: Path, phase: str | None):
    """Save current phase for next comparison."""
    tracker_file = project_dir / "runs" / ".phase-tracker"
    try:
        tracker_file.parent.mkdir(parents=True, exist_ok=True)
        tracker_file.write_text(phase or "", encoding="utf-8")
    except Exception:
        pass  # Non-critical


def validate_transition(from_phase: str | None, to_phase: str | None) -> tuple[bool, str]:
    """Validate a phase transition. Returns (valid, error_message)."""
    # No phase change or clearing phase
    if to_phase is None:
        return True, ""

    # Unknown phase
    if to_phase not in VALID_PHASES:
        return False, f"Unknown phase '{to_phase}'. Valid: {', '.join(VALID_PHASES)}"

    # Same phase (no transition)
    if from_phase == to_phase:
        return True, ""

    # Check if transition is allowed
    allowed_next = VALID_TRANSITIONS.get(from_phase, [])
    if to_phase not in allowed_next:
        if from_phase is None:
            return False, f"Invalid initial phase '{to_phase}'. Must start with ARCHITECTURE."
        return False, f"Invalid transition: {from_phase} -> {to_phase}. Allowed from {from_phase}: {allowed_next}"

    return True, ""


@safe_hook("phase-validate")
def main():
    hook_input = json.load(sys.stdin)
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only trigger on Write/Edit
    if tool_name not in ("Write", "Edit"):
        return

    # Only trigger for state.json
    file_path = tool_input.get("file_path", "")
    if not file_path.endswith("state.json"):
        return

    # More specific check - must be runs/state.json
    if "/runs/state.json" not in file_path and not file_path.endswith("/runs/state.json"):
        # Could be arbiter/state.json or other state files
        return

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    state_file = project_dir / "runs" / "state.json"

    if not state_file.exists():
        return

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return

    new_phase = state.get("phase")
    previous_phase = get_previous_phase(project_dir)

    # Validate the transition
    valid, error = validate_transition(previous_phase, new_phase)

    if not valid:
        # Log the invalid transition
        log_event(
            "phase_transition",
            {
                "from": previous_phase,
                "to": new_phase,
                "valid": False,
                "error": error,
            },
            project_dir=project_dir,
            session_id=hook_input.get("session_id"),
        )

        # REVERT the invalid transition - restore previous phase in state.json
        if previous_phase is not None:
            try:
                state["phase"] = previous_phase
                state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"Failed to revert state.json: {e}", file=sys.stderr)

        result = {
            "status": "INVALID_PHASE_TRANSITION",
            "from_phase": previous_phase,
            "to_phase": new_phase,
            "error": error,
            "valid_transitions": VALID_TRANSITIONS.get(previous_phase, []),
            "message": f"Phase transition REVERTED: {error}. State.json restored to phase '{previous_phase}'.",
        }
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    # Valid transition - save new phase and log
    if new_phase != previous_phase:
        log_event(
            "phase_transition",
            {
                "from": previous_phase,
                "to": new_phase,
                "valid": True,
            },
            project_dir=project_dir,
            session_id=hook_input.get("session_id"),
        )
        save_current_phase(project_dir, new_phase)


if __name__ == "__main__":
    main()

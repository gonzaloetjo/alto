#!/usr/bin/env python3
"""
SubagentStop hook: validates review file structure after alto-reviewer completes.

Validates:
- Review file exists at expected path
- Contains Status: APPROVED or REJECTED
- REJECTED reviews have Reason and Action Required sections

Returns error JSON to block if validation fails.
"""
import json
import os
import re
import sys
from pathlib import Path

from hook_utils import log_event, safe_hook


def load_state(project_dir: Path) -> dict:
    """Load ALTO state."""
    state_file = project_dir / "runs" / "state.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def validate_review(project_dir: Path, task_id: str) -> list[str]:
    """Validate review file exists and has required format."""
    errors = []
    review_path = project_dir / "runs" / "review" / f"{task_id}-review.md"

    if not review_path.exists():
        errors.append(f"Missing review file: runs/review/{task_id}-review.md")
        return errors

    content = review_path.read_text(encoding="utf-8")

    # Check for Status line
    status_match = re.search(r'\*\*Status:\*\*\s*(APPROVED|REJECTED)', content, re.IGNORECASE)
    if not status_match:
        errors.append("Missing '**Status:** APPROVED' or '**Status:** REJECTED'")
        return errors

    status = status_match.group(1).upper()

    # For REJECTED, check required sections
    if status == "REJECTED":
        content_lower = content.lower()
        if "## reason" not in content_lower:
            errors.append("REJECTED review missing '## Reason' section")
        if "## action required" not in content_lower and "## action needed" not in content_lower:
            errors.append("REJECTED review missing '## Action Required' section")

    # Check minimum length
    if len(content.strip()) < 50:
        errors.append("Review too short (< 50 chars)")

    return errors


@safe_hook("review-validate")
def main():
    hook_input = json.load(sys.stdin)

    # Only validate after alto-reviewer
    agent_name = hook_input.get("agent_name", "")
    if agent_name != "alto-reviewer":
        return

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    state = load_state(project_dir)

    task_id = state.get("current_task_id")
    if not task_id:
        return

    # Validate review
    errors = validate_review(project_dir, task_id)

    if errors:
        log_event(
            "review",
            {
                "task_id": task_id,
                "valid": False,
                "errors": errors,
            },
            project_dir=project_dir,
            session_id=hook_input.get("session_id"),
        )

        result = {
            "status": "INVALID_REVIEW",
            "task_id": task_id,
            "errors": errors,
            "message": f"Review validation failed: {len(errors)} issue(s)",
        }
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)
    else:
        # Log successful review
        review_path = project_dir / "runs" / "review" / f"{task_id}-review.md"
        content = review_path.read_text(encoding="utf-8")
        status_match = re.search(r'\*\*Status:\*\*\s*(APPROVED|REJECTED)', content, re.IGNORECASE)
        status = status_match.group(1).upper() if status_match else "UNKNOWN"

        log_event(
            "review",
            {
                "task_id": task_id,
                "valid": True,
                "decision": status,
            },
            project_dir=project_dir,
            session_id=hook_input.get("session_id"),
        )


if __name__ == "__main__":
    main()

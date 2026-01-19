#!/usr/bin/env python3
"""
PostToolUse hook: validates task file structure after planner creates them.

Triggers on Write/Edit to runs/tasks/*.md. Validates:
- YAML frontmatter exists and is valid
- Required fields present: task_id, title, role, allowed_paths, handoff
- Role is a known agent name
- Task body has required sections

Returns error JSON to block if validation fails.
"""
import json
import os
import re
import sys
from pathlib import Path

from hook_utils import safe_hook

# Known role agents that can execute tasks
VALID_ROLES = [
    "alto-backend",
    "alto-frontend",
    "alto-qa",
    "alto-docs",
    "alto-gitops",
    "code-simplifier",
]

# Required frontmatter fields
REQUIRED_FIELDS = ["task_id", "title", "role", "allowed_paths", "handoff"]

# Optional but recognized fields
OPTIONAL_FIELDS = ["post", "depends_on", "priority"]


def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body) or (None, error_message).
    """
    if not content.startswith("---"):
        return None, "Missing YAML frontmatter (file must start with ---)"

    # Find end of frontmatter
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return None, "Malformed frontmatter (missing closing ---)"

    frontmatter_text = content[4:end_match.start() + 3]
    body = content[end_match.end() + 3:]

    # Parse YAML (simple key: value parsing, no external deps)
    frontmatter = {}
    current_key = None
    current_list = None

    for line in frontmatter_text.split('\n'):
        line = line.rstrip()
        if not line or line.startswith('#'):
            continue

        # Check for list item
        if line.startswith('  - ') and current_key:
            if current_list is None:
                current_list = []
            current_list.append(line[4:].strip())
            frontmatter[current_key] = current_list
            continue

        # Check for key: value
        if ':' in line:
            # Save previous list if any
            current_list = None

            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            current_key = key

            if value:
                # Handle inline list [a, b, c]
                if value.startswith('[') and value.endswith(']'):
                    items = value[1:-1].split(',')
                    frontmatter[key] = [item.strip().strip('"\'') for item in items if item.strip()]
                else:
                    frontmatter[key] = value.strip('"\'')
            else:
                # Value might be a list on following lines
                frontmatter[key] = None

    return frontmatter, body


def validate_task(file_path: Path) -> list[str]:
    """Validate a task file. Returns list of errors."""
    errors = []

    if not file_path.exists():
        return ["Task file does not exist"]

    content = file_path.read_text(encoding="utf-8")

    # Parse frontmatter
    frontmatter, body_or_error = parse_frontmatter(content)
    if frontmatter is None:
        errors.append(body_or_error)
        return errors

    body = body_or_error

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in frontmatter or frontmatter[field] is None:
            errors.append(f"Missing required field: {field}")

    # Validate role is known
    role = frontmatter.get("role")
    if role and role not in VALID_ROLES:
        errors.append(f"Unknown role '{role}'. Valid roles: {', '.join(VALID_ROLES)}")

    # Validate allowed_paths is a list
    allowed_paths = frontmatter.get("allowed_paths")
    if allowed_paths is not None and not isinstance(allowed_paths, list):
        errors.append("allowed_paths must be a list")

    # Validate post agents if specified
    post = frontmatter.get("post")
    if post:
        if not isinstance(post, list):
            errors.append("post must be a list")
        else:
            for agent in post:
                if agent not in VALID_ROLES and agent not in ["alto-reviewer"]:
                    errors.append(f"Unknown post agent '{agent}'")

    # Validate task_id matches filename
    task_id = frontmatter.get("task_id")
    expected_filename = f"{task_id}.md" if task_id else None
    if expected_filename and file_path.name != expected_filename:
        errors.append(f"task_id '{task_id}' doesn't match filename '{file_path.name}'")

    # Check body has content
    if len(body.strip()) < 50:
        errors.append("Task body too short (< 50 chars). Include goal and DoD.")

    # Check for recommended sections (warnings, not errors)
    body_lower = body.lower()
    if "## goal" not in body_lower and "## objective" not in body_lower:
        pass  # Optional, don't error

    if "## definition of done" not in body_lower and "## dod" not in body_lower and "## done" not in body_lower:
        errors.append("Missing '## Definition of Done' section")

    return errors


@safe_hook("task-validate")
def main():
    hook_input = json.load(sys.stdin)
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only trigger on Write/Edit
    if tool_name not in ("Write", "Edit"):
        return

    # Only trigger for task files
    file_path = tool_input.get("file_path", "")
    if "/runs/tasks/" not in file_path or not file_path.endswith(".md"):
        return

    # Validate the task file
    errors = validate_task(Path(file_path))

    if errors:
        result = {
            "status": "INVALID_TASK",
            "file": file_path,
            "errors": errors,
            "message": f"Task validation failed: {len(errors)} issue(s)",
        }
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

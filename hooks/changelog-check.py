#!/usr/bin/env python3
"""Pre-commit check for CHANGELOG updates.

Blocks git commit if key files are staged without CHANGELOG.md.
"""

import json
import subprocess
import sys
from pathlib import Path

# Key file patterns that require CHANGELOG update
KEY_PATTERNS = [
    "templates/CLAUDE.md",
    "devenv.nix",
    "agents/",
    "hooks/",
    "skills/",
    "ARCHITECTURE.md",
    "README.md",
]


def get_staged_files() -> list[str]:
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except Exception:
        pass
    return []


def is_key_file(filepath: str) -> bool:
    """Check if file matches key patterns."""
    for pattern in KEY_PATTERNS:
        if pattern in filepath:
            return True
    return False


def main():
    # Read hook input
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only check Bash commands
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")

    # Only check git commit commands
    if "git commit" not in command:
        sys.exit(0)

    # Skip if --amend (usually fixing previous commit)
    if "--amend" in command:
        sys.exit(0)

    # Get staged files
    staged = get_staged_files()
    if not staged:
        sys.exit(0)

    # Check for key files and CHANGELOG
    key_files_staged = [f for f in staged if is_key_file(f)]
    changelog_staged = any("CHANGELOG.md" in f for f in staged)

    if key_files_staged and not changelog_staged:
        # Block the commit
        result = {
            "decision": "block",
            "reason": f"Key files staged without CHANGELOG.md update:\n"
                      + "\n".join(f"  - {f}" for f in key_files_staged[:5])
                      + "\n\nPlease update CHANGELOG.md or stage it with the commit."
        }
        print(json.dumps(result))
        sys.exit(0)

    # Allow the commit
    sys.exit(0)


if __name__ == "__main__":
    main()

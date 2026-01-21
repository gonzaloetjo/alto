#!/usr/bin/env python3
"""
Dynamic verification hook for ALTO.
Reads verification config from runs/verification-config.json and runs
appropriate checks based on file patterns.

This allows verification commands to be configured mid-session without
requiring a shell restart.
"""

import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path


def load_config() -> dict:
    """Load verification config from alto.json."""
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    alto_json = project_dir / "alto.json"
    if alto_json.exists():
        try:
            data = json.loads(alto_json.read_text())
            if "verification" in data:
                return data["verification"]
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def match_pattern(file_path: str, pattern: str) -> bool:
    """Check if file matches a glob pattern."""
    # Handle patterns like "*.ts", "**/*.py", "src/*.js"
    file_name = os.path.basename(file_path)

    # Try matching against filename
    if fnmatch.fnmatch(file_name, pattern):
        return True

    # Try matching against full path
    if fnmatch.fnmatch(file_path, pattern):
        return True

    # Handle ** patterns
    if "**" in pattern:
        # Convert ** to work with fnmatch
        pattern_parts = pattern.split("**")
        if len(pattern_parts) == 2:
            prefix, suffix = pattern_parts
            suffix = suffix.lstrip("/")
            if file_path.startswith(prefix.rstrip("/")) and fnmatch.fnmatch(file_name, suffix):
                return True

    return False


def run_command(command: str, file_path: str) -> tuple[bool, str]:
    """Run a verification command. Returns (success, output)."""
    # Replace {file} placeholder if present
    cmd = command.replace("{file}", file_path)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.environ.get("CLAUDE_PROJECT_DIR", ".")
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 60s"
    except Exception as e:
        return False, f"Error running command: {e}"


def main():
    """Main hook entry point."""
    try:
        hook_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    tool_name = hook_data.get("tool_name", "")
    tool_input = hook_data.get("tool_input", {})

    # Only run on Edit/Write
    if tool_name not in ["Edit", "Write"]:
        return

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return

    # Load dynamic config
    config = load_config()
    if not config:
        return

    # Check each pattern in config
    for pattern, checks in config.items():
        if not match_pattern(file_path, pattern):
            continue

        # Run each enabled check for this pattern
        for check_name, check_config in checks.items():
            # Handle both string (command only) and dict (with enable flag)
            if isinstance(check_config, str):
                command = check_config
                enabled = True
            elif isinstance(check_config, dict):
                enabled = check_config.get("enable", True)
                command = check_config.get("command", "")
            else:
                continue

            if not enabled or not command:
                continue

            # Run the check
            success, output = run_command(command, file_path)

            if not success:
                print(f"\n[verify-dynamic] {check_name} failed for {os.path.basename(file_path)}:")
                print(output[:1000] if output else "(no output)")
                print()
            # Don't print on success - keep output clean


if __name__ == "__main__":
    main()

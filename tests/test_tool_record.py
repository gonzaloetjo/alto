"""
Tests for hooks/tool-record.py functions.
"""

import json
from pathlib import Path

import pytest

# Import will use conftest.py path setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

# Use importlib to handle the hyphenated filename
import importlib.util
spec = importlib.util.spec_from_file_location(
    "tool_record",
    Path(__file__).parent.parent / "hooks" / "tool-record.py"
)
tool_record = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool_record)

extract_exit_code = tool_record.extract_exit_code
is_check_command = tool_record.is_check_command


class TestExtractExitCode:
    """Tests for extract_exit_code function."""

    def test_extracts_exit_code_from_output(self):
        """Should extract exit code from tool result."""
        result = "Command completed.\nExit code: 0\nOutput: success"

        exit_code = extract_exit_code(result)
        assert exit_code == 0

    def test_extracts_non_zero_exit_code(self):
        """Should extract non-zero exit code."""
        result = "Command failed.\nExit code: 1\nError: something went wrong"

        exit_code = extract_exit_code(result)
        assert exit_code == 1

    def test_returns_none_for_empty_result(self):
        """Should return None for empty result."""
        exit_code = extract_exit_code("")
        assert exit_code is None

    def test_returns_none_for_none_result(self):
        """Should return None for None result."""
        exit_code = extract_exit_code(None)
        assert exit_code is None

    def test_returns_none_when_no_exit_code(self):
        """Should return None when no exit code in output."""
        result = "Just some output\nwith no exit code information"

        exit_code = extract_exit_code(result)
        assert exit_code is None

    def test_case_insensitive(self):
        """Should handle different cases."""
        result1 = "EXIT CODE: 0"
        result2 = "exit code: 1"
        result3 = "Exit Code: 2"

        assert extract_exit_code(result1) == 0
        assert extract_exit_code(result2) == 1
        assert extract_exit_code(result3) == 2


class TestIsCheckCommand:
    """Tests for is_check_command function."""

    def test_detects_make_check(self):
        """Should detect 'make check' as check command."""
        tool_input = {"command": "make check"}
        assert is_check_command(tool_input) is True

    def test_detects_pytest(self):
        """Should detect pytest as check command."""
        tool_input = {"command": "pytest tests/"}
        assert is_check_command(tool_input) is True

    def test_detects_npm_test(self):
        """Should detect npm test as check command."""
        tool_input = {"command": "npm test"}
        assert is_check_command(tool_input) is True

    def test_detects_npm_run_test(self):
        """Should detect npm run test as check command."""
        tool_input = {"command": "npm run test"}
        assert is_check_command(tool_input) is True

    def test_detects_npm_run_build(self):
        """Should detect npm run build as check command."""
        tool_input = {"command": "npm run build"}
        assert is_check_command(tool_input) is True

    def test_returns_false_for_regular_commands(self):
        """Should return False for non-check commands."""
        assert is_check_command({"command": "ls -la"}) is False
        assert is_check_command({"command": "echo hello"}) is False
        assert is_check_command({"command": "git status"}) is False
        assert is_check_command({"command": "npm install"}) is False

    def test_handles_empty_command(self):
        """Should handle empty command."""
        assert is_check_command({"command": ""}) is False
        assert is_check_command({}) is False

    def test_handles_command_with_arguments(self):
        """Should detect check commands with arguments."""
        assert is_check_command({"command": "pytest -v --cov=src"}) is True
        assert is_check_command({"command": "npm test -- --watch"}) is True
        assert is_check_command({"command": "npm run build --production"}) is True

    def test_case_sensitive(self):
        """Should be case sensitive for command matching."""
        # The patterns in the function are lowercase, so uppercase won't match
        assert is_check_command({"command": "PYTEST"}) is False
        assert is_check_command({"command": "NPM TEST"}) is False

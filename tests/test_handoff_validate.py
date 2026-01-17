"""
Tests for hooks/handoff-validate.py functions.
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
    "handoff_validate",
    Path(__file__).parent.parent / "hooks" / "handoff-validate.py"
)
handoff_validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff_validate)

validate_handoff = handoff_validate.validate_handoff
validate_file_locations = handoff_validate.validate_file_locations
validate_state_consistency = handoff_validate.validate_state_consistency


class TestValidateHandoff:
    """Tests for validate_handoff function."""

    def test_valid_handoff(self, tmp_project: Path, sample_handoff: Path):
        """Should return no errors for valid handoff."""
        errors = validate_handoff(tmp_project, "001")
        assert errors == []

    def test_missing_handoff(self, tmp_project: Path):
        """Should return error when handoff file is missing."""
        errors = validate_handoff(tmp_project, "999")

        assert len(errors) == 1
        assert "Missing handoff" in errors[0]

    def test_missing_summary_section(self, tmp_project: Path):
        """Should detect missing summary section."""
        handoff_file = tmp_project / "runs" / "handoffs" / "task-002.md"
        handoff_file.write_text("""# Handoff

## Files Changed
- src/main.py

## Verification
Run tests.
""")

        errors = validate_handoff(tmp_project, "002")

        assert any("summary" in e.lower() for e in errors)

    def test_missing_files_section(self, tmp_project: Path):
        """Should detect missing files section."""
        handoff_file = tmp_project / "runs" / "handoffs" / "task-003.md"
        handoff_file.write_text("""# Handoff

## Summary
Did the work.

## Verification
Run tests.
""")

        errors = validate_handoff(tmp_project, "003")

        assert any("files" in e.lower() for e in errors)

    def test_missing_verify_section(self, tmp_project: Path):
        """Should detect missing verification section."""
        handoff_file = tmp_project / "runs" / "handoffs" / "task-004.md"
        handoff_file.write_text("""# Handoff

## Summary
Did the work.

## Files Changed
- src/main.py
""")

        errors = validate_handoff(tmp_project, "004")

        assert any("verify" in e.lower() for e in errors)

    def test_empty_handoff(self, tmp_project: Path):
        """Should detect empty/stub handoff."""
        handoff_file = tmp_project / "runs" / "handoffs" / "task-005.md"
        handoff_file.write_text("# TODO")

        errors = validate_handoff(tmp_project, "005")

        assert any("incomplete" in e.lower() for e in errors)


class TestValidateFileLocations:
    """Tests for validate_file_locations function."""

    def test_no_restrictions(self, tmp_project: Path):
        """Should return no errors when no allowed_paths configured."""
        errors = validate_file_locations(tmp_project, "001", [])
        assert errors == []

    def test_allowed_path_match(self, tmp_project: Path, sample_tool_usage: Path):
        """Should accept files within allowed paths."""
        # Update tool usage with files in allowed paths
        usage_file = tmp_project / "runs" / "tools" / "usage.jsonl"
        records = [
            {
                "ts": "2024-01-01T10:00:00Z",
                "tool_name": "Edit",
                "file_path": str(tmp_project / "src" / "main.py"),
                "task_id": "001",
            },
        ]
        with usage_file.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        errors = validate_file_locations(tmp_project, "001", ["src/**"])
        assert errors == []

    def test_file_outside_allowed_paths(self, tmp_project: Path):
        """Should detect files outside allowed paths."""
        usage_file = tmp_project / "runs" / "tools" / "usage.jsonl"
        records = [
            {
                "ts": "2024-01-01T10:00:00Z",
                "tool_name": "Edit",
                "file_path": str(tmp_project / "config" / "settings.json"),
                "task_id": "001",
            },
        ]
        with usage_file.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        errors = validate_file_locations(tmp_project, "001", ["src/**"])

        assert len(errors) == 1
        assert "outside allowed_paths" in errors[0]

    def test_protected_files(self, tmp_project: Path):
        """Should detect modifications to protected files."""
        usage_file = tmp_project / "runs" / "tools" / "usage.jsonl"
        records = [
            {
                "ts": "2024-01-01T10:00:00Z",
                "tool_name": "Write",
                "file_path": str(tmp_project / "CLAUDE.md"),
                "task_id": "001",
            },
        ]
        with usage_file.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        errors = validate_file_locations(tmp_project, "001", ["**"])

        assert any("Protected file" in e for e in errors)


class TestValidateStateConsistency:
    """Tests for validate_state_consistency function."""

    def test_consistent_state(self, tmp_project: Path):
        """Should return no errors for consistent state."""
        state = {
            "current_task_id": "001",
            "phase": "EXECUTING",
        }

        errors = validate_state_consistency(tmp_project, state, "001")
        assert errors == []

    def test_task_id_mismatch(self, tmp_project: Path):
        """Should detect task ID mismatch."""
        state = {
            "current_task_id": "002",
            "phase": "EXECUTING",
        }

        errors = validate_state_consistency(tmp_project, state, "001")

        assert len(errors) == 1
        assert "State mismatch" in errors[0]

    def test_invalid_phase(self, tmp_project: Path):
        """Should detect invalid phase."""
        state = {
            "current_task_id": "001",
            "phase": "INVALID_PHASE",
        }

        errors = validate_state_consistency(tmp_project, state, "001")

        assert any("Invalid phase" in e for e in errors)

    def test_valid_phases(self, tmp_project: Path):
        """Should accept all valid phases."""
        valid_phases = ["PLANNING", "EXECUTING", "REVIEWING", "BLOCKED"]

        for phase in valid_phases:
            state = {
                "current_task_id": "001",
                "phase": phase,
            }
            errors = validate_state_consistency(tmp_project, state, "001")
            assert errors == [], f"Phase {phase} should be valid"

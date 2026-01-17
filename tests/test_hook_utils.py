"""
Tests for hooks/hook_utils.py
"""

import json
from pathlib import Path

import pytest

from hook_utils import (
    get_events,
    get_state,
    health_check,
    is_debug_mode,
    log_event,
    read_json_safe,
    write_json_safe,
)


class TestReadJsonSafe:
    """Tests for read_json_safe function."""

    def test_reads_valid_json(self, tmp_path: Path):
        """Should read valid JSON file."""
        data = {"key": "value", "number": 42}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(data))

        result = read_json_safe(json_file)
        assert result == data

    def test_returns_default_for_missing_file(self, tmp_path: Path):
        """Should return default when file doesn't exist."""
        missing_file = tmp_path / "missing.json"

        result = read_json_safe(missing_file, default={"default": True})
        assert result == {"default": True}

    def test_returns_default_for_invalid_json(self, tmp_path: Path):
        """Should return default when JSON is invalid."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json {{{")

        result = read_json_safe(invalid_file, default=[])
        assert result == []

    def test_returns_none_by_default(self, tmp_path: Path):
        """Should return None as default when not specified."""
        missing_file = tmp_path / "missing.json"

        result = read_json_safe(missing_file)
        assert result is None


class TestWriteJsonSafe:
    """Tests for write_json_safe function."""

    def test_writes_valid_json(self, tmp_path: Path):
        """Should write JSON to file."""
        data = {"key": "value", "list": [1, 2, 3]}
        json_file = tmp_path / "output.json"

        result = write_json_safe(json_file, data)

        assert result is True
        assert json_file.exists()
        loaded = json.loads(json_file.read_text())
        assert loaded == data

    def test_creates_parent_directories(self, tmp_path: Path):
        """Should create parent directories if needed."""
        data = {"nested": True}
        json_file = tmp_path / "deep" / "nested" / "dir" / "output.json"

        result = write_json_safe(json_file, data)

        assert result is True
        assert json_file.exists()

    def test_returns_false_on_error(self, tmp_path: Path):
        """Should return False on write error."""
        data = {"key": "value"}
        # Try to write to a directory (should fail)
        dir_path = tmp_path / "is_dir"
        dir_path.mkdir()

        result = write_json_safe(dir_path, data)
        assert result is False


class TestGetState:
    """Tests for get_state function."""

    def test_reads_state_json(self, tmp_project: Path):
        """Should read state.json from project."""
        state = get_state(tmp_project)

        assert state["protocol"] == "alto-v1"
        assert state["phase"] == "BETWEEN_TASKS"

    def test_returns_empty_dict_when_missing(self, tmp_path: Path):
        """Should return empty dict when state.json doesn't exist."""
        empty_project = tmp_path / "empty"
        empty_project.mkdir()

        state = get_state(empty_project)
        assert state == {}


class TestIsDebugMode:
    """Tests for is_debug_mode function."""

    def test_returns_false_by_default(self, tmp_project: Path):
        """Should return False when debug-config.json doesn't exist."""
        result = is_debug_mode(tmp_project)
        assert result is False

    def test_returns_true_when_enabled(self, debug_project: Path):
        """Should return True when debug mode is enabled."""
        result = is_debug_mode(debug_project)
        assert result is True

    def test_returns_false_when_disabled(self, tmp_project: Path):
        """Should return False when debug is explicitly False."""
        config_file = tmp_project / "runs" / "debug-config.json"
        config_file.write_text(json.dumps({"debug": False}))

        result = is_debug_mode(tmp_project)
        assert result is False


class TestLogEvent:
    """Tests for log_event function."""

    def test_logs_event_in_debug_mode(self, debug_project: Path):
        """Should write event to events.jsonl when debug mode enabled."""
        result = log_event(
            "test_event",
            {"test_key": "test_value"},
            project_dir=debug_project,
            session_id="test-session",
        )

        assert result is True
        events_file = debug_project / "runs" / "logs" / "events.jsonl"
        assert events_file.exists()

        content = events_file.read_text()
        event = json.loads(content.strip())
        assert event["event"] == "test_event"
        assert event["test_key"] == "test_value"
        assert event["session_id"] == "test-session"

    def test_does_not_log_when_debug_disabled(self, tmp_project: Path):
        """Should not write event when debug mode disabled."""
        result = log_event(
            "test_event",
            {"test_key": "test_value"},
            project_dir=tmp_project,
        )

        assert result is False
        events_file = tmp_project / "runs" / "logs" / "events.jsonl"
        assert not events_file.exists()


class TestGetEvents:
    """Tests for get_events function."""

    def test_returns_empty_when_no_events(self, tmp_project: Path):
        """Should return empty list when no events file."""
        events = get_events(tmp_project)
        assert events == []

    def test_reads_events_from_file(self, debug_project: Path):
        """Should read events from events.jsonl."""
        # Log some events first
        log_event("event1", {"n": 1}, project_dir=debug_project)
        log_event("event2", {"n": 2}, project_dir=debug_project)

        events = get_events(debug_project)

        assert len(events) == 2
        assert events[0]["event"] == "event1"
        assert events[1]["event"] == "event2"

    def test_filters_by_event_type(self, debug_project: Path):
        """Should filter events by type."""
        log_event("type_a", {"n": 1}, project_dir=debug_project)
        log_event("type_b", {"n": 2}, project_dir=debug_project)
        log_event("type_a", {"n": 3}, project_dir=debug_project)

        events = get_events(debug_project, event_type="type_a")

        assert len(events) == 2
        assert all(e["event"] == "type_a" for e in events)

    def test_limits_results(self, debug_project: Path):
        """Should limit number of events returned."""
        for i in range(10):
            log_event("test", {"n": i}, project_dir=debug_project)

        events = get_events(debug_project, limit=5)

        assert len(events) == 5
        # Should return most recent
        assert events[-1]["n"] == 9


class TestHealthCheck:
    """Tests for health_check function."""

    def test_healthy_project(self, tmp_project: Path):
        """Should report healthy for valid project."""
        result = health_check(tmp_project)

        assert result["healthy"] is True
        assert result["checks"]["runs_dir_exists"] is True
        assert result["checks"]["objective_exists"] is True
        assert len(result["issues"]) == 0

    def test_missing_runs_dir(self, tmp_path: Path):
        """Should report unhealthy when runs/ is missing."""
        project = tmp_path / "broken"
        project.mkdir()
        (project / "objective.md").write_text("# Test\n\nThis is a test.\n" * 10)

        result = health_check(project)

        assert result["healthy"] is False
        assert "runs/ directory missing" in result["issues"]

    def test_missing_objective(self, tmp_project: Path):
        """Should report issue when objective.md is missing."""
        (tmp_project / "objective.md").unlink()

        result = health_check(tmp_project)

        assert result["healthy"] is False
        assert "objective.md missing" in result["issues"]

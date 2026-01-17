"""
Tests for hooks/arbiter-scheduler.py functions.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pytest

# Import will use conftest.py path setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

# Use importlib to handle the hyphenated filename
import importlib.util
spec = importlib.util.spec_from_file_location(
    "arbiter_scheduler",
    Path(__file__).parent.parent / "hooks" / "arbiter-scheduler.py"
)
arbiter_scheduler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbiter_scheduler)

sum_tokens = arbiter_scheduler.sum_tokens
git_numstat = arbiter_scheduler.git_numstat
count_since = arbiter_scheduler.count_since


class TestSumTokens:
    """Tests for sum_tokens function."""

    def test_empty_file(self, tmp_path: Path):
        """Should return 0 for empty file."""
        usage_file = tmp_path / "usage.jsonl"
        usage_file.touch()

        result = sum_tokens(usage_file)
        assert result == 0

    def test_missing_file(self, tmp_path: Path):
        """Should return 0 for missing file."""
        missing_file = tmp_path / "missing.jsonl"

        result = sum_tokens(missing_file)
        assert result == 0

    def test_sums_all_token_types(self, tmp_path: Path):
        """Should sum all token types."""
        usage_file = tmp_path / "usage.jsonl"
        records = [
            {
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cache_read_input_tokens": 25,
                    "cache_creation_input_tokens": 10,
                }
            },
            {
                "usage": {
                    "input_tokens": 200,
                    "output_tokens": 100,
                }
            },
        ]
        with usage_file.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        result = sum_tokens(usage_file)
        # First record: 100 + 50 + 25 + 10 = 185
        # Second record: 200 + 100 = 300
        # Total: 485
        assert result == 485

    def test_handles_missing_usage_field(self, tmp_path: Path):
        """Should handle records without usage field."""
        usage_file = tmp_path / "usage.jsonl"
        records = [
            {"other_field": "value"},
            {"usage": {"input_tokens": 100}},
        ]
        with usage_file.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        result = sum_tokens(usage_file)
        assert result == 100

    def test_handles_invalid_json_lines(self, tmp_path: Path):
        """Should skip invalid JSON lines."""
        usage_file = tmp_path / "usage.jsonl"
        with usage_file.open("w") as f:
            f.write('{"usage": {"input_tokens": 100}}\n')
            f.write("not valid json\n")
            f.write('{"usage": {"input_tokens": 200}}\n')

        result = sum_tokens(usage_file)
        assert result == 300

    def test_handles_empty_lines(self, tmp_path: Path):
        """Should skip empty lines."""
        usage_file = tmp_path / "usage.jsonl"
        with usage_file.open("w") as f:
            f.write('{"usage": {"input_tokens": 100}}\n')
            f.write("\n")
            f.write('{"usage": {"input_tokens": 200}}\n')

        result = sum_tokens(usage_file)
        assert result == 300


class TestGitNumstat:
    """Tests for git_numstat function."""

    def test_returns_dict_structure(self, tmp_path: Path):
        """Should return dict with expected keys."""
        result = git_numstat(tmp_path)

        assert "files" in result
        assert "lines_added" in result
        assert "lines_removed" in result

    def test_returns_zeros_for_non_git_dir(self, tmp_path: Path):
        """Should return zeros for non-git directory."""
        result = git_numstat(tmp_path)

        assert result["files"] == 0
        assert result["lines_added"] == 0
        assert result["lines_removed"] == 0


class TestCountSince:
    """Tests for count_since function."""

    def test_counts_records_since_epoch(self, tmp_path: Path):
        """Should count records since given epoch."""
        jsonl_file = tmp_path / "records.jsonl"

        # Create records with timestamps using UTC to match the function's expectations
        base_epoch = int(time.time()) - 1000  # 1000 seconds ago
        records = [
            {"ts": datetime.utcfromtimestamp(base_epoch - 100).isoformat() + "Z"},  # Before
            {"ts": datetime.utcfromtimestamp(base_epoch + 100).isoformat() + "Z"},  # After
            {"ts": datetime.utcfromtimestamp(base_epoch + 200).isoformat() + "Z"},  # After
        ]
        with jsonl_file.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        result = count_since(jsonl_file, base_epoch)
        assert result == 2  # Only records after base_epoch

    def test_returns_zero_for_missing_file(self, tmp_path: Path):
        """Should return 0 for missing file."""
        missing_file = tmp_path / "missing.jsonl"

        result = count_since(missing_file, int(time.time()))
        assert result == 0

    def test_returns_zero_for_empty_file(self, tmp_path: Path):
        """Should return 0 for empty file."""
        jsonl_file = tmp_path / "empty.jsonl"
        jsonl_file.touch()

        result = count_since(jsonl_file, int(time.time()))
        assert result == 0

    def test_handles_invalid_timestamps(self, tmp_path: Path):
        """Should skip records with invalid timestamps."""
        jsonl_file = tmp_path / "records.jsonl"
        base_epoch = int(time.time()) - 1000

        records = [
            {"ts": "invalid-timestamp"},
            {"ts": datetime.fromtimestamp(base_epoch + 100).isoformat() + "Z"},
        ]
        with jsonl_file.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        result = count_since(jsonl_file, base_epoch)
        assert result == 1  # Only valid record counted

    def test_handles_missing_ts_field(self, tmp_path: Path):
        """Should skip records without ts field."""
        jsonl_file = tmp_path / "records.jsonl"
        base_epoch = int(time.time()) - 1000

        records = [
            {"other_field": "value"},
            {"ts": datetime.fromtimestamp(base_epoch + 100).isoformat() + "Z"},
        ]
        with jsonl_file.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        result = count_since(jsonl_file, base_epoch)
        assert result == 1

    def test_handles_empty_lines(self, tmp_path: Path):
        """Should skip empty lines."""
        jsonl_file = tmp_path / "records.jsonl"
        base_epoch = int(time.time()) - 1000

        with jsonl_file.open("w") as f:
            f.write(json.dumps({"ts": datetime.fromtimestamp(base_epoch + 100).isoformat() + "Z"}) + "\n")
            f.write("\n")
            f.write(json.dumps({"ts": datetime.fromtimestamp(base_epoch + 200).isoformat() + "Z"}) + "\n")

        result = count_since(jsonl_file, base_epoch)
        assert result == 2

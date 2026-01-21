"""
Pytest fixtures for ALTO tests.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add hooks directory to path so we can import hook modules
ALTO_SRC = Path(__file__).parent.parent
sys.path.insert(0, str(ALTO_SRC / "hooks"))


@pytest.fixture
def alto_src() -> Path:
    """Return the ALTO source directory."""
    return ALTO_SRC


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal ALTO project structure for testing.

    Creates:
    - alto.json (consolidated config)
    - runs/state.json (empty state)
    - objective.md (stub)
    """
    project = tmp_path / "test_project"
    project.mkdir()

    # Create runs directory structure
    runs = project / "runs"
    runs.mkdir()

    # Create minimal state.json
    state = {
        "protocol": "alto-v1",
        "phase": "BETWEEN_TASKS",
        "current_task_id": None,
        "current_role": None,
        "completed_task_ids": [],
    }
    (runs / "state.json").write_text(json.dumps(state, indent=2))

    # Create consolidated alto.json (new primary config)
    alto_config = {
        "version": 1,
        "arbiter": {
            "protocol": "alto-arbiter-v1",
            "token_checkpoint_interval": 100000,
            "time_checkpoint_interval_minutes": 20,
            "task_checkpoint_interval": 1,
            "max_files_changed_without_human": 50,
            "max_lines_changed_without_human": 2000,
        },
        "planning": {
            "require_approval": True,
            "replan_strategy": "auto",
            "fixed_batch_size": 5,
        },
        "verification": {},
    }
    (project / "alto.json").write_text(json.dumps(alto_config, indent=2))

    # Create arbiter directory and state
    arbiter = runs / "arbiter"
    arbiter.mkdir()

    # Create empty arbiter state
    (arbiter / "state.json").write_text(json.dumps({
        "last_checkpoint_epoch": 0,
        "last_checkpoint_tokens": 0,
        "last_checkpoint_tasks": 0,
    }, indent=2))

    # Create tools directory
    (runs / "tools").mkdir()

    # Create usage directory
    (runs / "usage").mkdir()

    # Create handoffs directory
    (runs / "handoffs").mkdir()

    # Create permissions directory
    (runs / "permissions").mkdir()

    # Create logs directory
    (runs / "logs").mkdir()

    # Create stub objective.md (must be >100 chars and not contain NEW_PROJECT)
    objective_content = """# Test Objective

## Overview

This is a test project for ALTO testing. It provides fixtures and utilities
for running unit tests against ALTO hooks and utilities.

## Features

### 1. Test Framework
Basic testing infrastructure for ALTO development.

**Definition of Done:**
- [ ] All unit tests pass
- [ ] Coverage above 80%
"""
    (project / "objective.md").write_text(objective_content)

    return project


@pytest.fixture
def debug_project(tmp_project: Path) -> Path:
    """Create a project with debug mode enabled."""
    debug_config = {"debug": True}
    (tmp_project / "runs" / "debug-config.json").write_text(json.dumps(debug_config))
    return tmp_project


@pytest.fixture
def mock_hook_input() -> dict:
    """Standard hook input dict for testing."""
    return {
        "hook_event_name": "PostToolUse",
        "session_id": "test-session-123",
        "tool_name": "Bash",
        "tool_use_id": "tool-456",
        "tool_input": {
            "command": "echo hello"
        },
        "tool_result": "hello",
    }


@pytest.fixture
def mock_subagent_input() -> dict:
    """Standard SubagentStop hook input for testing."""
    return {
        "hook_event_name": "SubagentStop",
        "session_id": "test-session-123",
        "agent_name": "alto-backend",
    }


@pytest.fixture
def sample_handoff(tmp_project: Path) -> Path:
    """Create a sample handoff file."""
    handoff_dir = tmp_project / "runs" / "handoffs"
    handoff_content = """# Task 001 Handoff

## Summary

Implemented the feature as requested.

## Files Changed

- src/main.py
- tests/test_main.py

## Verification

Run `pytest` to verify the implementation.
"""
    handoff_file = handoff_dir / "task-001.md"
    handoff_file.write_text(handoff_content)
    return handoff_file


@pytest.fixture
def sample_tool_usage(tmp_project: Path) -> Path:
    """Create sample tool usage records."""
    usage_file = tmp_project / "runs" / "tools" / "usage.jsonl"
    records = [
        {
            "ts": "2024-01-01T10:00:00Z",
            "tool_name": "Edit",
            "file_path": str(tmp_project / "src" / "main.py"),
            "task_id": "001",
            "success": True,
        },
        {
            "ts": "2024-01-01T10:01:00Z",
            "tool_name": "Bash",
            "command": "pytest",
            "task_id": "001",
            "success": True,
            "is_check_command": True,
        },
    ]
    with usage_file.open("w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return usage_file


@pytest.fixture
def sample_usage_records(tmp_project: Path) -> Path:
    """Create sample usage (token) records."""
    usage_dir = tmp_project / "runs" / "usage"
    usage_file = usage_dir / "usage.jsonl"
    records = [
        {
            "ts": "2024-01-01T10:00:00Z",
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 500,
                "cache_read_input_tokens": 200,
                "cache_creation_input_tokens": 100,
            },
        },
        {
            "ts": "2024-01-01T10:05:00Z",
            "usage": {
                "input_tokens": 2000,
                "output_tokens": 1000,
            },
        },
    ]
    with usage_file.open("w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return usage_file


@pytest.fixture
def sample_skill_file(tmp_path: Path) -> Path:
    """Create a sample skill file for testing."""
    skill_dir = tmp_path / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_content = """---
name: test-skill
type: discipline
triggers:
  - testing
  - validation
---

# Test Skill

## Hard Rule

Always test your code.

## Warning Signs

- Untested code
- Missing assertions
"""
    skill_file.write_text(skill_content)
    return skill_file


@pytest.fixture(autouse=True)
def set_env_vars(tmp_project: Path, monkeypatch):
    """Set environment variables for hook execution."""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_project))


@pytest.fixture
def clean_imports():
    """Clean up any imported hook modules between tests."""
    # Store original modules
    original_modules = set(sys.modules.keys())

    yield

    # Remove any newly imported modules from hooks
    new_modules = set(sys.modules.keys()) - original_modules
    for mod in new_modules:
        if "hook" in mod.lower():
            del sys.modules[mod]

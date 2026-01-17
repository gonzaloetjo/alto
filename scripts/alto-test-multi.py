#!/usr/bin/env python3
"""
Multi-turn ALTO test runner.

Simulates human interaction with ALTO orchestrators by:
1. Running Claude in headless mode with --print
2. Capturing session ID from runs/sessions/modes.json
3. Resuming sessions with --resume for subsequent turns
4. Detecting tool calls via runs/tools/usage.jsonl
5. Injecting responses via prompt continuation

Usage:
    alto-test-multi --scenario setup-new-project
    alto-test-multi --scenario setup-new-project --keep --verbose
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml


class MultiTurnRunner:
    """Runs multi-turn ALTO test scenarios."""

    # Valid phase transitions for state machine validation
    # Any phase can transition to BLOCKED (handled specially in validation)
    # BLOCKED can transition to recovery states (IN_TASK, BETWEEN_TASKS, PLANNING)
    VALID_TRANSITIONS: dict[str | None, set[str]] = {
        None: {"ARCHITECTURE", "PLANNING"},
        "ARCHITECTURE": {"PLANNING"},
        "PLANNING": {"IN_TASK"},
        "IN_TASK": {"BETWEEN_TASKS"},
        "BETWEEN_TASKS": {"IN_TASK", "PLANNING", "COMPLETED"},
        "COMPLETED": {"DEBUG"},
        "DEBUG": {"COMPLETED"},
        "BLOCKED": {"IN_TASK", "BETWEEN_TASKS", "PLANNING", "COMPLETED"},
    }

    def __init__(
        self,
        scenario_path: Path,
        alto_src: Path,
        keep_dir: bool = False,
        verbose: bool = False,
    ):
        self.scenario = self._load_scenario(scenario_path)
        self.alto_src = alto_src
        self.keep_dir = keep_dir
        self.verbose = verbose
        self.test_dir: Path | None = None
        self.session_id: str | None = None
        self.results: list[dict] = []
        self.tool_usage_offset = 0  # Track where we left off in usage.jsonl
        # Phase 1: Track phase history for state machine validation
        self.phase_history: list[tuple[str | None, str]] = []
        # Track all tool calls across turns for sequence verification
        self.all_tool_calls: list[dict] = []

    def _load_scenario(self, path: Path) -> dict:
        """Load and validate YAML scenario."""
        with open(path) as f:
            scenario = yaml.safe_load(f)

        # Validate required fields
        if not scenario.get("name"):
            raise ValueError("Scenario must have a 'name' field")
        if not scenario.get("turns"):
            raise ValueError("Scenario must have 'turns' array")

        return scenario

    def _log(self, msg: str, level: str = "INFO"):
        """Log message if verbose mode enabled."""
        if self.verbose or level == "ERROR":
            print(f"[{level}] {msg}", file=sys.stderr)

    def _get_current_phase(self) -> str | None:
        """Read phase from state.json."""
        if not self.test_dir:
            return None
        state_file = self.test_dir / "runs" / "state.json"
        if not state_file.exists():
            return None
        try:
            data = json.loads(state_file.read_text())
            return data.get("phase")
        except (json.JSONDecodeError, OSError):
            return None

    def _validate_phase_transition(self, from_phase: str | None, to_phase: str) -> bool:
        """Check if transition is allowed by state machine rules."""
        # Any phase can transition to BLOCKED
        if to_phase == "BLOCKED":
            return True
        valid_targets = self.VALID_TRANSITIONS.get(from_phase, set())
        return to_phase in valid_targets

    def _track_phase_change(self):
        """Track phase changes after a turn completes."""
        current_phase = self._get_current_phase()
        if current_phase is None:
            return

        # Check if phase changed from last recorded
        if self.phase_history:
            last_phase = self.phase_history[-1][1]
            if current_phase == last_phase:
                return  # No change
            prev = last_phase
        else:
            prev = None

        self.phase_history.append((prev, current_phase))
        self._log(f"Phase transition: {prev} -> {current_phase}")

    def _get_handoff_content(self) -> tuple[str | None, str]:
        """Return (task_id, content) for current handoff file."""
        if not self.test_dir:
            return (None, "")

        # Check state.json for current task
        state_file = self.test_dir / "runs" / "state.json"
        if not state_file.exists():
            return (None, "")

        try:
            state = json.loads(state_file.read_text())
            current_task = state.get("current_task")
            if current_task:
                handoff_file = self.test_dir / "runs" / "handoffs" / f"{current_task}.md"
                if handoff_file.exists():
                    return (current_task, handoff_file.read_text())
        except (json.JSONDecodeError, OSError):
            pass

        # Fallback: find most recent handoff file
        handoffs_dir = self.test_dir / "runs" / "handoffs"
        if handoffs_dir.exists():
            handoff_files = sorted(handoffs_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if handoff_files:
                task_id = handoff_files[0].stem
                return (task_id, handoff_files[0].read_text())

        return (None, "")

    def _parse_sections(self, content: str) -> list[str]:
        """Extract ## headers from markdown content."""
        sections = []
        for line in content.split("\n"):
            if line.startswith("## "):
                sections.append(line.strip())
        return sections

    def setup_test_directory(self) -> Path:
        """Create isolated test environment with devenv importing local ALTO."""
        test_dir = Path(tempfile.mkdtemp(prefix="alto-multi-"))
        self._log(f"Created test directory: {test_dir}")

        # Initialize git repo (required for ALTO)
        subprocess.run(
            ["git", "init", "-q"], cwd=test_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@alto.dev"],
            cwd=test_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "ALTO Test"],
            cwd=test_dir,
            check=True,
            capture_output=True,
        )

        # Create devenv.yaml pointing to local ALTO
        devenv_yaml = test_dir / "devenv.yaml"
        devenv_yaml.write_text(
            f"""inputs:
  nixpkgs:
    url: github:cachix/devenv-nixpkgs/rolling
  alto:
    url: path:{self.alto_src}
    flake: false

imports:
  - alto
"""
        )

        # Create devenv.nix with debug enabled
        orchestrator = self.scenario.get("orchestrator", "setup")
        devenv_nix = test_dir / "devenv.nix"
        devenv_nix.write_text(
            f"""{{ pkgs, ... }}:
{{
  alto.orchestrator = "{orchestrator}";
  alto.debug = true;
}}
"""
        )

        # Apply initial_state if specified
        initial_state = self.scenario.get("initial_state", {})
        if initial_state.get("objective_md"):
            (test_dir / "objective.md").write_text(initial_state["objective_md"])
            self._log("Applied initial objective.md")

        # Phase 6: Pre-seed state.json
        if initial_state.get("state_json"):
            runs_dir = test_dir / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)
            state_content = initial_state["state_json"]
            if isinstance(state_content, dict):
                state_content = json.dumps(state_content, indent=2)
            (runs_dir / "state.json").write_text(state_content)
            self._log("Applied initial state.json")

        # Phase 6: Pre-seed arbiter config
        if initial_state.get("arbiter_config"):
            arbiter_dir = test_dir / "runs" / "arbiter"
            arbiter_dir.mkdir(parents=True, exist_ok=True)
            config_content = initial_state["arbiter_config"]
            if isinstance(config_content, dict):
                config_content = json.dumps(config_content, indent=2)
            (arbiter_dir / "config.json").write_text(config_content)
            self._log("Applied initial arbiter config")

        # Phase 6: Pre-seed verification config
        if initial_state.get("verification_config"):
            runs_dir = test_dir / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)
            config_content = initial_state["verification_config"]
            if isinstance(config_content, dict):
                config_content = json.dumps(config_content, indent=2)
            (runs_dir / "verification-config.json").write_text(config_content)
            self._log("Applied initial verification config")

        # Phase 6: Pre-seed planning config
        if initial_state.get("planning_config"):
            runs_dir = test_dir / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)
            config_content = initial_state["planning_config"]
            if isinstance(config_content, dict):
                config_content = json.dumps(config_content, indent=2)
            (runs_dir / "planning-config.json").write_text(config_content)
            self._log("Applied initial planning config")

        return test_dir

    def get_session_id(self) -> str | None:
        """Extract session ID from modes.json."""
        modes_file = self.test_dir / "runs" / "sessions" / "modes.json"
        if not modes_file.exists():
            return None
        try:
            data = json.loads(modes_file.read_text())
            orchestrator = self.scenario.get("orchestrator", "setup")
            return data.get(orchestrator, {}).get("session_id")
        except Exception as e:
            self._log(f"Failed to read session ID: {e}", "ERROR")
            return None

    def get_new_tool_calls(self) -> list[dict]:
        """Get tool calls since last check from runs/tools/usage.jsonl."""
        usage_file = self.test_dir / "runs" / "tools" / "usage.jsonl"
        if not usage_file.exists():
            return []

        calls = []
        with open(usage_file) as f:
            lines = f.readlines()
            # Only get new lines since last check
            new_lines = lines[self.tool_usage_offset :]
            self.tool_usage_offset = len(lines)

            for line in new_lines:
                if line.strip():
                    try:
                        calls.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return calls

    def detect_ask_user_question(self, tool_calls: list[dict]) -> dict | None:
        """Detect if AskUserQuestion was called."""
        for call in tool_calls:
            if call.get("tool_name") == "AskUserQuestion":
                return call
        return None

    def parse_plain_text_options(self, response: str) -> list[str]:
        """Extract numbered options from plain text response."""
        # Match patterns like "1. Option text" or "1) Option text" or "1: Option text"
        pattern = r"^\s*(\d+)[.):\-]\s*(.+)$"
        options = []
        for line in response.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                options.append(match.group(2).strip())
        return options

    def find_option_number(self, options: list[str], label: str) -> str | None:
        """Find option number that matches the label (case-insensitive partial match)."""
        label_lower = label.lower()
        for i, opt in enumerate(options, 1):
            if label_lower in opt.lower():
                return str(i)
        return None

    def run_turn(self, turn: dict, prompt: str, is_first: bool = False) -> dict:
        """Execute a single turn and return results."""
        turn_name = turn.get("name", "unnamed")
        self._log(f"Running turn: {turn_name}")
        self._log(f"Prompt: {prompt[:100]}...")

        # Build inner command (claude invocation)
        claude_args = [
            "claude",
            "--print",
            "--dangerously-skip-permissions",
        ]

        if not is_first and self.session_id:
            claude_args.extend(["--resume", self.session_id])
            self._log(f"Resuming session: {self.session_id}")

        # Escape the prompt for shell
        escaped_prompt = prompt.replace("'", "'\\''")
        claude_args.append(f"'{escaped_prompt}'")

        # Build full command using bash -c to avoid shell plugin issues (e.g., enhancd)
        # We cd inside bash to bypass the parent shell's cd override
        inner_cmd = " ".join(claude_args)
        cmd = [
            "/bin/bash", "-c",
            f"cd '{self.test_dir}' && devenv shell -- {inner_cmd}"
        ]

        # Execute
        timeout = turn.get("timeout_seconds", 120)
        start_time = time.time()

        try:
            # Use clean bash shell environment
            env = os.environ.copy()
            env["SHELL"] = "/bin/bash"
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            exit_code = result.returncode
            response = result.stdout
            stderr = result.stderr
            self._log(f"Exit code: {exit_code}")
            self._log(f"Stdout length: {len(response)}")
            self._log(f"Stderr length: {len(stderr)}")
            if not response and stderr:
                self._log(f"Stderr preview: {stderr[:500]}")
        except subprocess.TimeoutExpired:
            exit_code = -1
            response = ""
            stderr = f"Timeout after {timeout}s"

        duration = time.time() - start_time

        # Capture session ID after first turn
        if is_first:
            # Give hooks time to write
            time.sleep(1)
            self.session_id = self.get_session_id()
            self._log(f"Captured session ID: {self.session_id}")

        # Get tool calls for this turn
        tool_calls = self.get_new_tool_calls()

        # Track tool calls globally for sequence verification
        self.all_tool_calls.extend(tool_calls)

        # Track phase changes for state machine validation
        self._track_phase_change()

        return {
            "turn_name": turn_name,
            "prompt": prompt,
            "response": response,
            "stderr": stderr,
            "exit_code": exit_code,
            "duration": duration,
            "tool_calls": tool_calls,
            "session_id": self.session_id,
        }

    def verify_expectations(self, turn: dict, result: dict) -> list[str]:
        """Verify turn expectations, return list of failures."""
        failures = []
        expect = turn.get("expect", {})

        # Response contains (all must match)
        for text in expect.get("response_contains", []):
            if text.lower() not in result["response"].lower():
                failures.append(f"Response missing expected text: '{text}'")

        # Response contains any (at least one must match)
        if expect.get("response_contains_any"):
            found = any(
                t.lower() in result["response"].lower()
                for t in expect["response_contains_any"]
            )
            if not found:
                failures.append(
                    f"Response missing any of: {expect['response_contains_any']}"
                )

        # Tool called (soft check - warning only due to probabilistic behavior)
        if expect.get("tool_called"):
            tool_names = [c.get("tool_name") for c in result["tool_calls"]]
            if expect["tool_called"] not in tool_names:
                self._log(
                    f"Expected tool '{expect['tool_called']}' not detected (soft check)",
                    "WARN",
                )

        # State assertions (legacy)
        if expect.get("state"):
            # Handle legacy state.phase check
            legacy_state = {k: v for k, v in expect["state"].items()
                          if k not in ("phase_in", "completed_tasks_min")}
            if legacy_state:
                state_failures = self._verify_state(legacy_state)
                failures.extend(state_failures)

        # Phase assertions (Phase 1)
        failures.extend(self._verify_phase_assertions(expect, result))

        # Tool strict assertions (Phase 2)
        failures.extend(self._verify_tool_strict_assertions(expect, result))

        # Tool sequence (Phase 2)
        failures.extend(self._verify_tool_sequence(expect, result))

        # Handoff assertions (Phase 3)
        failures.extend(self._verify_handoff_assertions(expect, result))

        # Metric assertions (Phase 4)
        failures.extend(self._verify_metric_assertions(expect, result))

        # Negative assertions (Phase 5)
        failures.extend(self._verify_negative_assertions(expect, result))

        return failures

    def _verify_state(self, expected_state: dict) -> list[str]:
        """Verify runs/state.json matches expectations."""
        failures = []
        state_file = self.test_dir / "runs" / "state.json"

        if not state_file.exists():
            if expected_state.get("phase") is not None:
                failures.append("state.json does not exist but expected state")
            return failures

        try:
            actual = json.loads(state_file.read_text())
        except json.JSONDecodeError:
            failures.append("state.json is invalid JSON")
            return failures

        for key, expected_value in expected_state.items():
            actual_value = actual.get(key)
            if actual_value != expected_value:
                failures.append(
                    f"State mismatch: {key} = {actual_value}, expected {expected_value}"
                )

        return failures

    def _verify_phase_assertions(self, expect: dict, result: dict) -> list[str]:
        """Verify phase-related assertions (Phase 1)."""
        failures = []

        # Enhanced state assertions with phase_in and completed_tasks_min
        state_expect = expect.get("state", {})

        # phase_in: verify current phase is one of allowed values
        if "phase_in" in state_expect:
            current_phase = self._get_current_phase()
            allowed_phases = state_expect["phase_in"]
            if current_phase not in allowed_phases:
                failures.append(
                    f"Phase '{current_phase}' not in expected phases: {allowed_phases}"
                )

        # completed_tasks_min: verify at least N tasks completed
        if "completed_tasks_min" in state_expect:
            min_tasks = state_expect["completed_tasks_min"]
            state_file = self.test_dir / "runs" / "state.json"
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                    completed = len(state.get("completed_tasks", []))
                    if completed < min_tasks:
                        failures.append(
                            f"Only {completed} tasks completed, expected at least {min_tasks}"
                        )
                except json.JSONDecodeError:
                    failures.append("Cannot verify completed_tasks_min: invalid state.json")
            else:
                failures.append("Cannot verify completed_tasks_min: state.json missing")

        # phase_transition_valid: verify all recorded transitions are valid
        if expect.get("phase_transition_valid"):
            for from_phase, to_phase in self.phase_history:
                if not self._validate_phase_transition(from_phase, to_phase):
                    failures.append(
                        f"Invalid phase transition: {from_phase} -> {to_phase}"
                    )

        return failures

    def _verify_tool_strict_assertions(self, expect: dict, result: dict) -> list[str]:
        """Verify tool assertions with strictness levels (Phase 2)."""
        failures = []
        tools_expect = expect.get("tools", [])
        tool_names_called = [c.get("tool_name") for c in result["tool_calls"]]

        for tool_spec in tools_expect:
            tool_name = tool_spec.get("name")
            strictness = tool_spec.get("strictness", "soft")

            if tool_name not in tool_names_called:
                if strictness == "required":
                    failures.append(f"Required tool '{tool_name}' was not called")
                elif strictness == "strict":
                    failures.append(f"Strict tool '{tool_name}' was not called")
                continue

            # For strict mode, verify parameters
            if strictness == "strict" and "params" in tool_spec:
                expected_params = tool_spec["params"]
                # Find matching tool calls
                for call in result["tool_calls"]:
                    if call.get("tool_name") != tool_name:
                        continue
                    call_params = call.get("params", {})

                    # command_contains check
                    if "command_contains" in expected_params:
                        cmd = call_params.get("command", "")
                        if expected_params["command_contains"] not in cmd:
                            failures.append(
                                f"Tool '{tool_name}' command missing '{expected_params['command_contains']}'"
                            )

                    # file_path check
                    if "file_path" in expected_params:
                        path = call_params.get("file_path", "")
                        if expected_params["file_path"] not in path:
                            failures.append(
                                f"Tool '{tool_name}' file_path missing '{expected_params['file_path']}'"
                            )

        return failures

    def _verify_tool_sequence(self, expect: dict, result: dict) -> list[str]:
        """Verify tool calls appear in specified order (Phase 2)."""
        failures = []
        expected_sequence = expect.get("tool_sequence", [])
        if not expected_sequence:
            return failures

        # Get all tool names from this turn
        tool_names = [c.get("tool_name") for c in result["tool_calls"]]

        # Check sequence appears in order (not necessarily contiguous)
        seq_idx = 0
        for name in tool_names:
            if seq_idx < len(expected_sequence) and name == expected_sequence[seq_idx]:
                seq_idx += 1

        if seq_idx < len(expected_sequence):
            failures.append(
                f"Tool sequence not found in order: expected {expected_sequence}, "
                f"got {tool_names}"
            )

        return failures

    def _verify_handoff_assertions(self, expect: dict, result: dict) -> list[str]:
        """Verify handoff file structure (Phase 3)."""
        failures = []
        handoff_expect = expect.get("handoff", {})
        if not handoff_expect:
            return failures

        task_id, content = self._get_handoff_content()

        # exists check
        if handoff_expect.get("exists"):
            if not content:
                failures.append("Expected handoff file but none found")
                return failures

        if not content:
            return failures

        # has_sections check
        if "has_sections" in handoff_expect:
            sections = self._parse_sections(content)
            for expected_section in handoff_expect["has_sections"]:
                if expected_section not in sections:
                    failures.append(f"Handoff missing section: {expected_section}")

        # min_length check
        if "min_length" in handoff_expect:
            min_len = handoff_expect["min_length"]
            if len(content) < min_len:
                failures.append(
                    f"Handoff too short: {len(content)} chars, expected at least {min_len}"
                )

        return failures

    def _verify_metric_assertions(self, expect: dict, result: dict) -> list[str]:
        """Verify metric thresholds (Phase 4)."""
        failures = []
        metrics = expect.get("metrics", {})
        if not metrics:
            return failures

        # turn_duration_max_seconds
        if "turn_duration_max_seconds" in metrics:
            max_duration = metrics["turn_duration_max_seconds"]
            if result["duration"] > max_duration:
                failures.append(
                    f"Turn took {result['duration']:.1f}s, max allowed {max_duration}s"
                )

        # tokens_turn_max - would need to be extracted from Claude output/logs
        # Skipped for now as token usage isn't easily available in --print mode

        return failures

    def _verify_negative_assertions(self, expect: dict, result: dict) -> list[str]:
        """Verify negative assertions (Phase 5)."""
        failures = []

        # response_not_contains
        for text in expect.get("response_not_contains", []):
            if text.lower() in result["response"].lower():
                failures.append(f"Response contains forbidden text: '{text}'")

        # tool_not_called
        tool_names_called = [c.get("tool_name") for c in result["tool_calls"]]
        for tool_name in expect.get("tool_not_called", []):
            if tool_name in tool_names_called:
                failures.append(f"Tool '{tool_name}' was called but should not be")

        return failures

    def determine_next_prompt(self, turn: dict, result: dict) -> str:
        """Determine what prompt to send for the next turn based on response."""
        user_response = turn.get("user_response", {})

        if not user_response:
            return ""

        # Check if AskUserQuestion was used
        ask_call = self.detect_ask_user_question(result["tool_calls"])

        if ask_call and user_response.get("select_option"):
            # AskUserQuestion was called - send the option label
            # Claude Code will match it to the option
            self._log(f"AskUserQuestion detected, selecting: {user_response['select_option']}")
            return user_response["select_option"]

        # Try to match plain text menu
        if user_response.get("select_option"):
            options = self.parse_plain_text_options(result["response"])
            if options:
                option_num = self.find_option_number(
                    options, user_response["select_option"]
                )
                if option_num:
                    self._log(f"Plain text menu detected, selecting option {option_num}")
                    return option_num

        # Fallback to text response
        fallback = user_response.get("text_fallback") or user_response.get("text", "")
        if fallback:
            self._log(f"Using fallback response: {fallback[:50]}...")
        return fallback

    def verify_final_assertions(self, assertions: dict) -> list[str]:
        """Verify final state after all turns."""
        failures = []

        # Files exist
        for path in assertions.get("files_exist", []):
            if not (self.test_dir / path).exists():
                failures.append(f"Expected file does not exist: {path}")

        # Files NOT exist (Phase 5 negative assertion)
        for path in assertions.get("files_not_exist", []):
            if (self.test_dir / path).exists():
                failures.append(f"File should not exist: {path}")

        # File contains
        for path, patterns in assertions.get("file_contains", {}).items():
            file_path = self.test_dir / path
            if not file_path.exists():
                failures.append(f"Cannot check contents - file missing: {path}")
                continue
            content = file_path.read_text()
            for pattern in patterns:
                if pattern.lower() not in content.lower():
                    failures.append(f"File {path} missing expected content: '{pattern}'")

        # File NOT contains (Phase 5 negative assertion)
        for path, patterns in assertions.get("file_not_contains", {}).items():
            file_path = self.test_dir / path
            if not file_path.exists():
                continue  # File not existing is okay for negative check
            content = file_path.read_text()
            for pattern in patterns:
                if pattern.lower() in content.lower():
                    failures.append(f"File {path} contains forbidden content: '{pattern}'")

        # State assertions
        if assertions.get("state"):
            state_failures = self._verify_state(assertions["state"])
            failures.extend(state_failures)

        # Final phase transition validation
        if assertions.get("phase_transition_valid"):
            for from_phase, to_phase in self.phase_history:
                if not self._validate_phase_transition(from_phase, to_phase):
                    failures.append(
                        f"Invalid phase transition: {from_phase} -> {to_phase}"
                    )

        return failures

    def run_scenario(self) -> dict:
        """Run the complete multi-turn scenario."""
        self.test_dir = self.setup_test_directory()
        scenario_name = self.scenario.get("name", "unnamed")

        print(f"\n{'='*60}")
        print(f"Scenario: {scenario_name}")
        print(f"Orchestrator: {self.scenario.get('orchestrator', 'setup')}")
        print(f"Test dir: {self.test_dir}")
        print(f"{'='*60}\n")

        try:
            turns = self.scenario.get("turns", [])
            all_failures = []
            next_prompt = None

            for i, turn in enumerate(turns):
                turn_name = turn.get("name", f"turn-{i+1}")
                print(f"\n--- Turn {i+1}/{len(turns)}: {turn_name} ---")

                # Determine prompt for this turn
                # Explicit turn prompt takes precedence over user_response from previous turn
                turn_prompt = turn.get("prompt")
                if turn_prompt:
                    prompt = turn_prompt
                elif next_prompt:
                    prompt = next_prompt
                else:
                    prompt = ""

                if not prompt:
                    print(f"  [SKIP] No prompt for turn")
                    continue

                # Run turn
                is_first = i == 0
                result = self.run_turn(turn, prompt, is_first=is_first)
                self.results.append(result)

                # Show response preview
                response_preview = result["response"][:200].replace("\n", " ")
                print(f"  Response: {response_preview}...")

                # Verify expectations
                failures = self.verify_expectations(turn, result)
                if failures:
                    all_failures.extend([(turn_name, f) for f in failures])
                    for f in failures:
                        print(f"  [FAIL] {f}")
                else:
                    print(f"  [PASS] Duration: {result['duration']:.1f}s")

                # Prepare next turn's prompt
                next_prompt = self.determine_next_prompt(turn, result)

            # Final assertions
            if "final_assertions" in self.scenario:
                print(f"\n--- Final Assertions ---")
                final_failures = self.verify_final_assertions(
                    self.scenario["final_assertions"]
                )
                if final_failures:
                    all_failures.extend([("final", f) for f in final_failures])
                    for f in final_failures:
                        print(f"  [FAIL] {f}")
                else:
                    print(f"  [PASS] All final assertions passed")

            # Summary
            success = len(all_failures) == 0
            print(f"\n{'='*60}")
            print(f"Result: {'SUCCESS' if success else 'FAILED'}")
            print(f"Turns: {len(turns)}")
            print(f"Failures: {len(all_failures)}")
            if self.keep_dir:
                print(f"Test dir kept: {self.test_dir}")
            print(f"{'='*60}\n")

            return {
                "scenario": scenario_name,
                "success": success,
                "turns": len(turns),
                "failures": [{"turn": t, "message": m} for t, m in all_failures],
                "results": self.results,
                "test_dir": str(self.test_dir),
            }

        finally:
            if not self.keep_dir and self.test_dir:
                shutil.rmtree(self.test_dir, ignore_errors=True)


def run_single_scenario(
    scenario_path: Path,
    alto_src: Path,
    keep_dir: bool,
    verbose: bool,
    json_output: bool,
) -> dict:
    """Run a single scenario and return results."""
    runner = MultiTurnRunner(
        scenario_path=scenario_path,
        alto_src=alto_src,
        keep_dir=keep_dir,
        verbose=verbose,
    )

    result = runner.run_scenario()

    if json_output:
        # Clean results for JSON output (remove large response bodies)
        clean_results = []
        for r in result["results"]:
            clean_results.append({
                "turn_name": r["turn_name"],
                "exit_code": r["exit_code"],
                "duration": r["duration"],
                "tool_calls": len(r["tool_calls"]),
            })
        result["results"] = clean_results

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run multi-turn ALTO test scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  alto-test-multi --scenario setup-new-project
  alto-test-multi --scenario build-simple-feature --keep --verbose
  alto-test-multi --scenario-file ./my-scenario.yaml --json
  alto-test-multi --all --verbose
        """,
    )
    parser.add_argument(
        "--scenario",
        help="Scenario name from tests/scenarios/multi-turn/",
    )
    parser.add_argument(
        "--scenario-file",
        type=Path,
        help="Path to scenario YAML file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios in tests/scenarios/multi-turn/",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep test directory after run",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    # Determine ALTO source directory
    alto_src = Path(os.environ.get("ALTO_SRC", Path(__file__).parent.parent))
    if not (alto_src / "devenv.nix").exists():
        print(f"Error: ALTO_SRC not found at {alto_src}", file=sys.stderr)
        sys.exit(1)

    scenarios_dir = alto_src / "tests" / "scenarios" / "multi-turn"

    # Run all scenarios
    if args.all:
        scenario_files = sorted(scenarios_dir.glob("*.yaml"))
        if not scenario_files:
            print(f"Error: No scenarios found in {scenarios_dir}", file=sys.stderr)
            sys.exit(1)

        all_results = []
        total_turns = 0
        total_failures = 0
        passed = 0
        failed = 0

        print(f"\n{'#'*60}")
        print(f"# ALTO Protocol Test Suite")
        print(f"# Scenarios: {len(scenario_files)}")
        print(f"{'#'*60}\n")

        for scenario_path in scenario_files:
            result = run_single_scenario(
                scenario_path=scenario_path,
                alto_src=alto_src,
                keep_dir=args.keep,
                verbose=args.verbose,
                json_output=args.json,
            )
            all_results.append(result)
            total_turns += result["turns"]
            total_failures += len(result["failures"])
            if result["success"]:
                passed += 1
            else:
                failed += 1

        # Print summary
        print(f"\n{'#'*60}")
        print(f"# SUITE SUMMARY")
        print(f"{'#'*60}")
        print(f"  Scenarios: {len(scenario_files)}")
        print(f"  Passed:    {passed}")
        print(f"  Failed:    {failed}")
        print(f"  Turns:     {total_turns}")
        print(f"  Failures:  {total_failures}")
        print(f"{'#'*60}\n")

        # List failed scenarios
        if failed > 0:
            print("Failed scenarios:")
            for r in all_results:
                if not r["success"]:
                    print(f"  - {r['scenario']}")
                    for f in r["failures"]:
                        print(f"      [{f['turn']}] {f['message']}")
            print()

        if args.json:
            print(json.dumps({
                "suite": True,
                "scenarios": len(scenario_files),
                "passed": passed,
                "failed": failed,
                "total_turns": total_turns,
                "total_failures": total_failures,
                "results": all_results,
            }, indent=2))

        sys.exit(0 if failed == 0 else 1)

    # Find single scenario file
    if args.scenario_file:
        scenario_path = args.scenario_file
    elif args.scenario:
        scenario_path = scenarios_dir / f"{args.scenario}.yaml"
    else:
        parser.error("Must provide --scenario, --scenario-file, or --all")

    if not scenario_path.exists():
        print(f"Error: Scenario not found: {scenario_path}", file=sys.stderr)
        sys.exit(1)

    result = run_single_scenario(
        scenario_path=scenario_path,
        alto_src=alto_src,
        keep_dir=args.keep,
        verbose=args.verbose,
        json_output=args.json,
    )

    if args.json:
        print(json.dumps(result, indent=2))

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()

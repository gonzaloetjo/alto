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

        # State assertions
        if expect.get("state"):
            state_failures = self._verify_state(expect["state"])
            failures.extend(state_failures)

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

        # State assertions
        if assertions.get("state"):
            state_failures = self._verify_state(assertions["state"])
            failures.extend(state_failures)

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


def main():
    parser = argparse.ArgumentParser(
        description="Run multi-turn ALTO test scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  alto-test-multi --scenario setup-new-project
  alto-test-multi --scenario build-simple-feature --keep --verbose
  alto-test-multi --scenario-file ./my-scenario.yaml --json
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

    # Find scenario file
    if args.scenario_file:
        scenario_path = args.scenario_file
    elif args.scenario:
        scenario_path = alto_src / "tests" / "scenarios" / "multi-turn" / f"{args.scenario}.yaml"
    else:
        parser.error("Must provide --scenario or --scenario-file")

    if not scenario_path.exists():
        print(f"Error: Scenario not found: {scenario_path}", file=sys.stderr)
        sys.exit(1)

    # Run scenario
    runner = MultiTurnRunner(
        scenario_path=scenario_path,
        alto_src=alto_src,
        keep_dir=args.keep,
        verbose=args.verbose,
    )

    result = runner.run_scenario()

    if args.json:
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
        print(json.dumps(result, indent=2))

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# ALTO test harness - Run isolated test scenarios
# WARNING: Uses --dangerously-skip-permissions for automated testing.
# Only run with trusted scenarios. For CI/autonomous use, consider containers.
#
# Environment variables:
#   ALTO_SRC - Path to ALTO source directory

set -e

usage() {
  echo "ALTO Test Harness - Run isolated test scenarios"
  echo ""
  echo "WARNING: Uses --dangerously-skip-permissions. Only run trusted scenarios."
  echo ""
  echo "Usage: alto-test-run [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --scenario FILE    YAML scenario file from tests/scenarios/"
  echo "  --objective TEXT   Inline objective (alternative to --scenario)"
  echo "  --prompt TEXT      Prompt to send to Claude (default: 'Build the project')"
  echo "  --orchestrator X   Orchestrator mode: setup|build (default: build)"
  echo "  --dir DIR          Test directory (default: /tmp/alto-test-XXXX)"
  echo "  --keep             Keep test directory after run"
  echo "  --json             Output results as JSON"
  echo "  --help             Show this help"
  echo ""
  echo "Examples:"
  echo "  alto-test-run --scenario simple-hello-world"
  echo "  alto-test-run --objective 'Create hello.py that prints Hello'"
}

# Defaults
SCENARIO=""
OBJECTIVE=""
PROMPT="Read objective.md and build the project. The plan is pre-approved."
ORCHESTRATOR="build"
TEST_DIR=""
KEEP_DIR=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) SCENARIO="$2"; shift 2 ;;
    --objective) OBJECTIVE="$2"; shift 2 ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    --orchestrator) ORCHESTRATOR="$2"; shift 2 ;;
    --dir) TEST_DIR="$2"; shift 2 ;;
    --keep) KEEP_DIR=true; shift ;;
    --json) JSON_OUTPUT=true; shift ;;
    --help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

# Load scenario if provided
if [ -n "$SCENARIO" ]; then
  SCENARIO_FILE="$ALTO_SRC/tests/scenarios/$SCENARIO.yaml"
  if [ ! -f "$SCENARIO_FILE" ]; then
    echo "Error: Scenario not found: $SCENARIO_FILE" >&2
    exit 1
  fi
  OBJECTIVE=$(yq -r '.objective // ""' "$SCENARIO_FILE")
  PROMPT=$(yq -r '.prompt // "Read objective.md and build the project."' "$SCENARIO_FILE")
  ORCHESTRATOR=$(yq -r '.orchestrator // "build"' "$SCENARIO_FILE")
fi

if [ -z "$OBJECTIVE" ]; then
  echo "Error: Must provide --scenario or --objective" >&2
  usage
  exit 1
fi

# Create test directory
if [ -z "$TEST_DIR" ]; then
  TEST_DIR=$(mktemp -d /tmp/alto-test-XXXXXX)
else
  mkdir -p "$TEST_DIR"
fi

cleanup() {
  if [ "$KEEP_DIR" = false ] && [ -d "$TEST_DIR" ]; then
    rm -rf "$TEST_DIR"
  fi
}
trap cleanup EXIT

# Initialize git repo
git init -q "$TEST_DIR"

# Create devenv.yaml
cat > "$TEST_DIR/devenv.yaml" << YAML_EOF
inputs:
  nixpkgs:
    url: github:cachix/devenv-nixpkgs/rolling
  alto:
    url: path:$ALTO_SRC
    flake: false

imports:
  - alto
YAML_EOF

# Create devenv.nix with debug enabled
cat > "$TEST_DIR/devenv.nix" << NIX_EOF
{ pkgs, ... }:
{
  alto.orchestrator = "$ORCHESTRATOR";
  alto.debug = true;
}
NIX_EOF

# Create objective.md
cat > "$TEST_DIR/objective.md" << OBJ_EOF
# Test Objective

$OBJECTIVE
OBJ_EOF

# Record start time
START_TIME=$(date +%s)

# Run devenv shell with claude
cd "$TEST_DIR"
OUTPUT=$(devenv shell -- claude --print --dangerously-skip-permissions "$PROMPT" 2>&1) || true
EXIT_CODE=$?

# Record end time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Gather results
FILES_CREATED=$(find "$TEST_DIR" -maxdepth 1 -type f -name "*.py" -o -name "*.js" -o -name "*.ts" 2>/dev/null | wc -l)
EVENTS_COUNT=0
if [ -f "$TEST_DIR/runs/logs/events.jsonl" ]; then
  EVENTS_COUNT=$(wc -l < "$TEST_DIR/runs/logs/events.jsonl")
fi

if [ "$JSON_OUTPUT" = true ]; then
  # JSON output
  cat << JSON_EOF
{
  "success": $([ $EXIT_CODE -eq 0 ] && echo "true" || echo "false"),
  "exit_code": $EXIT_CODE,
  "duration_seconds": $DURATION,
  "test_dir": "$TEST_DIR",
  "files_created": $FILES_CREATED,
  "events_logged": $EVENTS_COUNT,
  "orchestrator": "$ORCHESTRATOR",
  "keep_dir": $KEEP_DIR
}
JSON_EOF
else
  # Human-readable output
  echo ""
  echo "ALTO Test Results"
  echo "================="
  echo "Status: $([ $EXIT_CODE -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')"
  echo "Duration: ${DURATION}s"
  echo "Files created: $FILES_CREATED"
  echo "Events logged: $EVENTS_COUNT"
  echo "Test dir: $TEST_DIR"
  if [ "$KEEP_DIR" = true ]; then
    echo ""
    echo "Directory kept. Inspect with:"
    echo "  ls -la $TEST_DIR"
    echo "  cat $TEST_DIR/runs/logs/events.jsonl"
  fi
fi

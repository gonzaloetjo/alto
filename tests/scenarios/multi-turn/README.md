# Multi-Turn Protocol Test Scenarios

These scenarios test ALTO's orchestrator protocols by simulating human interaction across multiple conversation turns.

## Running Scenarios

```bash
# From ALTO source directory (requires devenv shell)
devenv shell -- alto-test-multi --scenario setup-new-project

# Run with verbose output and keep test directory
devenv shell -- alto-test-multi --scenario build-blocked-recovery --keep --verbose

# Output as JSON (for CI)
devenv shell -- alto-test-multi --scenario build-simple-feature --json
```

**Cost:** Each turn costs ~$0.08 (Claude API). A 3-turn scenario costs ~$0.24.

## Scenario Format

```yaml
name: scenario-name
description: What this scenario tests
type: multi-turn

orchestrator: setup | build
timeout_seconds: 600

# Optional: seed initial state
initial_state:
  objective_md: |
    Content for objective.md...
  state_json:              # Pre-seed runs/state.json
    phase: "BLOCKED"
    block_reason: "Test error"
  arbiter_config:          # Pre-seed runs/arbiter/config.json
    task_checkpoint_interval: 1

turns:
  - name: "turn-name"
    prompt: "What to send to Claude"
    timeout_seconds: 120
    expect:
      # Response content checks
      response_contains:
        - "must contain this"
      response_contains_any:
        - "or this"
        - "or that"
      response_not_contains:    # Negative assertion
        - "error"
        - "failed"

      # Tool checks (legacy - soft warning only)
      tool_called: "AskUserQuestion"

      # Tool checks with strictness levels
      tools:
        - name: "Write"
          strictness: required  # Fail if not called
        - name: "Bash"
          strictness: strict    # Fail if not called OR params don't match
          params:
            command_contains: "python"

      # Tool sequence (must appear in order)
      tool_sequence: ["Read", "Edit", "Bash"]

      # Negative tool assertion
      tool_not_called:
        - "Write"  # Should use Edit instead

      # State machine validation
      state:
        phase: "IN_TASK"           # Exact match (legacy)
        phase_in: ["IN_TASK", "BETWEEN_TASKS"]  # One of these
        completed_tasks_min: 1     # At least N completed
      phase_transition_valid: true # Validate all transitions

      # Handoff file verification
      handoff:
        exists: true
        has_sections:
          - "## Summary"
          - "## Files"
        min_length: 100

      # Metric thresholds
      metrics:
        turn_duration_max_seconds: 120

    user_response:
      select_option: "Option label"  # For AskUserQuestion
      text_fallback: "1"             # Fallback for plain text menus
      text: "Direct text response"   # Or just send text

final_assertions:
  files_exist:
    - expected-file.py
  files_not_exist:             # Negative assertion
    - runs/arbiter/pending.json
  file_contains:
    expected-file.py:
      - "expected content"
  file_not_contains:           # Negative assertion
    some-file.py:
      - "forbidden content"
  state:
    phase: "COMPLETED"
  phase_transition_valid: true # Validate all recorded transitions
```

## Available Scenarios

| Scenario | Orchestrator | Turns | Description |
|----------|--------------|-------|-------------|
| `setup-new-project` | setup | 4 | Complete setup flow from welcome to objective.md |
| `build-simple-feature` | build | 2 | Build orchestrator with pre-defined objective |
| `build-phase-transitions` | build | 3 | Validates state machine transitions |
| `build-handoff-structure` | build | 2 | Verifies handoff file format |
| `setup-configure-flow` | setup | 3 | Tests configuration path with Write verification |
| `build-blocked-recovery` | build | 2 | Tests recovery from BLOCKED state |

## Key Behaviors

### AskUserQuestion Handling

The setup orchestrator often uses `AskUserQuestion` to present options. However, this is probabilistic - Claude may sometimes output plain text menus instead.

The test harness handles both cases:
1. If `AskUserQuestion` is detected in tool logs, uses `select_option` to respond
2. If plain text menu is detected, parses numbered options and uses `text_fallback`

### Session Continuity

Each turn after the first uses `--resume <session_id>` to continue the conversation. Session IDs are captured from `runs/sessions/modes.json`.

### State Verification

Between turns, the harness can verify `runs/state.json`:
- `phase`: Current protocol phase (ARCHITECTURE, PLANNING, IN_TASK, etc.)
- Other state fields as needed

## Assertion Types

### Tool Strictness Levels

| Level | Behavior |
|-------|----------|
| `soft` | Warning only if not called (default for `tool_called`) |
| `required` | Fail if tool not called |
| `strict` | Fail if not called OR params don't match |

### State Machine Validation

The `phase_transition_valid` assertion validates against these rules:
- `None` → `ARCHITECTURE`, `PLANNING`
- `ARCHITECTURE` → `PLANNING`
- `PLANNING` → `IN_TASK`
- `IN_TASK` → `BETWEEN_TASKS`
- `BETWEEN_TASKS` → `IN_TASK`, `PLANNING`, `COMPLETED`
- `COMPLETED` → `DEBUG`
- `DEBUG` → `COMPLETED`
- `BLOCKED` → `IN_TASK`, `BETWEEN_TASKS`, `PLANNING`, `COMPLETED`
- Any phase → `BLOCKED` (always valid)

## Writing New Scenarios

1. Create a new `.yaml` file in this directory
2. Define the conversation flow as a series of turns
3. Use flexible assertions (`response_contains_any`) to handle response variability
4. Always provide `text_fallback` for `AskUserQuestion` responses
5. Use `strictness: required` sparingly - Claude's tool selection is probabilistic
6. Test with `--keep --verbose` to debug failures

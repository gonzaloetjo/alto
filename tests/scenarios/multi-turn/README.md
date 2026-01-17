# Multi-Turn Protocol Test Scenarios

These scenarios test ALTO's orchestrator protocols by simulating human interaction across multiple conversation turns.

## Running Scenarios

```bash
# Run a single scenario
alto-test-multi --scenario setup-new-project

# Run with verbose output and keep test directory
alto-test-multi --scenario setup-new-project --keep --verbose

# Output as JSON (for CI)
alto-test-multi --scenario build-simple-feature --json
```

## Scenario Format

```yaml
name: scenario-name
description: What this scenario tests
type: multi-turn

orchestrator: setup | build
timeout_seconds: 600

# Optional: seed initial files
initial_state:
  objective_md: |
    Content for objective.md...

turns:
  - name: "turn-name"
    prompt: "What to send to Claude"
    timeout_seconds: 120  # Per-turn timeout
    expect:
      response_contains:
        - "must contain this"
      response_contains_any:
        - "or this"
        - "or that"
      tool_called: "AskUserQuestion"  # Soft check - warns if missing
      state:
        phase: "IN_TASK"
    user_response:
      select_option: "Option label"  # For AskUserQuestion
      text_fallback: "1"             # Fallback for plain text menus
      text: "Direct text response"   # Or just send text

final_assertions:
  files_exist:
    - expected-file.py
  file_contains:
    expected-file.py:
      - "expected content"
```

## Available Scenarios

| Scenario | Orchestrator | Description |
|----------|--------------|-------------|
| `setup-new-project` | setup | Complete setup flow from welcome to objective.md |
| `build-simple-feature` | build | Build orchestrator with pre-defined objective |

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

## Writing New Scenarios

1. Create a new `.yaml` file in this directory
2. Define the conversation flow as a series of turns
3. Use flexible assertions (`response_contains_any`) to handle response variability
4. Always provide `text_fallback` for `AskUserQuestion` responses
5. Test with `--keep --verbose` to debug failures

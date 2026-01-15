# ALTO Test Scenarios

Test scenarios for `alto-test-run` harness.

## Usage

```bash
# Run a scenario
alto-test-run --scenario simple-hello-world

# Run with JSON output
alto-test-run --scenario simple-hello-world --json

# Keep test directory for inspection
alto-test-run --scenario simple-hello-world --keep
```

## Scenario Format

```yaml
name: scenario-name
description: Brief description

orchestrator: build  # setup | build
objective: |
  The objective.md content...

prompt: "The prompt to send to Claude"

# Optional: expected outcomes for validation
expected:
  files_created:
    - file1.py
  output_contains: "text"
  max_duration_seconds: 120
```

## Available Scenarios

| Scenario | Description | Orchestrator |
|----------|-------------|--------------|
| `simple-hello-world` | Basic Python script creation | build |
| `setup-feature-definition` | Feature definition flow | setup |

## Adding New Scenarios

1. Create `tests/scenarios/<name>.yaml`
2. Define objective and expected outcomes
3. Test with `alto-test-run --scenario <name> --keep`
4. Verify results in the kept test directory

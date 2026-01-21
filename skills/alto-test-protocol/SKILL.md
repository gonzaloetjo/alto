---
name: alto-test-protocol
description: Use when testing ALTO protocol and finding issues. Run protocol tests, analyze artifacts, find issues, classify, and optionally fix. Invoked via /alto-test-protocol in dev mode.
---

# Protocol Test & Analysis

Test ALTO protocol, analyze results, find and fix issues.

**Requirement:** Run from ALTO source repo OR consumer project with `url: path:../alto-2` in devenv.yaml.

## Startup

Use AskUserQuestion:
- Header: "Mode"
- Question: "What would you like to do?"
- Options:
  1. Label: "Find issues", Description: "Run tests, analyze artifacts, identify protocol issues"
  2. Label: "Classify + suggest", Description: "Find issues, classify severity, suggest fixes"
  3. Label: "Full fix", Description: "Find, classify, create issues, implement fixes"

## Step 1: Run Tests

**CRITICAL:**
- Use 10 minute timeout
- Do NOT run in background
- WAIT for complete output before proceeding to Step 2

```bash
devenv shell -- alto-test-multi --all --json --keep
```

The command takes ~2-5 minutes for full suite. WAIT for it to finish completely.

Parse JSON from stdout. Structure:

```json
{
  "suite": true,
  "scenarios": 6,
  "passed": 4,
  "failed": 2,
  "total_turns": 16,
  "total_failures": 2,
  "results": [
    {
      "scenario": "setup-new-project",
      "success": true,
      "turns": 4,
      "failures": [],
      "test_dir": "/tmp/alto-multi-abc123"
    },
    {
      "scenario": "build-phase-transitions",
      "success": false,
      "turns": 3,
      "failures": [{"turn": "turn-2", "message": "phase_transition_valid failed"}],
      "test_dir": "/tmp/alto-multi-def456"
    }
  ]
}
```

Extract `test_dir` from each result in `results[]` array.

## Step 2: Read Artifacts

**Only proceed after Step 1 completes and you have the test_dir paths.**

For each `test_dir` from JSON:

### 2a. Check directory exists
```bash
ls -la $TEST_DIR/runs/
```

### 2b. Read state.json
```
Read $TEST_DIR/runs/state.json
```

**Check for:**
- Valid phases: `ARCHITECTURE`, `PLANNING`, `IN_TASK`, `BETWEEN_TASKS`, `BLOCKED`, `COMPLETED`
- `completed_tasks` grows as tasks finish
- `current_task` set during IN_TASK

### 2c. Read tool usage
```
Read $TEST_DIR/runs/tools/usage.jsonl
```

Each line: `{"tool": "Name", "params": {...}, "timestamp": "..."}`

**Check for:**
- Expected tools called (AskUserQuestion for menus, Write for files, Task for agents)
- No forbidden tools for the phase
- Correct tool order

### 2d. Read handoffs
```bash
ls $TEST_DIR/runs/handoffs/
```
Then read each file found.

**Required sections:** `## Summary`, `## Changes`, `## Status`

## Step 3: Analyze

Evaluate against protocol rules:

**Valid state transitions:**
```
None → ARCHITECTURE, PLANNING, IN_TASK
ARCHITECTURE → PLANNING
PLANNING → IN_TASK, BLOCKED
IN_TASK → BETWEEN_TASKS, BLOCKED, COMPLETED
BETWEEN_TASKS → IN_TASK, PLANNING, COMPLETED
BLOCKED → PLANNING, IN_TASK
```

**Issues to find (even if test passed):**
- Invalid state transitions
- Missing/incomplete handoffs
- Wrong tools for phase
- Unnecessary tool calls
- Protocol steps skipped

## Step 4: Report Issues

```markdown
## Issue 1: [scenario] - [summary]

**Scenario:** build-simple-feature
**Problem:** Handoff missing ## Changes section
**Evidence:** $TEST_DIR/runs/handoffs/task-001.md has ## Summary but no ## Changes
```

**If Mode 1: STOP here.**

## Step 5: Classify

For each issue:
- **Severity**: Critical | High | Medium | Low
- **Component**: File responsible
- **Root cause**: Why it happens
- **Suggested fix**: Specific change

Check duplicates: `gh issue list --repo gonzaloetjo/alto --label protocol-test --state open`

**If Mode 2: STOP here.**

## Step 6: Create Issues and Fix

```bash
gh issue create --repo gonzaloetjo/alto \
  --title "[protocol-test] component: summary" \
  --label "protocol-test,automated" \
  --body "..."
```

Then implement via `/alto-self-fix` workflow.

# Protocol Testing Implementation Analysis

*Created: 2026-01-17*
*Branch: feature/protocol-testing*

Honest assessment of what was implemented vs what the original plan targeted.

---

## Original Problem

The multi-turn protocol test infrastructure existed (`scripts/alto-test-multi.py`, 543 lines) but could not run due to:

```
[devenv:files]! Conflicting file .claude/settings.json
```

The manual `.claude/settings.json` conflicted with devenv's symlink management.

---

## What Was Actually Fixed

### 1. Devenv Conflict (Root Cause)

**Fixed:** Deleted the manual `.claude/settings.json` file. Devenv now regenerates it as a Nix store symlink with all permissions and hooks intact.

This was the **blocker** preventing any tests from running.

### 2. Python Dependency Issue

**Fixed:** Changed `devenv.nix` from:
```nix
packages = [ pkgs.python3Packages.pyyaml ];  # Not in PYTHONPATH
```
To:
```nix
python = pkgs.python3.withPackages (ps: [ ps.pyyaml ]);
exec ${python}/bin/python3 ...  # pyyaml available
```

Without this, tests failed with `ModuleNotFoundError: No module named 'yaml'`.

### 3. Shell Plugin Interference

**Fixed:** Changed from `subprocess.run(cmd, cwd=test_dir)` to:
```python
cmd = ["/bin/bash", "-c", f"cd '{self.test_dir}' && devenv shell -- {inner_cmd}"]
```

The user's zsh has `enhancd` plugin that overrides `cd`. Using Python's `cwd=` parameter still triggered zsh's cd hook. Wrapping in `/bin/bash -c` bypasses this.

### 4. Prompt Priority Bug

**Fixed:** The test harness ignored explicit turn prompts when there was a user_response from the previous turn:
```python
# Before (bug):
if next_prompt:
    prompt = next_prompt
else:
    prompt = turn.get("prompt", "")

# After (fixed):
turn_prompt = turn.get("prompt")
if turn_prompt:  # Explicit prompt takes precedence
    prompt = turn_prompt
elif next_prompt:
    prompt = next_prompt
```

This caused turn 4 of `setup-new-project` to send wrong prompt.

### 5. Non-Deterministic State Expectation

**Fixed:** Removed `state.phase: "IN_TASK"` expectation from `build-simple-feature.yaml`. Simple tasks complete in one turn, so phase is already COMPLETED.

---

## What the Original Plan Targeted

From `protocol-testing-plan.md`, the key challenges were:

| Challenge | Status | Notes |
|-----------|--------|-------|
| AskUserQuestion handling | **Partial** | Soft check only - logs warning if tool not detected, falls back to plain text menu parsing |
| Session continuity | **Working** | Session ID captured from `modes.json`, used with `--resume` |
| State verification | **Partial** | Only basic assertions (file exists, contains text). No phase transition validation. |
| Devenv overhead | **Not addressed** | Each turn runs full `devenv shell` startup (~2-3s overhead) |

---

## Does This Enable Autonomous Testing?

### Yes, for basic flows:
- **Setup orchestrator**: Can verify welcome → project definition → objective.md creation
- **Build orchestrator**: Can verify objective.md → hello.py → verification

### Evidence from actual test runs:

**setup-new-project (4 turns):**
```
Turn 1: "Welcome to ALTO" ✓
Turn 2: "Let's set up your project" ✓
Turn 3: Asked about features ✓
Turn 4: Created objective.md with 5 features ✓
```

**build-simple-feature (2 turns):**
```
Turn 1: Created hello.py, committed to branch ✓
Turn 2: Verified output ✓
```

### No, for these scenarios:
- **Complex state transitions**: No validation of `state.json` phase changes
- **AskUserQuestion reliability**: Claude doesn't always use the tool (probabilistic)
- **Error recovery**: No tests for BLOCKED state, arbiter checkpoints, replanning
- **Cost/speed**: Each turn costs ~$0.05-0.10 and takes 10-30s

---

## What's Still Missing

### 1. State Machine Validation
The harness doesn't verify:
- Phase transitions (ARCHITECTURE → PLANNING → IN_TASK → COMPLETED)
- Handoff file creation and format
- Task assignment state

### 2. Tool Call Verification
- `tool_called` is a "soft check" (warning only)
- No verification of tool parameters
- No verification of tool sequence

### 3. Negative Test Cases
- What happens when Claude hallucinates?
- What happens when a task fails?
- What happens at arbiter checkpoints?

### 4. Session Resume Reliability
- `modes.json` session tracking works
- But tests don't verify context preservation across turns

### 5. AskUserQuestion Determinism
The orchestrators sometimes output plain text menus instead of using `AskUserQuestion`. The harness handles this with `text_fallback`, but it means:
- Tests can't verify the tool was actually used
- Option selection may fail if menu format changes

---

## Recommendations

### Short-term
1. Add state.json phase assertions to scenarios
2. Add handoff file verification
3. Create negative test scenarios (missing files, invalid input)

### Medium-term
1. Make AskUserQuestion more deterministic in orchestrators
2. Add tool sequence verification (not just "was it called")
3. Reduce devenv overhead (warm shell, process pool)

### Long-term
1. Consider Agent SDK approach (more control, less overhead)
2. Cost-aware test selection (expensive tests run less often)
3. Parallel test execution

---

## Summary

| Aspect | Assessment |
|--------|------------|
| Original blocker | **Fixed** (settings.json conflict) |
| Tests run | **Yes** (both scenarios pass) |
| Multi-turn works | **Yes** (session resume functional) |
| Protocol verification | **Basic** (file creation, text contains) |
| State machine validation | **Missing** |
| Production-ready | **No** (needs more scenarios, reliability) |

The implementation successfully unblocks protocol testing and validates basic orchestrator flows. However, it's a foundation, not a comprehensive test suite. The scenarios prove Claude follows the happy path but don't verify edge cases, error handling, or complete protocol compliance.

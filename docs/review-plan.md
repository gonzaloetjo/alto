# ALTO Review Plan

> Consolidated review plan based on redundancy-analysis.md and architecture-analysis.md

*Created: 2026-01-12*

---

## Overview

This document consolidates findings from two analyses and proposes actionable tasks for improving ALTO. Each item is categorized by priority and includes implementation considerations.

---

## Task Categories

| Category | Description |
|----------|-------------|
| **REMOVE** | Component should be deleted |
| **SIMPLIFY** | Component should be reduced in scope |
| **KEEP** | Component provides unique value, no changes |
| **ADD** | New functionality needed |

---

## Review Items

### Item 1: alto-planner → Use EnterPlanMode

**Source:** redundancy-analysis.md
**Category:** REMOVE / SIMPLIFY
**Priority:** Medium

**Current State:**
- `alto-planner` agent generates `runs/plan.md` and task files
- Separate "PLANNING" phase in state machine

**Native Equivalent:**
- `EnterPlanMode` + `ExitPlanMode` for user-approved planning
- `TodoWrite` for task tracking

**Discussion Points:**
- [ ] Does EnterPlanMode provide sufficient structure for task decomposition?
- [ ] Can we use TodoWrite for in-session tracking, task files only for persistence?
- [ ] What's lost if we remove the formal planning phase?

**Proposed Action:**
- Option A: Remove alto-planner entirely, use EnterPlanMode
- Option B: Simplify alto-planner to only write task files (not orchestrate)
- Option C: Keep as-is for explicit separation

---

### Item 2: Role Agents → Task Subagent Prompts

**Source:** redundancy-analysis.md
**Category:** SIMPLIFY
**Priority:** Medium

**Current State:**
- 4 role agents: `alto-backend`, `alto-frontend`, `alto-qa`, `alto-docs`
- Each has dedicated `.md` file with constraints

**Native Equivalent:**
- `Task` tool with `subagent_type` already supports role-based delegation
- Prompts can include constraints inline

**Discussion Points:**
- [ ] Do separate agent files provide value beyond inline prompts?
- [ ] Is the `allowed_paths` constraint enforceable via Task prompts?
- [ ] Would merging reduce maintainability?

**Proposed Action:**
- Option A: Merge agent constraints into CLAUDE.md as prompt templates
- Option B: Keep agents but document they're "prompt libraries" not orchestration
- Option C: Keep as-is for explicit separation

---

### Item 3: alto-enforcer → Remove

**Source:** redundancy-analysis.md
**Category:** REMOVE
**Priority:** Low

**Current State:**
- Enforcer checks protocol compliance after reviewer
- Can reject back to agent

**Native Equivalent:**
- Claude Code has built-in sandboxing and permission controls
- `settings.json` deny lists already prevent forbidden operations

**Discussion Points:**
- [ ] Is there value in explicit protocol compliance checking?
- [ ] Does the 2-rejection-cycle limit add safety or just overhead?
- [ ] Could this be merged into alto-reviewer?

**Proposed Action:**
- Option A: Remove entirely
- Option B: Merge into alto-reviewer as "compliance section"
- Option C: Keep for explicit separation

---

### Item 4: alto-recorder → Session Boundary Only

**Source:** redundancy-analysis.md
**Category:** SIMPLIFY
**Priority:** Low

**Current State:**
- Runs after every task
- Writes `task-XXX-recorder.md` summaries

**Native Equivalent:**
- Conversation context preserved within session
- Handoffs only needed for cross-session

**Discussion Points:**
- [ ] Is per-task recording valuable or just overhead?
- [ ] Could we record only at session end (via Stop hook)?
- [ ] What context is lost if we skip mid-session recording?

**Proposed Action:**
- Option A: Only record at session boundaries
- Option B: Record every N tasks (configurable)
- Option C: Keep as-is for complete audit trail

---

### Item 5: alto-reviewer → Simplify

**Source:** architecture-analysis.md
**Category:** SIMPLIFY
**Priority:** Medium

**Current State:**
- Opus model for code quality review
- Can reject with 3-cycle limit

**Discussion Points:**
- [ ] Is Opus necessary, or would Sonnet suffice?
- [ ] Could review be inline with task execution (single agent)?
- [ ] Is the rejection cycle worth the token cost?

**Proposed Action:**
- Option A: Switch to Sonnet model
- Option B: Merge review into task agent's check_command loop
- Option C: Keep as quality gate (current)

---

### Item 6: Hook Reliability

**Source:** architecture-analysis.md
**Category:** ADD
**Priority:** High

**Current State:**
- 7 Python hooks run on lifecycle events
- No error handling visible
- Silent failures possible

**Proposed Action:**
- [ ] Add try/catch wrappers to all hooks
- [ ] Create `runs/errors.jsonl` for hook failures
- [ ] Add health check on session start
- [ ] Consider retry mechanism for transient failures

**Implementation Notes:**
```python
# Pattern for hook error handling
try:
    # hook logic
except Exception as e:
    with open("runs/errors.jsonl", "a") as f:
        json.dump({"hook": __file__, "error": str(e), "ts": ...}, f)
```

---

### Item 7: Lite Mode

**Source:** architecture-analysis.md
**Category:** ADD
**Priority:** Medium

**Current State:**
- All 11 agents always deployed
- No way to reduce complexity for simple projects

**Proposed Action:**
- [ ] Add `alto.mode = "lite" | "full"` option
- [ ] Lite mode: arbiter + gitops + persistence only
- [ ] Full mode: all agents (current behavior)

**Implementation Notes:**
```nix
alto = {
  mode = "lite";  # or "full"
};
```

Lite mode would deploy:
- `alto-arbiter` (human gates)
- `alto-gitops` (commits)
- Persistence layer (state.json, handoffs)
- Skip: planner, reviewer, enforcer, recorder, role agents

---

### Item 8: Handoff Schema Validation

**Source:** architecture-analysis.md
**Category:** ADD
**Priority:** Low

**Current State:**
- Handoffs follow documented format
- No runtime validation

**Proposed Action:**
- [ ] Define JSON schema for handoff frontmatter
- [ ] Add validation in session-start.py
- [ ] Warn/fail on malformed handoffs

---

### Item 9: Native Tool Documentation

**Source:** architecture-analysis.md
**Category:** ADD
**Priority:** Medium

**Current State:**
- No explicit guidance on ALTO vs native tools

**Proposed Action:**
- [ ] Add "When to Use ALTO" section to README
- [ ] Decision tree: project size → recommended mode
- [ ] Examples of native-only vs ALTO workflows

---

### Item 10: Run Branch Management

**Source:** architecture-analysis.md
**Category:** ADD
**Priority:** Low

**Current State:**
- `run/001`, `run/002` accumulate
- No cleanup strategy

**Proposed Action:**
- [ ] Document branch lifecycle in ARCHITECTURE.md
- [ ] Add optional `alto.cleanupAfterRuns = 5` to auto-delete old branches
- [ ] Or: squash completed runs into main

---

## Summary Matrix

| Item | Action | Priority | Effort | Impact |
|------|--------|----------|--------|--------|
| 1. alto-planner | DISCUSS | Medium | High | Medium |
| 2. Role agents | DISCUSS | Medium | Medium | Low |
| 3. alto-enforcer | REMOVE? | Low | Low | Low |
| 4. alto-recorder | SIMPLIFY | Low | Low | Low |
| 5. alto-reviewer | SIMPLIFY | Medium | Medium | Medium |
| 6. Hook reliability | ADD | High | Medium | High |
| 7. Lite mode | ADD | Medium | High | High |
| 8. Handoff validation | ADD | Low | Low | Low |
| 9. Native docs | ADD | Medium | Low | Medium |
| 10. Branch management | ADD | Low | Low | Low |

---

## Next Steps

1. Review this document together
2. Mark decisions for each item (implement / defer / reject)
3. Create implementation tasks for approved items
4. Update ARCHITECTURE.md with decisions

---

*This is a living document. Update as decisions are made.*

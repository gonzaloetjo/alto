# ALTO Protocol

> Action classification and execution model for ALTO orchestration.

---

## Classification Axes

Actions are classified along three axes (1-5 scale). These are **requirements** that determine execution type.

| Axis | 1 | 2 | 3 | 4 | 5 |
|------|---|---|---|---|---|
| **Input** | None | Minimal | Partial | Significant | Full |
| **Output** | Deterministic | Mostly Det. | Mixed | Mostly Judg. | Judgment |
| **Process** | Atomic | Simple | Moderate | Complex | Compound |

---

## Routing Matrix

Requirements (axes) determine execution type:

| In | Out | Proc | → Runs As | Why |
|:--:|:---:|:----:|-----------|-----|
| ≤2 | ≤2 | ≤2 | **hook** | Deterministic, low context, atomic → Python script |
| ≤2 | ≥3 | ≤2 | **skill** | Needs judgment, minimal context → on-demand procedure |
| ≥3 | ≥3 | ≥3 | **subagent** | Context + judgment + multi-step → isolated subprocess |
| ≥4 | ≥4 | ≥4 | **orchestrator** | Full context, high judgment, coordination → main conversation |

> **Validation**: If `Runs As` doesn't match routing matrix for given axes, the action is mis-specified.

---

## Column Reference

### Runs As

| Value | Description |
|-------|-------------|
| `hook` | Python script triggered by Claude Code event |
| `subagent` | Spawned subprocess with isolated context |
| `orchestrator` | Main conversation (CLAUDE.md.{mode} template) |
| `skill` | On-demand procedure invoked in current context |

### Defined In

The source file where the action's behavior is specified:
- Hooks: `hooks/*.py`
- Subagents: `agents/*.md`
- Orchestrator: `templates/CLAUDE.md.{mode}`
- Skills: `skills/*/SKILL.md`

### Triggerer

| Value | Meaning |
|-------|---------|
| Event name | Claude Code hook event (SessionStart, PostToolUse, SubagentStop, etc.) |
| `user` | Explicit user input |
| `self` | The agent's own execution flow |
| `parent` | Orchestrator spawns this subagent |
| `#index` | Previous action's completion triggers this |

### Constrained By

Passive rules that constrain the action's output format. These don't execute—they define requirements the action must follow.

---

## Agent Categories

| Category | Agents | Purpose |
|----------|--------|---------|
| **impl** | alto-backend, alto-frontend | Write production code |
| **tester** | alto-qa | Write tests |
| **reviewer** | alto-reviewer | Quality gates |
| **controller** | alto-arbiter | Checkpoint decisions |
| **planner** | alto-planner | Create tasks |
| **support** | alto-docs, code-simplifier, alto-feature-finder | Documentation, refactoring, analysis |

---

## Setup Mode Actions

| # | Action | In | Out | Proc | → Runs As | Defined In | Triggerer | Constrained By |
|---|--------|:--:|:---:|:----:|-----------|------------|-----------|----------------|
| 1 | Initialize session | 2 | 1 | 1 | hook | session-start.py | SessionStart | — |
| 2 | Record tool usage | 2 | 1 | 1 | hook | tool-record.py | PostToolUse | — |
| 3 | Record usage | 2 | 1 | 1 | hook | usage-record.py | Stop | — |
| 4 | Summarize session | 3 | 1 | 2 | hook | session-summary.py | SessionEnd | — |
| 5 | Configure settings | 2 | 3 | 3 | skill | alto-configure | user | — |
| 6 | Define feature | 3 | 3 | 3 | skill | alto-objective | user | — |
| 7 | Analyze codebase | 4 | 4 | 3 | subagent | alto-feature-finder | parent | — |

---

## Build Mode Actions

### Session Lifecycle

| # | Action | In | Out | Proc | → Runs As | Defined In | Triggerer | Constrained By |
|---|--------|:--:|:---:|:----:|-----------|------------|-----------|----------------|
| 1 | Initialize session | 2 | 1 | 1 | hook | session-start.py | SessionStart | — |
| 2 | Record tool usage | 2 | 1 | 1 | hook | tool-record.py | PostToolUse | — |
| 3 | Record usage | 2 | 1 | 1 | hook | usage-record.py | Stop | — |
| 4 | Summarize session | 3 | 1 | 2 | hook | session-summary.py | SessionEnd | — |

### Architecture Phase

| # | Action | In | Out | Proc | → Runs As | Defined In | Triggerer | Constrained By |
|---|--------|:--:|:---:|:----:|-----------|------------|-----------|----------------|
| 10 | Explore & architect | 5 | 5 | 5 | orchestrator | CLAUDE.md.build | user | — |
| 10.1 | Read objective | 2 | 2 | 1 | orchestrator | CLAUDE.md.build | self | — |
| 10.2 | Analyze codebase | 4 | 4 | 3 | subagent | alto-feature-finder | parent | — |
| 10.3 | Write milestones | 4 | 4 | 3 | orchestrator | CLAUDE.md.build | #10.2 | — |
| 10.4 | Write decisions | 4 | 4 | 3 | orchestrator | CLAUDE.md.build | #10.2 | — |

### Planning Phase

| # | Action | In | Out | Proc | → Runs As | Defined In | Triggerer | Constrained By |
|---|--------|:--:|:---:|:----:|-----------|------------|-----------|----------------|
| 20 | Plan tasks | 4 | 4 | 4 | subagent | alto-planner | parent | — |
| 20.1 | Read milestones | 2 | 2 | 1 | subagent | alto-planner | self | — |
| 20.2 | Create task files | 3 | 4 | 3 | subagent | alto-planner | #20.1 | formats/task.md |
| 21 | Validate task | 2 | 1 | 1 | hook | task-validate.py | PostToolUse | — |
| 22 | Validate phase | 2 | 1 | 1 | hook | phase-validate.py | PostToolUse | — |

### Execution Loop

| # | Action | In | Out | Proc | → Runs As | Defined In | Triggerer | Constrained By |
|---|--------|:--:|:---:|:----:|-----------|------------|-----------|----------------|
| 30 | Check arbiter pending | 2 | 2 | 1 | orchestrator | CLAUDE.md.build | self | — |
| 31 | Assess checkpoint risk | 3 | 4 | 2 | subagent | alto-arbiter | parent | — |
| 32 | Decide block/continue | 3 | 2 | 1 | orchestrator | CLAUDE.md.build | #31 | — |
| 33 | Pick next task | 3 | 3 | 2 | orchestrator | CLAUDE.md.build | #32 | — |
| 34 | Invoke role agent | 3 | 3 | 2 | orchestrator | CLAUDE.md.build | #33 | — |
| 35 | Schedule arbiter | 3 | 1 | 2 | hook | arbiter-scheduler.py | SubagentStop | — |
| 36 | Block for human | 3 | 3 | 2 | orchestrator | CLAUDE.md.build | #32 | — |
| 37 | Resume from block | 3 | 4 | 2 | orchestrator | CLAUDE.md.build | user | — |
| 38 | Decide replan | 3 | 3 | 2 | orchestrator | CLAUDE.md.build | #33 | — |

### Task Execution (Role Agent)

| # | Action | In | Out | Proc | → Runs As | Defined In | Triggerer | Constrained By |
|---|--------|:--:|:---:|:----:|-----------|------------|-----------|----------------|
| 40 | Implement task | 4 | 5 | 5 | subagent | alto-{role} | parent | — |
| 40.1 | Read task file | 2 | 2 | 1 | subagent | alto-{role} | self | — |
| 40.2 | Read previous handoff | 2 | 2 | 1 | subagent | alto-{role} | #40.1 | — |
| 40.3 | Write code | 4 | 5 | 5 | subagent | alto-{role} | #40.2 | — |
| 40.4 | Run verification | 2 | 2 | 2 | subagent | alto-{role} | #40.3 | — |
| 40.5 | Write handoff | 3 | 3 | 2 | subagent | alto-{role} | #40.4 | formats/handoff.md |
| 41 | Validate handoff | 2 | 1 | 1 | hook | handoff-validate.py | SubagentStop | — |
| 42 | Create handoff template | 2 | 1 | 1 | hook | handoff-template.py | PostToolUse | — |

> **alto-{role}** = any implementer agent (alto-backend, alto-frontend, etc.). All follow the same execution pattern.

### Post-Task Processing

| # | Action | In | Out | Proc | → Runs As | Defined In | Triggerer | Constrained By |
|---|--------|:--:|:---:|:----:|-----------|------------|-----------|----------------|
| 50 | Assess code quality | 3 | 4 | 2 | subagent | alto-reviewer | parent | formats/review.md |
| 51 | Validate review | 2 | 1 | 1 | hook | review-validate.py | SubagentStop | — |
| 52 | Decide approve/reject | 3 | 3 | 1 | orchestrator | CLAUDE.md.build | #50 | — |
| 53 | Write tests | 4 | 4 | 4 | subagent | alto-qa | parent | formats/handoff.md |
| 53.1 | Run tests | 2 | 2 | 2 | subagent | alto-qa | self | — |
| 53.2 | Fix test failures | 3 | 4 | 3 | subagent | alto-qa | #53.1 | — |
| 54 | Refactor code | 3 | 4 | 4 | subagent | code-simplifier | parent | formats/handoff.md |
| 55 | Write documentation | 3 | 4 | 3 | subagent | alto-docs | parent | formats/handoff.md |
| 56 | Execute git commit | 2 | 2 | 2 | subagent | alto-gitops | parent | — |
| 57 | Record permissions | 2 | 1 | 1 | hook | permission-record.py | PermissionRequest | — |

### Completion

| # | Action | In | Out | Proc | → Runs As | Defined In | Triggerer | Constrained By |
|---|--------|:--:|:---:|:----:|-----------|------------|-----------|----------------|
| 60 | Mark task complete | 2 | 2 | 1 | orchestrator | CLAUDE.md.build | #56 | — |
| 61 | Update state | 2 | 2 | 1 | orchestrator | CLAUDE.md.build | #60 | — |
| 62 | Update DoD | 2 | 2 | 1 | orchestrator | CLAUDE.md.build | #61 | — |
| 63 | Complete feature | 2 | 2 | 1 | orchestrator | CLAUDE.md.build | #62 | — |
| 64 | Enter debug mode | 2 | 2 | 1 | orchestrator | CLAUDE.md.build | user | — |

---

## Passive Constraints

These don't execute—they constrain actions that do.

| Constraint | File | Applies To | Required Content |
|------------|------|------------|------------------|
| Task format | formats/task.md | #20.2 | Frontmatter: task_id, title, role, allowed_paths, handoff. Section: ## Definition of Done |
| Handoff format | formats/handoff.md | #40.5, #53, #54, #55 | Sections: ## Summary, ## Files Touched, ## How to Verify |
| Review format | formats/review.md | #50 | **Status:** APPROVED\|REJECTED. Section: ## Reason (if rejected) |
| Scope discipline | rules/scope-discipline.md | #40.3, #53 | Prevents out-of-scope work |
| Prompt writing | rules/prompt-writing.md | dev orchestrator | Explicit tool names and paths |

### Constraint Enforcement

| Constraint | Enforced By | Mechanism |
|------------|-------------|-----------|
| Task format | task-validate.py | Blocks invalid task files |
| Handoff format | handoff-validate.py | Blocks invalid handoffs |
| Review format | review-validate.py | Blocks invalid reviews |
| Scope discipline | — | Suggestion only (no hook) |
| Prompt writing | — | Suggestion only (no hook) |

> **Key insight**: Format rules (formats/*.md) have validation hooks. Behavioral rules (rules/*.md) are suggestions only.

---

## Skills Reference

On-demand procedures invoked by user or context-matched:

| Skill | Invoked At | Purpose |
|-------|------------|---------|
| alto-configure | #5 | Edit alto.json settings |
| alto-objective | #6 | Define feature in objective.md |
| alto-protocol | any | Reference for ALTO conventions |
| alto-switch | user | Switch orchestrator mode |

---

## Validation Summary

| What | Hook | Triggers On | Blocks On |
|------|------|-------------|-----------|
| Task files | task-validate.py | PostToolUse (Write to runs/tasks/) | Missing frontmatter, invalid role |
| Phase transitions | phase-validate.py | PostToolUse (Write to state.json) | Invalid transition (reverts) |
| Handoff files | handoff-validate.py | SubagentStop | Missing required sections |
| Review files | review-validate.py | SubagentStop | Missing status, no reason for rejection |

# ALTO Protocol

> Action classification and execution model for ALTO orchestration.

---

## Classification Axes

Actions are classified along three axes (1-5 scale):

| Axis | 1 | 2 | 3 | 4 | 5 |
|------|---|---|---|---|---|
| **Input** | None | Minimal | Partial | Significant | Full |
| **Output** | Deterministic | Mostly Det. | Mixed | Mostly Judg. | Judgment |
| **Process** | Atomic | Simple | Moderate | Complex | Compound |

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

> Agent .md files follow naming: `alto-{name}.md` (e.g., `alto-backend.md`, `alto-planner.md`)

---

## Column Reference

### Type

| Type | Description |
|------|-------------|
| `hook` | Python script triggered by Claude Code events |
| `orchestrator` | Action defined in CLAUDE.md.{mode} template |
| `agent` | Action executed by a spawned agent |
| `skill` | Reusable procedure (can be active or passive) |
| `rule` | Format constraint applied to agent output |

### Executor

| Type | Executor Value |
|------|----------------|
| `hook` | .py filename (e.g., `session-start.py`) |
| `orchestrator` | `CLAUDE.md.build` or `CLAUDE.md.setup` |
| `agent` | Category name (impl, planner, support, etc.) |
| `skill` | Skill name (e.g., `alto-configure`) |
| `rule` | Format file (e.g., `formats/handoff.md`) |

### Triggerer

| Value | Meaning |
|-------|---------|
| Event name | Claude Code hook event (SessionStart, PostToolUse, SubagentStop, etc.) |
| `user` | Explicit user input |
| `self` | The .md file's own execution flow |
| `parent` | Orchestrator invokes this agent |
| `#index` | Previous action's completion triggers this |

---

## Setup Mode Actions

| # | Action | Type | Executor | Triggerer | Context | In | Out | Proc |
|---|--------|------|----------|-----------|---------|:--:|:---:|:----:|
| 1 | Initialize session | hook | session-start.py | SessionStart | project state | 2 | 1 | 1 |
| 2 | Record tool usage | hook | tool-record.py | PostToolUse | tool call | 2 | 1 | 1 |
| 3 | Record usage | hook | usage-record.py | Stop | session data | 2 | 1 | 1 |
| 4 | Summarize session | hook | session-summary.py | SessionEnd | session data | 3 | 1 | 2 |
| 5 | Configure settings | skill | alto-configure | user | alto.json | 2 | 3 | 3 |
| 6 | Define feature | skill | alto-objective | user | user input | 3 | 3 | 3 |
| 7 | Analyze codebase | agent | support | parent | objective.md | 4 | 4 | 3 |

---

## Build Mode Actions

### Session Lifecycle

| # | Action | Type | Executor | Triggerer | Context | In | Out | Proc |
|---|--------|------|----------|-----------|---------|:--:|:---:|:----:|
| 1 | Initialize session | hook | session-start.py | SessionStart | project state | 2 | 1 | 1 |
| 2 | Record tool usage | hook | tool-record.py | PostToolUse | tool call | 2 | 1 | 1 |
| 3 | Record usage | hook | usage-record.py | Stop | session data | 2 | 1 | 1 |
| 4 | Summarize session | hook | session-summary.py | SessionEnd | session data | 3 | 1 | 2 |

### Architecture Phase

| # | Action | Type | Executor | Triggerer | Context | In | Out | Proc |
|---|--------|------|----------|-----------|---------|:--:|:---:|:----:|
| 10 | Explore & architect | orchestrator | CLAUDE.md.build | user | objective.md | 5 | 5 | 5 |
| 10.1 | Read objective | orchestrator | CLAUDE.md.build | self | objective.md | 2 | 2 | 1 |
| 10.2 | Analyze codebase | agent | support | parent | objective.md | 4 | 4 | 3 |
| 10.3 | Write milestones | orchestrator | CLAUDE.md.build | #10.2 | analysis | 4 | 4 | 3 |
| 10.4 | Write decisions | orchestrator | CLAUDE.md.build | #10.2 | analysis | 4 | 4 | 3 |

### Planning Phase

| # | Action | Type | Executor | Triggerer | Context | In | Out | Proc |
|---|--------|------|----------|-----------|---------|:--:|:---:|:----:|
| 20 | Plan tasks | agent | planner | parent | milestones | 4 | 4 | 4 |
| 20.1 | Read milestones | agent | planner | self | milestones.md | 2 | 2 | 1 |
| 20.2 | Create task files | agent | planner | #20.1 | task breakdown | 3 | 4 | 3 |
| 20.3 | Format task file | rule | formats/task.md | #20.2 | task content | 2 | 2 | 1 |
| 21 | Validate task | hook | task-validate.py | PostToolUse | task file | 2 | 1 | 1 |
| 22 | Validate phase | hook | phase-validate.py | PostToolUse | state.json | 2 | 1 | 1 |

### Execution Loop

| # | Action | Type | Executor | Triggerer | Context | In | Out | Proc |
|---|--------|------|----------|-----------|---------|:--:|:---:|:----:|
| 30 | Check arbiter pending | orchestrator | CLAUDE.md.build | self | pending.json | 2 | 2 | 1 |
| 31 | Assess checkpoint risk | agent | controller | parent | metrics, logs | 3 | 4 | 2 |
| 32 | Decide block/continue | orchestrator | CLAUDE.md.build | #31 | assessment | 3 | 2 | 1 |
| 33 | Pick next task | orchestrator | CLAUDE.md.build | #32 | state, tasks | 3 | 3 | 2 |
| 34 | Invoke role agent | orchestrator | CLAUDE.md.build | #33 | task, context | 3 | 3 | 2 |
| 35 | Schedule arbiter | hook | arbiter-scheduler.py | SubagentStop | metrics | 3 | 1 | 2 |
| 36 | Block for human | orchestrator | CLAUDE.md.build | #32 | blocker info | 3 | 3 | 2 |
| 37 | Resume from block | orchestrator | CLAUDE.md.build | user | human input | 3 | 4 | 2 |
| 38 | Decide replan | orchestrator | CLAUDE.md.build | #33 | state, milestones | 3 | 3 | 2 |

### Task Execution (Role Agent)

| # | Action | Type | Executor | Triggerer | Context | In | Out | Proc |
|---|--------|------|----------|-----------|---------|:--:|:---:|:----:|
| 40 | Implement task | agent | impl | parent | task file | 4 | 5 | 5 |
| 40.1 | Read task file | agent | impl | self | task file | 2 | 2 | 1 |
| 40.2 | Read previous handoff | agent | impl | #40.1 | handoff file | 2 | 2 | 1 |
| 40.3 | Write code | agent | impl | #40.2 | task context | 4 | 5 | 5 |
| 40.4 | Run verification | agent | impl | #40.3 | verify steps | 2 | 2 | 2 |
| 40.5 | Write handoff | agent | impl | #40.4 | impl summary | 3 | 3 | 2 |
| 40.6 | Format handoff | rule | formats/handoff.md | #40.5 | handoff content | 2 | 2 | 1 |
| 41 | Validate handoff | hook | handoff-validate.py | SubagentStop | handoff file | 2 | 1 | 1 |
| 42 | Create handoff template | hook | handoff-template.py | PostToolUse | state.json | 2 | 1 | 1 |

> **impl** = any implementer agent (alto-backend, alto-frontend). All follow the same execution pattern.

### Post-Task Processing

| # | Action | Type | Executor | Triggerer | Context | In | Out | Proc |
|---|--------|------|----------|-----------|---------|:--:|:---:|:----:|
| 50 | Assess code quality | agent | reviewer | parent | handoff, diff | 3 | 4 | 2 |
| 50.1 | Format review | rule | formats/review.md | #50 | review content | 2 | 2 | 1 |
| 51 | Validate review | hook | review-validate.py | SubagentStop | review file | 2 | 1 | 1 |
| 52 | Decide approve/reject | orchestrator | CLAUDE.md.build | #50 | assessment | 3 | 3 | 1 |
| 53 | Write tests | agent | tester | parent | handoff, impl | 4 | 4 | 4 |
| 53.1 | Run tests | agent | tester | self | test files | 2 | 2 | 2 |
| 53.2 | Fix test failures | agent | tester | #53.1 | test output | 3 | 4 | 3 |
| 54 | Refactor code | agent | support | parent | handoff, files | 3 | 4 | 4 |
| 55 | Write documentation | agent | support | parent | handoff, plan | 3 | 4 | 3 |
| 56 | Execute git commit | agent | support | parent | staged files | 2 | 2 | 2 |
| 57 | Record permissions | hook | permission-record.py | PermissionRequest | permission req | 2 | 1 | 1 |

### Completion

| # | Action | Type | Executor | Triggerer | Context | In | Out | Proc |
|---|--------|------|----------|-----------|---------|:--:|:---:|:----:|
| 60 | Mark task complete | orchestrator | CLAUDE.md.build | #56 | state.json | 2 | 2 | 1 |
| 61 | Update state | orchestrator | CLAUDE.md.build | #60 | state.json | 2 | 2 | 1 |
| 62 | Update DoD | orchestrator | CLAUDE.md.build | #61 | objective.md | 2 | 2 | 1 |
| 63 | Complete feature | orchestrator | CLAUDE.md.build | #62 | state | 2 | 2 | 1 |
| 64 | Enter debug mode | orchestrator | CLAUDE.md.build | user | user choice | 2 | 2 | 1 |

---

## Passive Constraints

| Constraint | Type | Applies To | Where | Soft | Strong | Effect |
|------------|------|------------|-------|------|--------|--------|
| Scope discipline | skill | impl, tester | skills/scope-discipline/ | #40.3, #53 | — | Prevents out-of-scope work |
| Path restrictions | rule | role agents | agents/*.md | — | — | Limits file access per agent |
| Prompt writing | rule | orchestrator, agents | CLAUDE.md.* | — | — | Enforces explicit tool/path references |
| Handoff format | rule | impl, reviewer | formats/handoff.md | — | #40.5, #50 | Structures agent output |
| Task format | rule | planner | formats/task.md | — | #20.2 | Structures task files |
| Review format | rule | reviewer | formats/review.md | — | #50 | Structures review output |
| alto-configure | skill | orchestrator | skills/alto-configure/ | — | #5 | Configuration procedures |
| alto-objective | skill | orchestrator | skills/alto-objective/ | — | #6 | Feature definition procedures |
| alto-protocol | skill | all agents | skills/alto-protocol/ | any | — | Reference for ALTO conventions |

### Column Reference

| Column | Meaning |
|--------|---------|
| **Where** | Location where the rule/skill is defined |
| **Soft** | Actions where it *could* be used (probabilistic, description-matched) |
| **Strong** | Actions where it *must* be used (explicitly referenced/required) |

### Rules vs Skills

| Aspect | Rules | Skills |
|--------|-------|--------|
| **Loading** | Always in context when referencing agent runs | On-demand (lazy loading) |
| **Activation** | Deterministic — embedded in agent .md | Probabilistic — description matching or explicit call |
| **Where defined** | `formats/*.md` or embedded in `agents/*.md` | `skills/*/SKILL.md` |
| **Propagation** | Referenced per-agent | Can be shared across agents |

> - **Rules**: Format/convention constraints. Always active for agents that reference them.
> - **Skills**: On-demand procedures. Soft = could auto-invoke via description. Strong = explicitly called.

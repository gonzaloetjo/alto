# ALTO Architecture

> Autonomous Lifecycle Task Orchestrator for Claude Code

Human-readable design document covering the models and lifecycle of ALTO.

---

## Overview

ALTO is a multi-agent orchestration protocol for Claude Code that provides:
- **Session persistence** across Claude Code restarts
- **Human review gates** via the arbiter system
- **Structured handoffs** between specialized agents
- **Git-based audit trail** with run branches

---

## The Three Modes

ALTO uses three orchestrator modes, each with distinct purposes:

| Mode | Purpose | Human Interaction |
|------|---------|-------------------|
| **setup** | Project initialization, feature definition, configuration | Interactive |
| **build** | Autonomous execution of features | Minimal (checkpoints) |
| **dev** | ALTO development | Interactive |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ALTO ORCHESTRATOR MODES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SETUP MODE              BUILD MODE                  DEV MODE               │
│   (Human-Interactive)     (Autonomous)               (Meta)                  │
│                                                                              │
│   • Project init          • Architecture             • ALTO development      │
│   • Feature definition    • Task planning            • Single alto-dev agent │
│   • Configuration         • Task execution           • Minimal hooks         │
│   • Cleanup               • Rolling replan           • Dev-specific skills   │
│   • Onboarding            • Arbiter checkpoints                              │
│                                                                              │
│         │                       │                                            │
│         │ "Start building"      │ "Next feature"                             │
│         └──────────►   ◄────────┘                                            │
│                                                                              │
│   Switch: alto <mode>                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Setup Mode

Handles human-interactive tasks:
- Writing `objective.md` interactively
- Configuring arbiter thresholds, permissions, verification
- Cleanup after feature completion
- Explaining ALTO to new users

### Build Mode

Handles autonomous execution:
- Architecture phase (milestones, decisions)
- Planning phase (task generation)
- Execution loop (role agents, QA, gitops)
- Arbiter checkpoints with optional reconfiguration
- Feature completion (debug mode, next feature)

### Dev Mode

For developing ALTO itself:
- Single `alto-dev` agent with full access
- Development-focused skills (`alto-dev-guide`, `writing-alto-skills`)
- Minimal hooks (just `changelog-check`)

See **DEVELOPMENT.md** for details.

---

## Feature Lifecycle

Features flow through a defined lifecycle:

```
objective.md → Architecture → Planning → Execution → Completion
```

### 1. Objective Definition (Setup Mode)

User defines what to build in `objective.md`:
- Overview of the feature
- Numbered feature items
- Definition of Done for each
- Testing and verification patterns

### 2. Architecture Phase (Build Mode)

Orchestrator explores codebase and designs approach:
- Reads `objective.md`
- Analyzes existing code patterns
- Writes `runs/milestones.md` (high-level steps)
- Writes `runs/decisions.md` (architectural choices)
- User approves (if `require_approval` is true)

### 3. Planning Phase (Build Mode)

Planner agent generates tasks:
- Reads milestones and decisions
- Creates `runs/plan.md` with task breakdown
- Creates individual `runs/tasks/task-XXX.md` files
- Each task specifies role, allowed paths, DoD

### 4. Execution Loop (Build Mode)

Tasks are executed by specialized agents:
1. **Arbiter check** — Block if thresholds exceeded
2. **Role agent** — Implements the task (backend, frontend, qa, docs)
3. **Verification** — Run task's verification steps
4. **Handoff** — Write structured output to `runs/handoffs/`
5. **Post-agents** — QA, code-simplifier, gitops
6. **Advance** — Mark complete, move to next task

### 5. Completion (Build Mode → Setup Mode)

When all tasks complete:
- Offer debug mode (test and fix pre-merge)
- Offer next feature (merge, cleanup, new objective)
- Offer reconfigure (adjust settings)

---

## State Machine

Build mode tracks progress through phases:

| Phase | Description |
|-------|-------------|
| `ARCHITECTURE` | Orchestrator exploring codebase, designing milestones |
| `PLANNING` | Planner generating task files from milestones |
| `IN_TASK` | Role agent executing a task |
| `BETWEEN_TASKS` | Task completed; arbiter may trigger; replan may occur |
| `BLOCKED` | Human review required |
| `COMPLETED` | All tasks done |
| `DEBUG` | Human testing pre-merge |

**Transitions:**
```
ARCHITECTURE → PLANNING → BETWEEN_TASKS ⟷ IN_TASK
                                ↓
                            BLOCKED
                                ↓
                            COMPLETED → DEBUG
```

---

## Agents Model

Agents are specialized subprocesses with constrained capabilities:

| Agent | Mode | Purpose | Key Constraints |
|-------|------|---------|-----------------|
| `alto-planner` | build | Create tasks from milestones | No Bash, runs/ only |
| `alto-feature-finder` | both | Analyze codebase | Read-only |
| `alto-backend` | build | API, DB, worker logic | Path-restricted |
| `alto-frontend` | build | UI, charts, client state | Path-restricted |
| `alto-qa` | build | Tests, verification config | Runs after role agents |
| `alto-docs` | build | Documentation | docs/ only |
| `alto-gitops` | build | Branch/commit/push | Prompts for git |
| `alto-reviewer` | build | Code quality gate | Read-only, can reject |
| `alto-arbiter` | build | Checkpoint auditor | arbiter/ only |
| `code-simplifier` | build | Refine code | Touched files only |
| `alto-dev` | dev | ALTO development | Full access |

**Communication model:** Agents write to files (`runs/handoffs/`), never to each other directly. The orchestrator reads outputs and passes context to the next agent.

**Post-agent flow:** Role implements → QA tests → simplifier refines → gitops commits

---

## Skills Model

Skills are reusable procedures and rules that agents reference.

| Type | Purpose | Example |
|------|---------|---------|
| `discipline` | Enforce behavioral rules | `scope-discipline` |
| `technique` | How-to procedures | `alto-configure` |
| `reference` | Lookup information | `alto-protocol` |

**Activation:** Agent prompts explicitly reference skills:
```markdown
## Skills
- Read `skills/alto-configure/SKILL.md` — configuration procedures
```

This is reference-based (not discovery-based) for:
- No discovery overhead per invocation
- Selective per agent
- Auditable in prompts

---

## Human Intervention Points

### Arbiter Checkpoints

The arbiter monitors thresholds and triggers human review:
- Token usage
- Lines/files changed
- Tasks completed
- Permission prompts

When thresholds are exceeded, orchestrator blocks and waits for human.

### Feature Completion

At completion, user chooses:
- Debug mode (test pre-merge)
- Next feature (merge and continue)
- Reconfigure (adjust settings)

---

## For AI Agents

See **AI-CONTEXT.md** for full session context including:
- State machine details
- Task and handoff formats
- Execution flow diagrams
- File locations

## For Operators

See **OPERATIONS.md** for:
- Commands reference
- Configuration options
- Directory structure
- Troubleshooting

## For ALTO Developers

See **DEVELOPMENT.md** for:
- Dev mode setup
- Testing workflows
- Adding agents, skills, hooks

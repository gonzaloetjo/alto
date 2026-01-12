# ALTO Architecture

> Autonomous Lifecycle Task Orchestrator for Claude Code

## Overview

ALTO is a multi-agent orchestration protocol for Claude Code that provides:
- **Session persistence** across Claude Code restarts
- **Human review gates** via the arbiter system
- **Structured handoffs** between tasks
- **Git-based audit trail** with run branches

---

## Agent & Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            ORCHESTRATOR                                  │
│                           (CLAUDE.md)                                    │
│                                                                          │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │PLANNING │──▶│BETWEEN_ │──▶│IN_TASK  │──▶│BETWEEN_ │──▶│BLOCKED  │     │
│  │         │   │TASKS    │   │         │   │TASKS    │   │(human)  │     │
│  └────┬────┘   └────┬────┘   └────┬────┘   └─────────┘   └─────────┘     │
│       │             │             │                                      │
│       ▼             ▼             ▼                                      │
│  ┌─────────┐   ┌─────────┐   ┌────────────────────────────────────┐      │
│  │ planner │   │ arbiter │   │          ROLE AGENTS               │      │
│  └─────────┘   └─────────┘   │  ┌─────────┐ ┌─────────┐ ┌──────┐  │      │
│                              │  │ backend │ │frontend │ │  qa  │  │      │
│                              │  └─────────┘ └─────────┘ └──────┘  │      │
│                              │  ┌─────────┐ ┌─────────┐ ┌──────┐  │      │
│                              │  │recorder │ │  docs   │ │gitops│  │      │
│                              │  └─────────┘ └─────────┘ └──────┘  │      │
│                              │  ┌──────────┐ ┌──────────┐         │      │
│                              │  │ reviewer │ │ enforcer │         │      │
│                              │  └──────────┘ └──────────┘         │      │
│                              └────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                          HOOKS (out-of-band)                             │
│                                                                          │
│  PreToolUse ─────────▶ tool-use-record.py ─────▶ runs/tools/usage.jsonl  │
│                                                                          │
│  Stop / SubagentStop┬▶ usage-record.py ───────▶ runs/usage/usage.jsonl   │
│                     └▶ arbiter-scheduler.py ──▶ runs/arbiter/pending.json│
│                                                                          │
│  PermissionRequest ──▶ permission-record.py ───▶ runs/permissions/*.jsonl│
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION LOOP                                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │                                                                │      │
│  ▼                                                                │      │
│  ┌──────────┐  pending?  ┌──────────┐  invoke  ┌──────────┐       │      │
│  │ arbiter  │───────────▶│  check   │─────────▶│ execute  │       │      │
│  │  check   │    no      │ decision │   role   │   task   │       │      │
│  └──────────┘            └────┬─────┘          └────┬─────┘       │      │
│                               │                     │             │      │
│                          needs_human?               │             │      │
│                          yes │ no                   │             │      │
│                              ▼                      ▼             │      │
│                        ┌─────────┐           ┌──────────┐         │      │
│                        │ BLOCKED │           │ handoff  │─────────┘      │
│                        │ (stop)  │           │ + post   │                │
│                        └─────────┘           └──────────┘                │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                          TASK LIFECYCLE                                  │
│                                                                          │
│  runs/tasks/task-XXX.md                                                  │
│         │                                                                │
│         ▼                                                                │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐       │
│  │ read task  │──▶│invoke role │──▶│ check_cmd  │──▶│   write    │       │
│  │ frontmatter│   │   agent    │   │ until pass │   │  handoff   │       │
│  └────────────┘   └────────────┘   └────────────┘   └─────┬──────┘       │
│                                                           │              │
│                                                           ▼              │
│                                                   runs/handoffs/         │
│                                                   task-XXX.md            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Claude Code Integration

ALTO is built on Claude Code features:
- **Memory file**: `CLAUDE.md` is automatically loaded as project memory at launch
- **Project subagents**: `.claude/agents/*.md` define tool access, system prompts, and separate contexts
- **Hierarchical settings**: `.claude/settings.json` defines project-wide permissions
- **Hooks**: `Stop` / `SubagentStop` hooks collect usage/telemetry without LLM tokens

References:
- Memory (`CLAUDE.md`): https://docs.anthropic.com/en/docs/claude-code/memory
- Subagents: https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Settings: https://docs.anthropic.com/en/docs/claude-code/settings
- Hooks: https://docs.anthropic.com/en/docs/claude-code/hooks

---

## Directory Structure

```
CLAUDE.md                    # Orchestrator protocol (auto-loaded)
ARCHITECTURE.md              # This file - AI agent architecture
objective.md                 # Project goals and requirements
docs/                        # Implementation docs (alto-docs writes here)

.claude/
├── settings.json            # Project-wide permissions + hooks
├── agents/
│   ├── alto-planner.md      # Generates plan + tasks
│   ├── alto-backend.md      # Backend implementation
│   ├── alto-frontend.md     # Frontend implementation
│   ├── alto-recorder.md     # Records task changes in handoffs
│   ├── alto-docs.md         # Implementation documentation for readers
│   ├── alto-gitops.md       # Branch/commit/push hygiene
│   ├── alto-qa.md           # Check/fix loop
│   ├── alto-reviewer.md     # Code quality gate (automatic)
│   ├── alto-enforcer.md     # Protocol compliance gate (automatic)
│   └── alto-arbiter.md      # Periodic checkpoint auditor
├── hooks/
│   ├── usage-record.py      # Token tracking (no LLM overhead)
│   ├── tool-use-record.py   # Tool invocation logging (PreToolUse)
│   ├── permission-record.py # Permission request logging
│   └── arbiter-scheduler.py # Triggers arbiter on thresholds
└── skills/
    └── alto-protocol/
        └── SKILL.md         # Protocol definition (task/state/handoff formats)

runs/
├── plan.md                  # Generated: architecture, task outline
├── state.json               # Generated: current task + phase + role
├── tasks/                   # Generated: task-XXX.md (YAML frontmatter + DoD)
├── handoffs/                # Generated: task-XXX.md (changes + verify + next)
├── review/                  # Generated: task-XXX-review.md, task-XXX-enforcer.md
├── usage/                   # Generated: usage.jsonl (token records)
├── tools/                   # Generated: usage.jsonl (tool invocation log)
├── permissions/             # Generated: requests.jsonl (permission prompts)
├── arbiter/                 # Arbiter checkpoint system
│   ├── config.json          # Thresholds (tokens, time, files, lines)
│   ├── state.json           # Last checkpoint metadata
│   ├── pending.json         # Snapshot triggering arbiter (transient)
│   ├── decision.json        # Arbiter output (needs_human, reasons)
│   └── checkpoints/         # Historical checkpoint reports
└── notes.md                 # Generated: blocking notes (if stuck)
```

---

## Orchestration Flow

The orchestrator is defined in `CLAUDE.md` (the "protocol controller").

```
1. Boot:
   * If no tasks/state exist → set phase = "PLANNING"
   * Invoke alto-planner to generate runs/plan.md + runs/tasks/* + runs/state.json
   * Set phase = "BETWEEN_TASKS"

2. Arbiter check (before each task):
   * If runs/arbiter/pending.json exists → invoke alto-arbiter
   * Read runs/arbiter/decision.json
   * If needs_human == true → set phase = "BLOCKED" and STOP

3. Execute:
   * Read runs/state.json → open current runs/tasks/task-XXX.md
   * Set phase = "IN_TASK", current_role = <role from task>
   * Invoke the task's role agent (backend/frontend/docs/qa/gitops)

4. Validate (inside the role agent):
   * Run task.check_command until it passes (fix failures and re-run)

5. Handoff:
   * Role agent writes runs/handoffs/task-XXX.md
   * If task specifies post agents → invoke them in order (e.g., docs → gitops)

6. Advance:
   * Mark task complete in runs/state.json
   * Set phase = "BETWEEN_TASKS", clear current_role
   * Proceed to next task (loop to step 2)
```

---

## State Phases

| Phase | Description |
|-------|-------------|
| `PLANNING` | Planner is generating/updating tasks |
| `IN_TASK` | A role agent is actively executing a task |
| `BETWEEN_TASKS` | Task completed; arbiter may trigger |
| `BLOCKED` | Human review required (arbiter decision or repeated failures) |

---

## Role Agents

| Agent | Primary responsibility | Typical constraints |
|-------|-------------------------|---------------------|
| `alto-planner` | Generate plan + task queue + state | edits **runs/** only; no Bash |
| `alto-backend` | API, DB schema, worker logic | obey `allowed_paths`; run checks |
| `alto-frontend` | Dashboard UI, charts, client state | obey `allowed_paths`; run checks |
| `alto-recorder` | Record task changes in handoffs | **runs/handoffs/** only |
| `alto-docs` | Write implementation docs for readers | **docs/** only |
| `alto-qa` | Run checks, diagnose failures, minimal fixes | smallest-diff fixes |
| `alto-gitops` | Branch/commit/push workflow | commit after checks pass |
| `alto-reviewer` | Code quality gate (auto after role) | read-only; can reject |
| `alto-enforcer` | Protocol compliance gate (auto after reviewer) | read-only; can reject |
| `alto-arbiter` | Periodic checkpoint auditor | edits **runs/arbiter/** only |

---

## Model Assignment

| Agent | Model | Rationale |
|-------|-------|-----------|
| `alto-arbiter` | **opus** | Critical judgment - decides if run should stop |
| `alto-planner` | **opus** | Architecture decisions, task decomposition |
| `alto-reviewer` | **opus** | Quality judgment - validates code and tests |
| `alto-backend` | sonnet | Complex implementation work |
| `alto-frontend` | sonnet | Complex implementation work |
| `alto-qa` | sonnet | Debugging and test fixes |
| `alto-docs` | sonnet | Quality documentation for readers |
| `alto-enforcer` | sonnet | Rule-based protocol checks |
| `alto-recorder` | haiku | Simple summarization |
| `alto-gitops` | haiku | Simple git commands |

---

## Task Format

Each task file is generated by the planner in `runs/tasks/task-XXX.md`:

```yaml
task_id: task-001
title: Short title
role: alto-backend
post: [alto-recorder, alto-gitops]
allowed_paths:
  - backend/**
check_command: make check
handoff: runs/handoffs/task-001.md
```

Task body includes:
* Goal
* Definition of Done (concrete, checkable)
* Any task-specific constraints

---

## Handoff Contract

After each task, the executing role agent must write a handoff containing:

* Summary of changes
* Files touched
* Interfaces/contracts changed (API endpoints, DB migrations, etc.)
* How to verify (commands + runtime steps)
* Next steps / risks

This enables deterministic context passing between role agents without relying on long chat history.

---

## Arbiter System

The arbiter is an independent "blackhat" auditor that operates between tasks to decide if human review is needed.

**Triggering:**
* `Stop` and `SubagentStop` hooks trigger `.claude/hooks/arbiter-scheduler.py`
* Scheduler checks if phase == "BETWEEN_TASKS" (never runs mid-task)
* If thresholds are exceeded, writes `runs/arbiter/pending.json`

**Checkpoints:**
* When `pending.json` exists, orchestrator invokes `alto-arbiter`
* Arbiter reviews: token burn, diff size, permission prompts, objective drift
* Writes checkpoint report to `runs/arbiter/checkpoints/<timestamp>.md`
* Writes `runs/arbiter/decision.json` with `needs_human` boolean

**Thresholds (configurable in `runs/arbiter/config.json`):**
```json
{
  "token_checkpoint_interval": 100000,
  "task_checkpoint_interval": 3,
  "max_files_changed_without_human": 50,
  "max_lines_changed_without_human": 2000,
  "high_risk_bash_prefixes": ["rm -rf /", "sudo rm", "dd if=", "mkfs"]
}
```

---

## Communication Model

All agent communication is **centralized through the orchestrator**:

1. **Agents write to files** — never to each other directly
   - Role agents → `runs/handoffs/task-{ID}.md`
   - Reviewer → `runs/review/task-{ID}-review.md`
   - Enforcer → `runs/review/task-{ID}-enforcer.md`
   - Post agents → `runs/handoffs/task-{ID}-{agent}.md`

2. **Orchestrator reads and passes context**
   - Reads outputs from previous step
   - Passes relevant context to next agent via prompt
   - Agents never read other agents' output directly

3. **Benefits**
   - Clear audit trail in `runs/`
   - No hidden agent-to-agent dependencies
   - Orchestrator controls information flow
   - Easy to debug handoff issues

---

## Permissions Model

* **Project-wide baseline** permissions live in `.claude/settings.json` (shared)
* **Per-agent differences** are controlled via each subagent file's YAML frontmatter:
  * `tools` (what the agent can do)
  * `permissionMode` (how aggressively it auto-approves)
  * `model` (optional)
* **Per-participant overrides** should go in `.claude/settings.local.json` (not committed)

Sensitive file reads (e.g. `.env`, private keys) are denied by default in project settings.

---

## Token Tracking

Token usage is captured **out-of-band** (no LLM overhead) via Claude Code hooks:

* `Stop` and `SubagentStop` trigger `.claude/hooks/usage-record.py`
* The hook records usage into `runs/usage/usage.jsonl`
* Records are tagged with the current `task_id` and role via `runs/state.json`

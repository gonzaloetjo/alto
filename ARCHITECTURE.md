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
│  ┌──────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐    │
│  │ARCHITECT │──▶│PLANNING │──▶│BETWEEN_ │──▶│IN_TASK  │──▶│BLOCKED  │    │
│  │(orch)    │   │         │   │TASKS    │   │         │   │(human)  │    │
│  └────┬─────┘   └────┬────┘   └────┬────┘   └────┬────┘   └─────────┘    │
│       │              │             │             │                       │
│       │              ▼             ▼             ▼                       │
│       │         ┌─────────┐   ┌─────────┐   ┌────────────────────────┐   │
│       │         │ planner │   │ arbiter │   │      ROLE AGENTS       │   │
│       │         └─────────┘   └─────────┘   │  ┌───────┐ ┌───────┐   │   │
│       │                                     │  │backend│ │frontend│  │   │
│       ▼                                     │  └───────┘ └───────┘   │   │
│  ┌──────────────────┐                       │  ┌───────┐ ┌───────┐   │   │
│  │ EnterPlanMode    │                       │  │  qa   │ │ docs  │   │   │
│  │ (if approval on) │                       │  └───────┘ └───────┘   │   │
│  │                  │                       │  ┌────────┐ ┌────────┐ │   │
│  │ Outputs:         │                       │  │recorder│ │ gitops │ │   │
│  │ - milestones.md  │                       │  └────────┘ └────────┘ │   │
│  │ - decisions.md   │                       │  ┌────────┐ ┌────────┐ │   │
│  └──────────────────┘                       │  │reviewer│ │enforcer│ │   │
│                                             │  └────────┘ └────────┘ │   │
│                                             └────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                          HOOKS (out-of-band)                             │
│                                                                          │
│  PostToolUse ────────▶ tool-record.py ────────▶ runs/tools/usage.jsonl   │
│                                                                          │
│  Stop / SubagentStop┬▶ usage-record.py ───────▶ runs/usage/usage.jsonl   │
│                     └▶ arbiter-scheduler.py ──▶ runs/arbiter/pending.json│
│                                                                          │
│  PermissionRequest ──▶ permission-record.py ───▶ runs/permissions/*.jsonl│
│                                                                          │
│  SessionStart ───────▶ session-start.py ──────▶ runs/sessions/starts.jsonl
│  SessionEnd ─────────▶ session-summary.py ────▶ (summary generation)     │
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
│         ┌─────────────────────────────────────────────────┘              │
│         │                                                                │
│         ▼                                                                │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐                        │
│  │  reviewer  │──▶│  enforcer  │──▶│post agents │                        │
│  │(code only) │   │(compliance)│   │(recorder,  │                        │
│  │ can reject │   │ can reject │   │ gitops...) │                        │
│  └────────────┘   └────────────┘   └─────┬──────┘                        │
│         │                                │                               │
│         │ REJECT                         ▼                               │
│         └──────────▶ back to      runs/handoffs/                         │
│                      role agent   task-XXX.md                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Devenv Scripts

ALTO provides shell scripts for common operations:

| Script | Purpose |
|--------|---------|
| `alto-setup` | First-time project initialization (creates objective.md) |
| `alto-status` | Show current phase, branch, completed tasks |
| `alto-new-run` | Create new run branch, reset state to ARCHITECTURE |
| `alto-clean` | Clean previous run artifacts (tasks, pending.json) |
| `alto-feature` | Quick guide for starting a new feature |

Usage:
```bash
devenv shell
alto-setup      # New project
alto-status     # Check state
alto-new-run    # Start new feature run
```

---

## Interactive Startup

When Claude Code starts, ALTO detects state and presents options:

**New project (no objective.md):**
- "Set up project" → Guide through objective.md creation
- "Explain ALTO" → Overview of how ALTO works

**Existing project (ready to start):**
- "Start building" → Begin architecture phase
- "New feature" → Run `/alto-feature-setup`
- "Show status" → Analyze project state

**In progress:** Resumes automatically from last state.

**Blocked:** Waits for human input, shows `runs/notes.md`.

---

## Claude Code Integration

ALTO is built on Claude Code features:
- **Memory file**: `CLAUDE.md` is automatically loaded as project memory at launch
- **Project subagents**: `agents/*.md` define tool access, system prompts, and separate contexts
- **Hierarchical settings**: `.claude/settings.json` defines project-wide permissions
- **Hooks**: `Stop` / `SubagentStop` / `PostToolUse` hooks collect usage/telemetry without LLM tokens

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

agents/
├── alto-planner.md          # Generates task files from milestones
├── alto-feature-finder.md   # Analyzes codebase, identifies next features
├── alto-backend.md          # Backend implementation
├── alto-frontend.md         # Frontend implementation
├── alto-docs.md             # Implementation documentation for readers
├── alto-gitops.md           # Branch/commit/push hygiene
├── alto-qa.md               # Check/fix loop
├── alto-reviewer.md         # Code quality gate (automatic)
├── alto-arbiter.md          # Periodic checkpoint auditor
├── alto-dev.md              # ALTO development helper (meta)
└── code-simplifier.md       # Code clarity refinement (post-agent)

hooks/
├── usage-record.py          # Token tracking (Stop/SubagentStop)
├── tool-record.py           # Tool invocation logging (PostToolUse)
├── permission-record.py     # Permission request logging (PermissionRequest)
├── arbiter-scheduler.py     # Triggers arbiter on thresholds (Stop/SubagentStop)
├── session-start.py         # Session initialization (SessionStart)
├── session-summary.py       # Session summary generation (SessionEnd)
└── handoff-validate.py      # Handoff validation (SubagentStop)

skills/
├── alto-protocol/
│   └── SKILL.md             # Protocol definition (task/state/handoff formats)
└── alto-feature-setup/
    └── SKILL.md             # Interactive feature setup guide (/alto-feature-setup)

.claude/
└── settings.json            # Project-wide permissions + hooks config

runs/
├── milestones.md            # Generated: high-level steps (orchestrator output)
├── decisions.md             # Generated: architectural trade-offs (orchestrator output)
├── planning-config.json     # Generated: planning configuration from devenv
├── plan.md                  # Generated: detailed batch plan (planner output)
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

### Boot (New Run)

```
1. Architecture Phase (orchestrator does this directly):
   * Set phase = "ARCHITECTURE"
   * Read runs/planning-config.json for require_approval setting
   * If require_approval is true:
     - Use EnterPlanMode tool
     - Explore codebase, read objective.md
     - Design high-level approach
     - Write runs/milestones.md (milestones, estimated task count)
     - Write runs/decisions.md (architectural choices)
     - Use ExitPlanMode tool (user approves)
   * If require_approval is false:
     - Explore and write milestones/decisions directly

2. Planning Phase:
   * Set phase = "PLANNING"
   * Invoke alto-planner with milestones.md as input
   * Planner creates runs/plan.md + runs/tasks/task-001..N.md
   * Set phase = "BETWEEN_TASKS"
```

### Execution Loop

```
3. Arbiter check (before each task):
   * If runs/arbiter/pending.json exists → invoke alto-arbiter
   * Read runs/arbiter/decision.json
   * If needs_human == true → set phase = "BLOCKED" and STOP

4. Replan check (after batch completion):
   * If replan_every is set and completed_tasks % replan_every == 0:
     - Set phase = "PLANNING"
     - Invoke alto-planner to create next batch
     - Continue to next task

5. Execute:
   * Read runs/state.json → open current runs/tasks/task-XXX.md
   * Set phase = "IN_TASK", current_role = <role from task>
   * Invoke the task's role agent (backend/frontend/docs/qa/gitops)

6. Validate (inside the role agent):
   * Run task.check_command until it passes (fix failures and re-run)

7. Handoff:
   * Role agent writes runs/handoffs/task-XXX.md
   * If task specifies post agents → invoke them in order (e.g., docs → gitops)

8. Update Progress:
   * If task completes an objective item → mark [x] in objective.md

9. Advance:
   * Mark task complete in runs/state.json
   * Set phase = "BETWEEN_TASKS", clear current_role
   * Proceed to next task (loop to step 3)
```

---

## State Phases

| Phase | Description |
|-------|-------------|
| `ARCHITECTURE` | Orchestrator exploring codebase, designing milestones |
| `PLANNING` | Planner is generating task files from milestones |
| `IN_TASK` | A role agent is actively executing a task |
| `BETWEEN_TASKS` | Task completed; arbiter may trigger; replan may occur |
| `BLOCKED` | Human review required (arbiter decision or repeated failures) |

---

## Role Agents

| Agent | Primary responsibility | Typical constraints |
|-------|-------------------------|---------------------|
| `alto-planner` | Create task files from milestones | edits **runs/** only; no Bash |
| `alto-feature-finder` | Analyze codebase, identify next features | read-only |
| `alto-backend` | API, DB schema, worker logic | obey `allowed_paths`; run checks |
| `alto-frontend` | Dashboard UI, charts, client state | obey `allowed_paths`; run checks |
| `alto-docs` | Write implementation docs for readers | **docs/** only |
| `alto-qa` | Run checks, diagnose failures, minimal fixes | smallest-diff fixes |
| `alto-gitops` | Branch/commit/push workflow | commit after checks pass |
| `alto-reviewer` | Code quality gate (auto after role) | read-only; can reject |
| `alto-arbiter` | Periodic checkpoint auditor | edits **runs/arbiter/** only |
| `alto-dev` | ALTO development helper (meta) | full access for ALTO repo work |
| `code-simplifier` | Refine code for clarity (post-agent) | edits files touched by role agent |

---

## Model Assignment

| Agent | Model | Rationale |
|-------|-------|-----------|
| `alto-arbiter` | **opus** | Critical judgment - decides if run should stop |
| `alto-planner` | **opus** (configurable) | Task decomposition from milestones |
| `alto-feature-finder` | **opus** | Codebase analysis and feature identification |
| `alto-reviewer` | **opus** | Quality judgment - validates code and tests |
| `alto-frontend` | **opus** | Complex UI implementation requiring design judgment |
| `code-simplifier` | **opus** | Code quality refinement requiring judgment |
| `alto-backend` | sonnet | Complex implementation work |
| `alto-qa` | sonnet | Debugging and test fixes |
| `alto-docs` | sonnet | Quality documentation for readers |
| `alto-gitops` | haiku | Simple git commands |

---

## Task Format

Each task file is generated by the planner in `runs/tasks/task-XXX.md`:

```yaml
task_id: task-001
title: Short title
role: alto-backend
post: [alto-gitops]
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
  "time_checkpoint_interval_minutes": 20,
  "task_checkpoint_interval": 3,
  "max_files_changed_without_human": 50,
  "max_lines_changed_without_human": 2000,
  "max_permission_prompts_between_checkpoints": 3,
  "high_risk_bash_prefixes": ["rm -rf /", "sudo rm", "dd if=", "mkfs", "> /dev/"]
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

# ALTO Architecture

> Autonomous Lifecycle Task Orchestrator for Claude Code

## Index

- [Overview](#overview)
- [Orchestrator Modes](#orchestrator-modes)
- [Agent & Flow Diagram (Build Mode)](#agent--flow-diagram-build-mode)
- [Devenv Scripts](#devenv-scripts)
- [Interactive Startup](#interactive-startup)
- [Claude Code Integration](#claude-code-integration)
- [Directory Structure](#directory-structure)
- [Orchestration Flow (Build Mode)](#orchestration-flow-build-mode)
- [State Phases (Build Mode)](#state-phases-build-mode)
- [Role Agents](#role-agents)
- [Skills](#skills)
- [Model Assignment](#model-assignment)
- [Task Format](#task-format)
- [Handoff Contract](#handoff-contract)
- [Arbiter System](#arbiter-system)
- [Configuration Timing](#configuration-timing)
- [Verification Hooks](#verification-hooks)
- [Hook Error Handling](#hook-error-handling)
- [Communication Model](#communication-model)
- [Permissions Model](#permissions-model)
- [Token Tracking](#token-tracking)
- [Branch Lifecycle](#branch-lifecycle)

---

## Overview

ALTO is a multi-agent orchestration protocol for Claude Code that provides:
- **Session persistence** across Claude Code restarts
- **Human review gates** via the arbiter system
- **Structured handoffs** between tasks
- **Git-based audit trail** with run branches

---

## Orchestrator Modes

ALTO uses two orchestrator modes, separated by human interaction level:

| Mode | Purpose | Agents | Shared Skills |
|------|---------|--------|---------------|
| **setup** | Human-interactive phase | `alto-feature-finder` | `alto-configure`, `alto-protocol` |
| **build** | Autonomous execution | All agents | `alto-configure`, `alto-protocol` |

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ALTO ORCHESTRATOR MODES                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   SETUP MODE                         BUILD MODE                      │
│   (Human-Interactive)                (Autonomous)                    │
│                                                                      │
│   • New project init                 • Architecture exploration      │
│   • Feature definition               • Task planning (planner)       │
│   • Configuration                    • Task execution (role agents)  │
│   • Cleanup between features         • Rolling replan                │
│   • Onboarding                       • Arbiter checkpoints           │
│                                                                      │
│         │                                   │                        │
│         │ "Start building"                  │ "Next feature"         │
│         └──────────────────►   ◄────────────┘                        │
│                                                                      │
│   Switch: alto.orchestrator = "build"/"setup" + alto-restart         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Setup Mode** handles:
- Writing `objective.md` interactively
- Configuring arbiter thresholds, permissions, verification
- Cleanup after feature completion
- Explaining ALTO to new users

**Build Mode** handles:
- Architecture phase (milestones, decisions)
- Planning phase (task generation)
- Execution loop (role agents, QA, gitops)
- Arbiter checkpoints with optional reconfiguration
- Feature completion (debug mode, next feature)

**Switching modes:** Edit `devenv.nix` to set `alto.orchestrator`, then run `alto-restart`.

---

## Agent & Flow Diagram (Build Mode)

The following diagram shows BUILD mode. Setup mode has only the `alto-feature-finder` agent, but both modes share the `alto-configure` and `alto-protocol` skills.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       BUILD ORCHESTRATOR                                 │
│                      (CLAUDE.md.build)                                   │
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
| `alto-status` | Show current phase, branch, completed tasks, orchestrator mode |
| `alto-switch` | Show how to switch between setup/build orchestrators |
| `alto-new-run` | Create new run branch, reset state to ARCHITECTURE |
| `alto-clean` | Clean previous run artifacts (tasks, pending.json) |
| `alto-feature` | Quick guide for starting a new feature |
| `alto-restart` | Restart Claude with fresh devenv config (applies config changes) |

Usage:
```bash
devenv shell
alto-setup      # New project
alto-status     # Check state (includes orchestrator mode)
alto-switch     # See how to switch orchestrators
alto-new-run    # Start new feature run
alto-restart    # Apply config changes (run from within Claude)
```

---

## Interactive Startup

Startup behavior depends on the orchestrator mode:

### Setup Mode (Human-Interactive)

**New project (no objective.md):**
- "Set up project" → Configure ALTO, then write objective.md
- "Configure ALTO" → Set thresholds, permissions
- "Explain ALTO" → Overview of two-mode model

**Has objective.md:**
- "Start building" → Switch to build mode
- "Edit objective" → Modify feature definition
- "Configure ALTO" → Adjust settings
- "Analyze codebase" → Run alto-feature-finder

### Build Mode (Autonomous)

**No objective.md:** Prompts to switch to setup mode.

**Has objective.md, no state:** Begins architecture phase automatically.

**In progress:** Resumes from last state (phase in `runs/state.json`).

**Blocked:** Waits for human input, shows `runs/notes.md`.

**Completed:** Offers debug mode, next feature, or reconfigure.

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
CLAUDE.md                    # Orchestrator protocol (copied from template based on mode)
ARCHITECTURE.md              # This file - AI agent architecture
objective.md                 # Project goals and requirements
docs/                        # Implementation docs (alto-docs writes here)

templates/
├── CLAUDE.md.setup          # Setup orchestrator protocol (human-interactive)
└── CLAUDE.md.build          # Build orchestrator protocol (autonomous)

agents/
├── alto-planner.md          # Generates task files from milestones (build only)
├── alto-feature-finder.md   # Analyzes codebase, identifies next features (both modes)
├── alto-backend.md          # Backend implementation (build only)
├── alto-frontend.md         # Frontend implementation (build only)
├── alto-docs.md             # Implementation documentation for readers (build only)
├── alto-gitops.md           # Branch/commit/push hygiene (build only)
├── alto-qa.md               # Tests + verification config updates (build only)
├── alto-reviewer.md         # Code quality gate (build only)
├── alto-arbiter.md          # Periodic checkpoint auditor (build only)
├── alto-dev.md              # ALTO development helper (meta)
└── code-simplifier.md       # Code clarity refinement (build only)

hooks/
├── usage-record.py          # Token tracking (Stop/SubagentStop) - shared
├── tool-record.py           # Tool invocation logging (PostToolUse) - shared
├── permission-record.py     # Permission request logging (PermissionRequest) - shared
├── session-start.py         # Session initialization (SessionStart) - shared
├── session-summary.py       # Session summary generation (SessionEnd) - shared
├── arbiter-scheduler.py     # Triggers arbiter on thresholds (build only)
├── handoff-validate.py      # Handoff validation (build only)
└── verify-dynamic.py        # Dynamic verification from JSON config (build only)

skills/
├── alto-protocol/
│   └── SKILL.md             # Protocol definition (task/state/handoff formats)
├── alto-feature-setup/
│   └── SKILL.md             # Interactive feature setup guide
├── alto-configure/
│   └── SKILL.md             # Shared configuration procedures (both modes)
└── scope-discipline/
    └── SKILL.md             # Prevent over-engineering discipline

.claude/
└── settings.json            # Project-wide permissions + hooks config

runs/
├── orchestrator.json        # Generated: current orchestrator mode
├── milestones.md            # Generated: high-level steps (build mode)
├── decisions.md             # Generated: architectural trade-offs (build mode)
├── planning-config.json     # Generated: planning configuration from devenv
├── verification-config.json # Generated: dynamic verification commands (QA updates)
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

## Orchestration Flow (Build Mode)

The build orchestrator is defined in `CLAUDE.md` (copied from `templates/CLAUDE.md.build`).

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
   * Run verification steps from task's "How to Verify" section

7. Handoff:
   * Role agent **edits** pre-created `runs/handoffs/task-XXX.md` (path from `state.json` → `current_handoff`)
   * Post-agents derive their path: `task-XXX.md` → `task-XXX-{agent}.md`
   * If task specifies post agents → invoke them in order (e.g., qa → simplifier → gitops)

8. Update Progress:
   * If task completes an objective item → mark [x] in objective.md

9. Advance:
   * Mark task complete in runs/state.json
   * Set phase = "BETWEEN_TASKS", clear current_role
   * Proceed to next task (loop to step 3)
```

---

## State Phases (Build Mode)

These phases apply only to BUILD mode. Setup mode doesn't use state phases.

| Phase | Description |
|-------|-------------|
| `ARCHITECTURE` | Orchestrator exploring codebase, designing milestones |
| `PLANNING` | Planner is generating task files from milestones |
| `IN_TASK` | A role agent is actively executing a task |
| `BETWEEN_TASKS` | Task completed; arbiter may trigger; replan may occur |
| `BLOCKED` | Human review required (arbiter decision or repeated failures) |
| `COMPLETED` | All tasks done, awaiting human decision (debug, next feature, or reconfigure) |
| `DEBUG` | Human testing and fixing issues before merge |

---

## Role Agents

| Agent | Mode | Primary responsibility | Typical constraints |
|-------|------|-------------------------|---------------------|
| `alto-planner` | build | Create task files from milestones | edits **runs/** only; no Bash |
| `alto-feature-finder` | both | Analyze codebase, identify next features | read-only |
| `alto-backend` | build | API, DB schema, worker logic | obey `allowed_paths`; run checks |
| `alto-frontend` | build | Dashboard UI, charts, client state | obey `allowed_paths`; run checks |
| `alto-docs` | build | Write implementation docs for readers | **docs/** only |
| `alto-qa` | build | Write tests, update verification-config | runs after role agents |
| `alto-gitops` | build | Branch/commit/push workflow | commit after checks pass |
| `alto-reviewer` | build | Code quality gate (auto after role) | read-only; can reject |
| `alto-arbiter` | build | Periodic checkpoint auditor | edits **runs/arbiter/** only |
| `alto-dev` | (meta) | ALTO development helper | full access for ALTO repo work |
| `code-simplifier` | build | Refine code for clarity (post-agent) | edits files touched by role agent |

---

## Skills

Skills are reusable procedures and rules that agents and orchestrators reference. Three types:

| Type | Purpose | Required Sections |
|------|---------|-------------------|
| `discipline` | Enforce behavioral rules | Hard Rule, Warning Signs |
| `technique` | How-to procedures | Process/steps |
| `reference` | Lookup information | Quick reference table |

### Current Skills

| Skill | Type | Purpose | Used By |
|-------|------|---------|---------|
| `alto-protocol` | reference | Task/state/handoff formats | All agents |
| `alto-feature-setup` | technique | Interactive feature setup | Setup orchestrator |
| `alto-configure` | technique | Configuration procedures (thresholds, permissions, verification) | Both orchestrators |
| `scope-discipline` | discipline | Prevent over-engineering | Implementation agents |

### Activation (Reference-Based)

Agent prompts and orchestrators explicitly reference skills:

```markdown
## Skills
- Read `skills/alto-configure/SKILL.md` — configuration procedures
- Read `skills/scope-discipline/SKILL.md` — only do what task asks
```

Reference-based activation (vs discovery-based):
- No discovery overhead per invocation
- Selective per agent (not all need all skills)
- Explicit in prompt (auditable)

### Discipline Skills

Discipline skills enforce behavioral rules. Structure:

```markdown
---
name: scope-discipline
type: discipline
triggers:
  - implementing features
---

## Hard Rule
[One-line non-negotiable]

## Warning Signs
If you catch yourself thinking:
- "[rationalization 1]"

STOP. [What to do instead].
```

### Adding Skills

1. Create `skills/<name>/SKILL.md` with frontmatter (name, type, triggers)
2. Include required sections for the type
3. Stay within word limit (discipline: 300, technique: 500, reference: 800)
4. Add reference to relevant agent prompts or orchestrator templates

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
post: [alto-qa, code-simplifier, alto-gitops]
allowed_paths:
  - backend/**
handoff: runs/handoffs/task-001.md
```

**Post agent flow:** Role implements → QA writes tests → code-simplifier refines → gitops commits

Task body includes:
* Goal
* Definition of Done (concrete, checkable)
* How to Verify (tests, commands, manual checks)
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

## Configuration Timing

Some settings can be changed mid-session, others require a shell restart (feature boundary).

| Config | When Applied | Location |
|--------|--------------|----------|
| Arbiter thresholds | **Dynamic** | `runs/arbiter/config.json` |
| Verification commands | **Dynamic** | `runs/verification-config.json` |
| Planning settings | **Dynamic** | `runs/planning-config.json` |
| Orchestrator mode | Feature boundary | `devenv.nix` → `alto.orchestrator` |
| Permissions (allow/deny) | Feature boundary | `devenv.nix` → `.claude/settings.json` |
| Agent tools | Feature boundary | `devenv.nix` → agent files |
| Hook definitions | Feature boundary | `devenv.nix` → `.claude/settings.json` |
| Permission profile | Feature boundary | `devenv.nix` |

**Dynamic:** Edit JSON file, takes effect on next hook invocation. Orchestrator writes these automatically via `alto-configure` skill.

**Feature boundary:** Edit `devenv.nix`, then either:
- Run `alto-restart` from within Claude (kills Claude, reloads devenv, restarts with `--continue`)
- Manually exit Claude and run `devenv shell` + `claude`

**Recommended flow:**
1. Start in setup mode, configure ALTO, write objective.md
2. Switch to build mode for autonomous execution
3. At arbiter checkpoints, optionally reconfigure thresholds/verification
4. At feature completion, switch back to setup for next feature

---

## Verification Hooks

Automated quality checks that run after file edits via `PostToolUse` hooks. Configured in `devenv.nix`:

```nix
alto.verification = {
  # Built-in hooks
  typecheck = {
    enable = true;
    command = "pnpm type:check";
    matcher = "Edit:*.ts|Edit:*.tsx|Write:*.ts|Write:*.tsx";
  };
  lint = {
    enable = true;
    command = "pnpm lint";
    matcher = "Edit:*.ts|Edit:*.tsx|Edit:*.js|Edit:*.jsx|...";
  };
  test = {
    enable = true;
    command = "npm test -- --related";
    matcher = "Edit:*.test.*|Edit:*.spec.*|...";
  };

  # Custom hooks
  custom = [
    { name = "security"; command = "./scripts/security.sh"; matcher = "Edit:src/auth/*"; }
    { name = "format"; command = "prettier --write"; matcher = "Write:*.json"; timeout = 10000; }
  ];
};
```

**How it works:**
1. User enables verification options in `devenv.nix`
2. ALTO generates `PostToolUse` hooks in `.claude/settings.json`
3. Hooks run automatically after Claude edits matching files
4. Failures block further edits until fixed

**Built-in vs Custom:**

| Type | Options | Use Case |
|------|---------|----------|
| `typecheck` | `enable`, `command`, `matcher` | TypeScript/Flow type checking |
| `lint` | `enable`, `command`, `matcher` | ESLint, Biome, Ruff, etc. |
| `test` | `enable`, `command`, `matcher` | Run related tests on change |
| `custom` | `name`, `command`, `matcher`, `timeout` | Security checks, formatters, etc. |

**Replaces `check_command`:** Tasks no longer specify a single check command. Instead:
- Automated checks run via hooks (deterministic, always runs)
- Task body has "How to Verify" section for acceptance criteria (conceptual)

### Dynamic Verification

For verification that can be configured mid-session without shell restart, use `runs/verification-config.json`:

```json
{
  "*.ts": {
    "typecheck": { "enable": true, "command": "pnpm type:check" }
  },
  "*.py": {
    "lint": "ruff check {file}",
    "test": { "enable": true, "command": "pytest" }
  },
  "src/api/**/*.ts": {
    "openapi": "./scripts/validate-openapi.sh"
  }
}
```

**Format:**
- Keys are glob patterns (`*.ts`, `src/**/*.py`)
- Values are objects mapping check names to commands
- Commands can be strings or `{ enable, command }` objects
- Use `{file}` placeholder for the edited file path

**When to use:**
| Approach | Use Case |
|----------|----------|
| Static (devenv.nix) | Known at project setup, rarely changes |
| Dynamic (JSON) | Discovered after first feature, tuned per-project |

The dynamic hook runs on all Edit/Write and checks the config file each time.

---

## Hook Error Handling

All hooks use `hook_utils.py` for consistent error handling:

```python
from hook_utils import safe_hook

@safe_hook("my-hook")
def main():
    # Hook logic - errors are caught and logged
    pass
```

**Behavior:**
- Errors logged to `runs/errors.jsonl` (not silent failures)
- Hook fails gracefully (returns exit 0, doesn't crash Claude Code)
- User-friendly message to stderr

**Health Check:**
`session-start` runs health checks on startup:
- Detects missing `objective.md` or unfilled template
- Reports recent errors in `runs/errors.jsonl`
- Validates state.json structure

**Error Log Format:**
```jsonl
{"timestamp":"2026-01-13T10:00:00","hook":"tool-record","error_type":"KeyError","error_message":"missing key","traceback":"..."}
```

---

## Communication Model

All agent communication is **centralized through the orchestrator**:

1. **Agents write to files** — never to each other directly
   - Role agents → `runs/handoffs/task-{ID}.md`
   - Reviewer → `runs/review/task-{ID}-review.md`
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

---

## Branch Lifecycle

ALTO creates `run/XXX` branches for each feature run. These accumulate and need periodic cleanup.

### Branch Strategy

| Branch | Purpose | Merge |
|--------|---------|-------|
| `main` | Stable code | Human decision |
| `run/001` | Feature run | Squash merge when complete |
| `run/002` | Next feature | Same |

### Cleanup (Human Task)

Branch cleanup is a **human decision**, not automated:
- **Merge** — human decides when a run is ready for main (squash merge recommended)
- **Delete** — after merging, human deletes the run branch
- **Abandon** — human can force-delete incomplete runs

### Feature Completion Transition

When all tasks complete, orchestrator sets `phase = "COMPLETED"` and uses `AskUserQuestion` to offer:

1. **Debug mode** — test and fix issues before merging
2. **Next feature** — merge and move on
3. **Reconfigure** — adjust ALTO settings (thresholds, verification, permissions)

#### Debug Mode (`phase = "DEBUG"`)
- Stay on run branch
- Human tests site/app/feature
- Fix issues directly (native Claude, no task files — fast iteration)
- When done → write debug summary to `runs/notes.md`, then ask same options again

#### Reconfigure
- Follow `alto-configure` skill procedures
- Adjust thresholds, verification commands, or permissions
- For permissions: edit `devenv.nix` then `alto-restart`
- Return to completion options after

#### Next Feature Mode
1. Check merge status (prompt human to merge if needed, wait for confirmation)
2. Run `alto-clean` (removes tasks, milestones, decisions; **keeps handoffs** for context)
3. Run `git checkout main && git pull`
4. Tell user: Switch to setup mode (`alto.orchestrator = "setup"` + `alto-restart`)
5. Setup mode guides through new feature definition

**Before transitioning**, capture follow-ups in `runs/notes.md`:
- New features identified during implementation
- Technical debt created

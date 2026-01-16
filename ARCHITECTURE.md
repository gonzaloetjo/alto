# ALTO Architecture

> Autonomous Lifecycle Task Orchestrator for Claude Code

## Index

- [Overview](#overview)
- [Orchestrator Modes](#orchestrator-modes)
- [Agent & Flow Diagram (Build Mode)](#agent--flow-diagram-build-mode)
- [Devenv Scripts](#devenv-scripts)
- [Claude Code Integration](#claude-code-integration)
- [Directory Structure](#directory-structure)
- [Orchestration Flow (Build Mode)](#orchestration-flow-build-mode)
- [State Phases (Build Mode)](#state-phases-build-mode)
- [Agents](#agents)
- [Skills](#skills)
- [Task Format](#task-format)
- [Handoff Contract](#handoff-contract)
- [Human Intervention](#human-intervention)
- [Configuration](#configuration)
- [Hook Error Handling](#hook-error-handling)
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

ALTO uses three orchestrator modes:

| Mode | Purpose | Agents | Skills |
|------|---------|--------|--------|
| **setup** | Human-interactive phase | `alto-feature-finder` | `alto-configure`, `alto-protocol`, `alto-feature-setup`, `scope-discipline` |
| **build** | Autonomous execution | All agents | `alto-configure`, `alto-protocol`, `alto-feature-setup`, `scope-discipline` |
| **dev** | ALTO development | `alto-dev` | `alto-dev-guide`, `writing-alto-skills` |

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
│   Switch: alto.orchestrator = "setup"/"build"/"dev" + alto-restart           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Setup Mode (Human-Interactive)

Handles:
- Writing `objective.md` interactively
- Configuring arbiter thresholds, permissions, verification
- Cleanup after feature completion
- Explaining ALTO to new users

**Startup behavior:**
- New project (no objective.md): Offers "Set up project", "Configure ALTO", "Explain ALTO"
- Has objective.md: Offers "Start building", "Edit objective", "Configure ALTO", "Analyze codebase"

### Build Mode (Autonomous)

Handles:
- Architecture phase (milestones, decisions)
- Planning phase (task generation)
- Execution loop (role agents, QA, gitops)
- Arbiter checkpoints with optional reconfiguration
- Feature completion (debug mode, next feature)

**Startup behavior:**
- No objective.md: Prompts to switch to setup mode
- Has objective.md, no state: Begins architecture phase automatically
- In progress: Resumes from last state (`runs/state.json`)
- Blocked: Waits for human input, shows `runs/notes.md`
- Completed: Offers debug mode, next feature, or reconfigure

### Dev Mode (Meta)

For developing ALTO itself. Provides:
- Single `alto-dev` agent with full access
- `alto-dev-guide` skill with documentation URLs and patterns
- `writing-alto-skills` skill for skill authoring
- Minimal hooks (just `changelog-check`)

To switch to dev mode: edit `default = "dev"` in devenv.nix, run `alto-restart`.

### Switching Modes

**Option 1: Shell-based (requires restart)**
Edit `devenv.nix` to set `alto.orchestrator`, then run `alto-restart`.

**Option 2: ALTO CLI (instant switch)**
Use the `alto` command with `/switch`:

```bash
alto              # Start ALTO CLI in current mode
```

Inside the ALTO CLI:
```
/switch build     # Instant switch to build mode
/switch setup     # Instant switch to setup mode
/switch dev       # Instant switch to dev mode
/status           # Show current mode and session
/clear            # Clear current session
/exit             # Exit ALTO CLI
```

The ALTO CLI maintains separate sessions per mode, enabling instant context switching.

### ALTO CLI Architecture

The `alto` command is a TypeScript wrapper using the Claude Agent SDK:

```
alto-cli/
├── src/
│   ├── index.ts          # CLI entry (commander)
│   ├── alto.ts           # Main orchestration class
│   ├── config/
│   │   ├── agents.ts     # Parse agent .md → AgentDefinition
│   │   ├── hooks.ts      # Spawn Python hooks via child_process
│   │   └── loader.ts     # Load mode config from runs/
│   ├── session/
│   │   └── manager.ts    # Per-mode session persistence
│   └── repl/
│       ├── input.ts      # AsyncIterable<SDKUserMessage>
│       └── output.ts     # Message formatting
└── bin/
    └── alto              # Shebang entry
```

**Key Features:**
- **Runtime filtering**: Agents/hooks filtered by mode at runtime (not build-time)
- **Session persistence**: Each mode has its own session in `runs/sessions/{mode}.json`
- **Python hook spawning**: Existing hooks run via `child_process.spawn`
- **SDK integration**: Uses `@anthropic-ai/claude-agent-sdk` for query streaming

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
| `alto-update` | Force update ALTO to latest version (fixes Nix cache issues) |
| `alto-switch` | Switch orchestrator mode (edits devenv.nix) |
| `alto-setup` | First-time project initialization (creates objective.md) |
| `alto-status` | Show current phase, branch, completed tasks, orchestrator mode |
| `alto-new-run` | Create new run branch, reset state to ARCHITECTURE |
| `alto-clean` | Clean previous run artifacts (tasks, pending.json) |
| `alto-feature` | Quick guide for starting a new feature |

Usage:
```bash
direnv allow        # Activate environment (keeps native shell)
claude              # Start Claude
alto-update         # Update ALTO to latest version
alto-switch dev     # Switch to dev mode (then /exit and restart claude)
alto-status         # Check state (includes orchestrator mode)
```

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
├── CLAUDE.md.build          # Build orchestrator protocol (autonomous)
└── CLAUDE.md.dev            # Dev orchestrator protocol (ALTO development)

agents/                      # See Agents section for details
├── alto-planner.md
├── alto-feature-finder.md
├── alto-backend.md
├── alto-frontend.md
├── alto-docs.md
├── alto-gitops.md
├── alto-qa.md
├── alto-reviewer.md
├── alto-arbiter.md
├── alto-dev.md
└── code-simplifier.md

hooks/
├── usage-record.py          # Token tracking (Stop/SubagentStop) - shared
├── tool-record.py           # Tool invocation logging (PostToolUse) - shared
├── permission-record.py     # Permission request logging (PermissionRequest) - shared
├── changelog-check.py       # Blocks commit without CHANGELOG (PreToolUse) - shared
├── session-start.py         # Session initialization (SessionStart) - shared
├── session-summary.py       # Session summary generation (SessionEnd) - shared
├── arbiter-scheduler.py     # Triggers arbiter on thresholds (build only)
├── handoff-validate.py      # Handoff validation (build only)
└── verify-dynamic.py        # Dynamic verification from JSON config (build only)

skills/
├── alto-protocol/           # Protocol definition (task/state/handoff formats)
├── alto-feature-setup/      # Interactive feature setup guide
├── alto-configure/          # Shared configuration procedures (setup/build)
├── scope-discipline/        # Prevent over-engineering discipline
├── alto-dev-guide/          # Dev mode: documentation URLs and patterns
└── writing-alto-skills/     # Dev mode: skill authoring methodology

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

## Agents

| Agent | Mode | Model | Purpose | Constraints |
|-------|------|-------|---------|-------------|
| `alto-planner` | build | opus | Create task files from milestones | runs/ only, no Bash |
| `alto-feature-finder` | both | opus | Analyze codebase, identify features | read-only |
| `alto-backend` | build | sonnet | API, DB schema, worker logic | allowed_paths |
| `alto-frontend` | build | opus | Dashboard UI, charts, client state | allowed_paths |
| `alto-qa` | build | sonnet | Write tests, update verification-config | runs after role agents |
| `alto-docs` | build | sonnet | Implementation documentation | docs/ only |
| `alto-gitops` | build | haiku | Branch/commit/push workflow | after checks pass |
| `alto-reviewer` | build | opus | Code quality gate | read-only, can reject |
| `alto-arbiter` | build | opus | Periodic checkpoint auditor | arbiter/ only |
| `code-simplifier` | build | opus | Refine code for clarity | touched files only |
| `alto-dev` | (meta) | - | ALTO development helper | full access |

**Post-agent flow:** Role implements → QA writes tests → code-simplifier refines → gitops commits

**Communication:** All agents write to files (`runs/handoffs/`), never to each other directly. Orchestrator reads outputs and passes context to next agent.

---

## Skills

Skills are reusable procedures and rules that agents and orchestrators reference. Three types:

| Type | Purpose | Required Sections |
|------|---------|-------------------|
| `discipline` | Enforce behavioral rules | Hard Rule, Warning Signs |
| `technique` | How-to procedures | Process/steps |
| `reference` | Lookup information | Quick reference table |

### Current Skills

| Skill | Type | Purpose | Mode |
|-------|------|---------|------|
| `alto-protocol` | reference | Task/state/handoff formats | setup, build |
| `alto-feature-setup` | technique | Interactive feature setup | setup, build |
| `alto-configure` | technique | Configuration procedures (thresholds, permissions, verification) | setup, build |
| `alto-switch` | technique | Switch orchestrator modes (setup/build/dev) | all |
| `scope-discipline` | discipline | Prevent over-engineering | setup, build |
| `alto-dev-guide` | reference | Documentation URLs and patterns for ALTO development | dev |
| `writing-alto-skills` | technique | Skill authoring methodology | dev |

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

## Human Intervention

ALTO has two human intervention points: arbiter checkpoints (mid-build) and feature completion.

### Arbiter Checkpoints

The arbiter is an independent auditor that operates between tasks to decide if human review is needed.

**Triggering:**
* `Stop` and `SubagentStop` hooks trigger `arbiter-scheduler.py`
* Scheduler checks if phase == "BETWEEN_TASKS" (never runs mid-task)
* If thresholds exceeded, writes `runs/arbiter/pending.json`

**Checkpoints:**
* Orchestrator invokes `alto-arbiter` when `pending.json` exists
* Arbiter reviews: token burn, diff size, permission prompts, objective drift
* Writes checkpoint report to `runs/arbiter/checkpoints/<timestamp>.md`
* Writes `runs/arbiter/decision.json` with `needs_human` boolean
* At checkpoint, user can optionally reconfigure (via `alto-configure` skill)

**Thresholds (`runs/arbiter/config.json`):**
```json
{
  "token_checkpoint_interval": 100000,
  "task_checkpoint_interval": 3,
  "max_files_changed_without_human": 50,
  "max_lines_changed_without_human": 2000
}
```

### Feature Completion

When all tasks complete, orchestrator sets `phase = "COMPLETED"` and offers:

1. **Debug mode** — test and fix issues before merging
2. **Next feature** — merge and move on
3. **Reconfigure** — adjust ALTO settings

**Debug Mode (`phase = "DEBUG"`):**
- Stay on run branch, human tests feature
- Fix issues directly (no task files — fast iteration)
- Write debug summary to `runs/notes.md` when done

**Next Feature:**
1. Prompt human to merge (squash recommended)
2. Run `alto-clean` (keeps handoffs for context)
3. Switch to setup mode for new feature definition

---

## Configuration

### When Settings Apply

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

**Feature boundary:** Edit `devenv.nix`, then run `alto-restart` (or exit Claude and run `devenv shell` + `claude`).

### Static Verification (devenv.nix)

Automated quality checks via `PostToolUse` hooks:

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

### Dynamic Verification (runs/verification-config.json)

For verification configured mid-session without shell restart:

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

**Static vs Dynamic:** Use static (devenv.nix) for known-at-setup checks; use dynamic (JSON) for checks discovered during build that need tuning.

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

ALTO creates `run/XXX` branches for each feature run.

| Branch | Purpose | Merge |
|--------|---------|-------|
| `main` | Stable code | Human decision |
| `run/001` | Feature run | Squash merge when complete |
| `run/002` | Next feature | Same |

**Cleanup (human task):**
- **Merge** — human decides when ready for main (squash recommended)
- **Delete** — after merging, delete the run branch
- **Abandon** — force-delete incomplete runs

See [Feature Completion](#feature-completion) for the transition flow.

  ┌─────────────────────────────────────────────────────────────────┐
  │ Terminal                                                        │
  ├─────────────────────────────────────────────────────────────────┤
  │ $ devenv shell                                                  │
  │ ALTO deployed                                                   │
  │                                                                 │
  │ $ alto                                                          │
  │ ╭─ ALTO ─────────────────────────────────────────────────────╮  │
  │ │ Mode: setup | Session: abc123                              │  │
  │ ╰────────────────────────────────────────────────────────────╯  │
  │                                                                 │
  │ > Help me write objective.md for a todo app                     │
  │                                                                 │
  │ I'll help you define your feature. Let me ask some questions... │
  │ [uses alto-feature-finder agent]                                │
  │                                                                 │
  │ > /switch build                                                 │
  │                                                                 │
  │ ╭─ Switching ────────────────────────────────────────────────╮  │
  │ │ ✓ Saved setup session (abc123)                             │  │
  │ │ ✓ Loading build mode                                       │  │
  │ │ ✓ Resumed build session (def456)                           │  │
  │ ╰────────────────────────────────────────────────────────────╯  │
  │                                                                 │
  │ ╭─ ALTO ─────────────────────────────────────────────────────╮  │
  │ │ Mode: build | Session: def456                              │  │
  │ ╰────────────────────────────────────────────────────────────╯  │
  │                                                                 │
  │ > Start building                                                │
  │                                                                 │
  │ Resuming from ARCHITECTURE phase. Let me review objective.md... │
  │ [has access to alto-planner, alto-backend, etc.]                │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘

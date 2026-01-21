# ALTO AI Context

> **This file is for AI agents.** Read once per session for orientation.

ALTO (Autonomous Lifecycle Task Orchestrator) coordinates multi-agent execution with human review gates. This document provides all context needed to understand and operate within ALTO.

---

## Protocol Overview

ALTO manages software development through:
- **Three orchestrator modes**: setup (human-interactive), build (autonomous), dev (meta)
- **State machine**: Tracks phases from architecture through completion
- **Agents**: Specialized subagents for planning, implementation, review, and operations
- **Skills**: Reusable procedures and rules referenced by agents
- **Hooks**: Out-of-band automation (tracking, validation, triggers)

---

## Current Mode Detection

Read `runs/orchestrator.json` to detect current mode:

```json
{ "orchestrator": "setup" | "build" | "dev" }
```

| Mode | Context File | Agents Available |
|------|--------------|------------------|
| `setup` | `CLAUDE.md` (from `templates/CLAUDE.md.setup`) | `alto-feature-finder` |
| `build` | `CLAUDE.md` (from `templates/CLAUDE.md.build`) | All agents |
| `dev` | `CLAUDE.md` (from `templates/CLAUDE.md.dev`) | `alto-dev` |

---

## State Machine (Build Mode)

Read `runs/state.json` for current state:

```json
{
  "phase": "BETWEEN_TASKS",
  "current_task": "task-003",
  "current_role": null,
  "current_handoff": null,
  "completed_tasks": ["task-001", "task-002"]
}
```

### Phases

| Phase | Description | Orchestrator Action |
|-------|-------------|---------------------|
| `ARCHITECTURE` | Exploring codebase, designing milestones | Write `milestones.md`, `decisions.md`, transition to PLANNING |
| `PLANNING` | Planner generating task files | Invoke `alto-planner`, transition to BETWEEN_TASKS |
| `IN_TASK` | Role agent executing task | Wait for completion, run post-agents |
| `BETWEEN_TASKS` | Task completed | Check arbiter, check replan, execute next task |
| `BLOCKED` | Human review required | STOP and wait for human |
| `COMPLETED` | All tasks done | Offer debug mode, next feature, or reconfigure |
| `DEBUG` | Human testing pre-merge | Free-form fixes, write notes when done |

### Phase Transitions

```
ARCHITECTURE → PLANNING → BETWEEN_TASKS ⟷ IN_TASK
                                ↓
                            BLOCKED (arbiter decision)
                                ↓
                            COMPLETED → DEBUG (optional)
```

---

## Agent Coordination

### Build Mode Diagram

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
```

### Hooks (Out-of-Band)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          HOOKS (out-of-band)                             │
│                                                                          │
│  PostToolUse ───────┬▶ tool-record.py ────────▶ runs/tools/usage.jsonl   │
│                     ├▶ handoff-template.py ───▶ runs/handoffs/*.md       │
│                     ├▶ task-validate.py ──────▶ (validates task files)   │
│                     └▶ phase-validate.py ─────▶ (validates transitions)  │
│                                                                          │
│  Stop / SubagentStop┬▶ usage-record.py ───────▶ runs/usage/usage.jsonl   │
│                     └▶ arbiter-scheduler.py ──▶ runs/arbiter/pending.json│
│                                                                          │
│  SubagentStop ──────┬▶ handoff-validate.py ───▶ (validates handoffs)     │
│                     └▶ review-validate.py ────▶ (validates reviews)      │
│                                                                          │
│  PermissionRequest ──▶ permission-record.py ───▶ runs/permissions/*.jsonl│
│                                                                          │
│  SessionStart ───────▶ session-start.py ──────▶ runs/sessions/starts.jsonl
│  SessionEnd ─────────▶ session-summary.py ────▶ (summary generation)     │
└──────────────────────────────────────────────────────────────────────────┘
```

### Execution Loop

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
▼                                                                │
┌──────────┐  pending?  ┌──────────┐  invoke  ┌──────────┐       │
│ arbiter  │───────────▶│  check   │─────────▶│ execute  │       │
│  check   │    no      │ decision │   role   │   task   │       │
└──────────┘            └────┬─────┘          └────┬─────┘       │
                             │                     │             │
                        needs_human?               │             │
                        yes │ no                   │             │
                            ▼                      ▼             │
                      ┌─────────┐           ┌──────────┐         │
                      │ BLOCKED │           │ handoff  │─────────┘
                      │ (stop)  │           │ + post   │
                      └─────────┘           └──────────┘
```

### Task Lifecycle

```
runs/tasks/task-XXX.md
       │
       ▼
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│ read task  │──▶│invoke role │──▶│ check_cmd  │──▶│   write    │
│ frontmatter│   │   agent    │   │ until pass │   │  handoff   │
└────────────┘   └────────────┘   └────────────┘   └─────┬──────┘
                                                         │
       ┌─────────────────────────────────────────────────┘
       │
       ▼
┌────────────┐   ┌────────────┐   ┌────────────┐
│  reviewer  │──▶│  enforcer  │──▶│post agents │
│(code only) │   │(compliance)│   │(recorder,  │
│ can reject │   │ can reject │   │ gitops...) │
└────────────┘   └────────────┘   └─────┬──────┘
       │                                │
       │ REJECT                         ▼
       └──────────▶ back to      runs/handoffs/
                    role agent   task-XXX.md
```

---

## Task Format

Each task file in `runs/tasks/task-XXX.md` has YAML frontmatter:

```yaml
---
task_id: task-001
title: Short title
role: alto-backend
post: [alto-qa, code-simplifier, alto-gitops]
allowed_paths:
  - backend/**
handoff: runs/handoffs/task-001.md
---
```

**Required body sections:**
- Goal
- Definition of Done (concrete, checkable items)
- How to Verify (tests, commands, manual checks)
- Any task-specific constraints

---

## Handoff Contract

Role agents must **edit** the pre-created handoff template (auto-created by `handoff-template` hook when `current_handoff` is set in state.json).

**Required sections** (validated by `handoff-validate` hook):

```markdown
## Summary
Brief description of what was accomplished (2-4 sentences).

## Files Touched
- path/to/file1.py - Added X function
- path/to/file2.ts - Fixed Y bug

## How to Verify
- Run `npm test` to verify tests pass
- Run `python script.py` to check output
```

**Post-agent path derivation:**
- `current_handoff`: `runs/handoffs/task-001.md`
- QA handoff: `runs/handoffs/task-001-qa.md`
- Gitops handoff: `runs/handoffs/task-001-gitops.md`

See `skills/handoff-writing/SKILL.md` for full format reference.

---

## File Locations

### Key Runtime Files

| File | Purpose | Read By |
|------|---------|---------|
| `runs/state.json` | Current phase, task, role | Orchestrator, all agents |
| `runs/orchestrator.json` | Current mode | Orchestrator |
| `runs/milestones.md` | High-level steps | Planner |
| `runs/decisions.md` | Architectural choices | All agents |
| `runs/plan.md` | Detailed batch plan | Orchestrator |
| `runs/tasks/task-XXX.md` | Task definitions | Role agents |
| `runs/handoffs/task-XXX.md` | Task outputs | Post-agents, orchestrator |
| `runs/arbiter/pending.json` | Arbiter trigger | Orchestrator |
| `runs/arbiter/decision.json` | Arbiter output | Orchestrator |
| `runs/notes.md` | Blocking notes | Human |

### Configuration Files

| File | Purpose | When Applied |
|------|---------|--------------|
| `alto.json` | Arbiter, planning, verification config | Dynamic (immediate) |
| `devenv.nix` | Orchestrator mode, permissions, agents | Feature boundary (reload) |
| `.claude/settings.json` | Hooks, project permissions | Feature boundary |

### Agent and Skill Files

| Directory | Purpose |
|-----------|---------|
| `agents/*.md` | Agent definitions (tools, prompts, permissions) |
| `skills/*/SKILL.md` | Skill definitions (procedures, rules) |
| `hooks/*.py` | Hook implementations |
| `templates/CLAUDE.md.*` | Orchestrator templates per mode |

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
| `alto-dev` | dev | - | ALTO development helper | full access |

**Post-agent flow:** Role implements → QA writes tests → code-simplifier refines → gitops commits

**Communication:** All agents write to files (`runs/handoffs/`), never to each other directly. Orchestrator reads outputs and passes context to next agent.

---

## Skills Reference

Skills are reusable procedures and rules. Three types:

| Type | Purpose | Required Sections |
|------|---------|-------------------|
| `discipline` | Enforce behavioral rules | Hard Rule, Warning Signs |
| `technique` | How-to procedures | Process/steps |
| `reference` | Lookup information | Quick reference table |

### Available Skills

| Skill | Type | Purpose | Mode |
|-------|------|---------|------|
| `alto-protocol` | reference | Task/state/handoff formats | setup, build |
| `alto-feature-setup` | technique | Interactive feature setup | setup, build |
| `alto-configure` | technique | Configuration procedures | setup, build |
| `alto-switch` | technique | Switch orchestrator modes | all |
| `handoff-writing` | reference | Exact handoff format | build |
| `task-writing` | reference | Exact task file format | build |
| `review-writing` | reference | Exact review format | build |
| `scope-discipline` | discipline | Prevent over-engineering | setup, build |
| `alto-dev-guide` | reference | Documentation URLs and patterns | dev |
| `writing-alto-skills` | technique | Skill authoring methodology | dev |

### Skill Activation

Agent prompts explicitly reference skills:

```markdown
## Skills
- Read `skills/alto-configure/SKILL.md` — configuration procedures
- Read `skills/scope-discipline/SKILL.md` — only do what task asks
```

Reference-based activation:
- No discovery overhead per invocation
- Selective per agent (not all need all skills)
- Explicit in prompt (auditable)

---

## Orchestration Flow (Build Mode)

### Boot (New Run)

1. **Architecture Phase** (orchestrator does this directly):
   - Set phase = "ARCHITECTURE"
   - Read `alto.json` for `require_approval` setting
   - If `require_approval` is true:
     - Use EnterPlanMode tool
     - Explore codebase, read objective.md
     - Design high-level approach
     - Write `runs/milestones.md` and `runs/decisions.md`
     - Use ExitPlanMode tool (user approves)
   - If `require_approval` is false:
     - Explore and write milestones/decisions directly

2. **Planning Phase**:
   - Set phase = "PLANNING"
   - Invoke `alto-planner` with milestones.md as input
   - Planner creates `runs/plan.md` + `runs/tasks/task-001..N.md`
   - Set phase = "BETWEEN_TASKS"

### Execution Loop

3. **Arbiter check** (before each task):
   - If `runs/arbiter/pending.json` exists → invoke `alto-arbiter`
   - Read `runs/arbiter/decision.json`
   - If `needs_human == true` → set phase = "BLOCKED" and STOP

4. **Replan check** (after batch completion):
   - If `replan_every` is set and `completed_tasks % replan_every == 0`:
     - Set phase = "PLANNING"
     - Invoke `alto-planner` to create next batch
     - Continue to next task

5. **Execute**:
   - Read `runs/state.json` → open current `runs/tasks/task-XXX.md`
   - Set phase = "IN_TASK", `current_role` = role from task
   - Invoke the task's role agent (backend/frontend/docs/qa/gitops)

6. **Validate** (inside the role agent):
   - Run verification steps from task's "How to Verify" section

7. **Handoff**:
   - Role agent **edits** `runs/handoffs/task-XXX.md` (auto-created by hook)
   - Must use exact section headers: `## Summary`, `## Files Touched`, `## How to Verify`
   - Post-agents derive their path from task handoff
   - If task specifies post agents → invoke them in order

8. **Update Progress**:
   - If task completes an objective item → mark [x] in objective.md

9. **Advance**:
   - Mark task complete in `runs/state.json`
   - Set phase = "BETWEEN_TASKS", clear `current_role`
   - Proceed to next task (loop to step 3)

---

## Human Intervention Points

### Arbiter Checkpoints

**Triggering:**
- `Stop` and `SubagentStop` hooks trigger `arbiter-scheduler.py`
- Scheduler checks if phase == "BETWEEN_TASKS" (never runs mid-task)
- If thresholds exceeded, writes `runs/arbiter/pending.json`

**Checkpoints:**
- Orchestrator invokes `alto-arbiter` when `pending.json` exists
- Arbiter reviews: token burn, diff size, permission prompts, objective drift
- Writes checkpoint report to `runs/arbiter/checkpoints/<timestamp>.md`
- Writes `runs/arbiter/decision.json` with `needs_human` boolean
- At checkpoint, user can optionally reconfigure (via `alto-configure` skill)

**Thresholds** (`alto.json` → `arbiter`):
```json
{
  "arbiter": {
    "token_checkpoint_interval": 100000,
    "task_checkpoint_interval": 3,
    "max_files_changed_without_human": 50,
    "max_lines_changed_without_human": 2000
  }
}
```

### Feature Completion

When all tasks complete, orchestrator sets `phase = "COMPLETED"` and offers:

1. **Debug mode** — test and fix issues before merging
2. **Next feature** — merge and move on
3. **Reconfigure** — adjust ALTO settings

**Debug Mode** (`phase = "DEBUG"`):
- Stay on run branch, human tests feature
- Fix issues directly (no task files — fast iteration)
- Write debug summary to `runs/notes.md` when done

**Next Feature:**
1. Prompt human to merge (squash recommended)
2. Run `alto-clean` (keeps handoffs for context)
3. Switch to setup mode for new feature definition

---

## Claude Code Integration

ALTO is built on Claude Code features:

| Feature | ALTO Usage |
|---------|------------|
| Memory file (`CLAUDE.md`) | Orchestrator protocol loaded at launch |
| Project subagents (`agents/*.md`) | Define tool access, prompts, separate contexts |
| Hierarchical settings (`.claude/settings.json`) | Project-wide permissions |
| Hooks | Out-of-band tracking without LLM tokens |

References:
- Memory: https://docs.anthropic.com/en/docs/claude-code/memory
- Subagents: https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Settings: https://docs.anthropic.com/en/docs/claude-code/settings
- Hooks: https://docs.anthropic.com/en/docs/claude-code/hooks

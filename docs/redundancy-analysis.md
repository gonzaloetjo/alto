# ASM Protocol Redundancy Analysis

> Analysis of ASM state machine vs Claude Code native capabilities (post Feature-6)

## What Claude Code Already Provides

| Native Feature | What It Does |
|----------------|--------------|
| `Task` tool | Spawns specialized subagents (Explore, Plan, general-purpose, etc.) |
| `TodoWrite` | Basic task tracking within a conversation |
| `EnterPlanMode` / `ExitPlanMode` | Planning workflow with user approval |
| Conversation summarization | Context preserved within a session |
| Built-in agents | Role-based delegation (already in the system) |

## What ASM Adds That's NOT Redundant

### 1. Session Persistence (CRITICAL)

- Claude Code loses all context between sessions
- `runs/state.json`, handoffs, and task files provide continuity across restarts
- Run branches (`run/001`, `run/007`) provide audit trails

### 2. Human Review Gates (Arbiter)

- Claude has no built-in "stop and escalate to human" system
- The arbiter's BLOCK severity with `needs_human=true` is unique
- Token/diff thresholds for autonomous operation limits

### 3. Formal Handoff Format

- Structured context passing between tasks
- Better than relying on conversation memory for multi-day projects

### 4. Multi-Run Audit Trail

- Git branches per run, checkpoint reports
- No native equivalent

## What's GENUINELY REDUNDANT

| ASM Component | Claude Native Equivalent |
|---------------|--------------------------|
| `asm-planner` "PLANNING" phase | `EnterPlanMode` + `TodoWrite` |
| Role agents (`asm-backend`, `asm-frontend`) | `Task` tool with subagent_type already does this |
| `asm-qa` running tests | Claude can just run tests directly |
| Task status tracking | `TodoWrite` does this |
| `asm-recorder` (within session) | Conversation context already preserved |

## Simplification Recommendations

### Keep (unique value)

- `runs/state.json` - session persistence
- Handoff files - cross-session context
- Arbiter system - human review gates
- GitOps - commit discipline
- Run branches - audit trail

### Could Remove/Simplify

1. **Replace `asm-planner` with `EnterPlanMode`** - Claude's native planning is sufficient
2. **Merge role agents into Task prompts** - Instead of `asm-backend.md`, just use Task with a backend prompt
3. **Use TodoWrite for in-session tracking** - Only use task files for cross-session persistence
4. **Remove `asm-enforcer`** - Claude Code already has sandboxing and permission controls
5. **Simplify `asm-recorder`** - Within a session, conversation context suffices; only write handoffs at session end

## Core Value Proposition

The ASM protocol's **irreplaceable value** is:

1. **Cross-session state** - Claude forgets everything between sessions
2. **Human escalation gates** - Autonomous operation limits
3. **Git-based audit trail** - Run branches and commits

The **redundant parts** are the elaborate in-session orchestration (phases, role agents, enforcer) that duplicate Claude Code's native Task/TodoWrite/PlanMode capabilities.

## Suggested Minimal Protocol

```
Persistence Layer (KEEP):
  runs/state.json    → resume across sessions
  runs/handoffs/     → context for next session
  run/NNN branches   → audit trail

Human Gates (KEEP):
  arbiter            → token/diff limits, BLOCK for human review

Could Use Native:
  EnterPlanMode      → instead of "PLANNING" phase
  TodoWrite          → instead of task-*.md files
  Task subagents     → instead of separate asm-* agent files
```

## Decision Matrix

| Component | Keep | Simplify | Remove | Rationale |
|-----------|------|----------|--------|-----------|
| `runs/state.json` | ✓ | | | Cross-session persistence |
| `runs/handoffs/` | ✓ | | | Context for resumed sessions |
| `asm-arbiter` | ✓ | | | Human review gates |
| `asm-gitops` | | ✓ | | Useful but could be simpler |
| `asm-planner` | | | ✓ | Use EnterPlanMode |
| `asm-enforcer` | | | ✓ | Claude has native safeguards |
| `asm-recorder` | | ✓ | | Only at session boundaries |
| `asm-reviewer` | | ✓ | | Inline with task execution |
| Role agents | | ✓ | | Merge into Task prompts |
| Task files | | ✓ | | Use for persistence only |

---

*Analysis conducted: 2026-01-12*
*Context: Post Feature-6 completion (run/007)*

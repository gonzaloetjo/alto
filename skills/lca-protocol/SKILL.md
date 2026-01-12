---
name: lca-protocol
description: Defines the LCA task/state/handoff protocol and role handoffs for Claude Code subagents.
---

# LCA Protocol

## Required folders
- `runs/plan.md`
- `runs/state.json`
- `runs/tasks/`
- `runs/handoffs/`

## runs/state.json schema
```json
{
  "protocol": "lca-v1",
  "run_branch": "run/001",
  "phase": "PLANNING | IN_TASK | BETWEEN_TASKS | BLOCKED",
  "current_task_id": "task-001",
  "current_role": "lca-backend",
  "completed_task_ids": [],
  "last_handoff": null,
  "updated_at": "ISO-8601"
}
```

### Phase values
- `PLANNING` – planner is generating/updating tasks
- `IN_TASK` – a role agent is executing a task
- `BETWEEN_TASKS` – task completed, arbiter may run
- `BLOCKED` – human review required

## Arbiter checkpoint folders
- `runs/arbiter/config.json` – thresholds
- `runs/arbiter/state.json` – last checkpoint metadata
- `runs/arbiter/pending.json` – snapshot triggering arbiter
- `runs/arbiter/decision.json` – arbiter output
- `runs/arbiter/checkpoints/` – historical reports

## Task File Format (runs/tasks/task-XXX.md)

Each task starts with YAML frontmatter:

```yaml
task_id: task-001
title: Short human title
role: lca-backend | lca-frontend | lca-recorder | lca-docs | lca-gitops | lca-qa
follow_roles: []            # optional: list of agent names to additionally obey
post: []                    # optional: list of agent names to run after role succeeds
depends_on: []              # optional
inputs:
  - objective.md
  - runs/plan.md
  - runs/handoffs/task-000.md
allowed_paths:
  - backend/**
check_command: make check
handoff: runs/handoffs/task-001.md
```

Then Markdown body with:

* Goal
* Constraints (if any)
* Definition of Done (must be concrete)

## Handoff Format (runs/handoffs/<task_id>.md)

Must include:

* Summary
* Files touched
* Interfaces/contracts changed
* How to verify (commands)
* Next steps / risks

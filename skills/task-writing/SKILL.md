---
name: task-writing
description: Use when creating task files in runs/tasks/. Provides exact format required for task frontmatter and body sections.
---

# Task Writing

## Template

Task files go in `runs/tasks/task-{NNN}.md`. Use **exactly** this format:

```yaml
---
task_id: task-001
title: Short descriptive title
role: alto-backend
post: [alto-qa, code-simplifier, alto-gitops]
allowed_paths:
  - src/api/**
  - src/models/**
handoff: runs/handoffs/task-001.md
---

## Goal
What this task accomplishes (1-2 sentences).

## Definition of Done
- [ ] Concrete, verifiable criterion
- [ ] Another verifiable criterion
- [ ] Tests pass: `npm test`

## How to Verify
- Run `npm test` to verify tests pass
- Check API endpoint responds correctly

## Context
Reference to relevant handoffs or decisions if needed.
```

## Required Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Must match filename: `task-001` → `task-001.md` |
| `title` | string | Short description (5-10 words) |
| `role` | string | Agent to execute: `alto-backend`, `alto-frontend`, `alto-qa`, `alto-docs`, `alto-gitops`, `code-simplifier` |
| `allowed_paths` | list | Glob patterns agent can modify |
| `handoff` | string | Path for handoff file: `runs/handoffs/task-{id}.md` |

## Optional Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `post` | list | Post-agents to run after: `[alto-qa, code-simplifier, alto-gitops]` |
| `depends_on` | list | Task IDs that must complete first: `[task-001, task-002]` |
| `priority` | string | `high`, `medium`, `low` |

## Required Body Sections

1. **## Goal** - What this task accomplishes
2. **## Definition of Done** - Checkboxes with verifiable criteria
3. **## How to Verify** - Commands to run

## Rules

1. **task_id matches filename** - `task-001` must be in `task-001.md`
2. **role must be valid** - Only known role agents
3. **allowed_paths scoped** - Don't give `**/*` access
4. **DoD is verifiable** - Each item must be checkable
5. **Minimum body length** - Validation rejects tasks under 50 characters

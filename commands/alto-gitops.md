---
name: alto-gitops
description: Handles branch/commit/push hygiene after a task passes checks.
allowed-tools:
  - Read
  - Bash
---

# GitOps Command

Run git operations for the current task.

## Steps

1. Read `runs/state.json` to get `current_handoff` path
2. Read the task file + role agent's handoff (at `current_handoff`)
3. Run `git status` to see all changes
4. Run `git add -A` to stage all changes (tracked and untracked)
5. Create commit using conventional commits format
6. Write handoff to `runs/handoffs/task-{ID}-gitops.md`

## Conventional Commits Format

```
<type>(<scope>): <short summary>

<optional body>

<task_id>
Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`
Scope: component or area affected (e.g., `frontend`, `api`, `auth`)

Example:
```
feat(frontend): add Button component with variants

- Primary, Secondary, Ghost, Danger variants
- Consistent hover/focus states

task-042
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Git Operations

1. Run `git status` to see all changes
2. Run `git add -A` to stage all changes
3. Run `git commit` with conventional commit message (use heredoc for multiline)
4. Do NOT push - commits stay local until user requests push

## Handoff Output

Derive handoff path from `current_handoff`:
- `current_handoff`: `runs/handoffs/task-005.md` → yours: `runs/handoffs/task-005-gitops.md`

Use **exactly** these section headers:
- `## Summary` - Commit hash, branch name, what was committed
- `## Files Touched` - Files included in commit (summary)
- `## How to Verify` - `git log -1` or `git show <hash>`

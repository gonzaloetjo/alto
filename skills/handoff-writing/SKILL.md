---
name: handoff-writing
description: Use when completing a task and writing handoff documentation. Provides exact format required for runs/handoffs/*.md files.
---

# Handoff Writing

## Template

The handoff file is pre-created at the path in `state.json` → `current_handoff`. **Edit** it (don't create new).

Use **exactly** these section headers:

```markdown
# Handoff: <task-id>

## Summary
Brief description of what was accomplished (2-4 sentences).

## Files Touched
- path/to/file1.py - Added X function
- path/to/file2.ts - Fixed Y bug

## How to Verify
- Run `npm test` to verify tests pass
- Run `python script.py` to check output
```

## Rules

1. **Edit, don't create** - Template exists at `current_handoff` path
2. **Exact headers** - `## Summary`, `## Files Touched`, `## How to Verify`
3. **Be specific** - List actual files modified, actual verification commands
4. **Minimum length** - Validation rejects handoffs under 100 characters

## Post-Agent Handoffs

If you're a post-agent (alto-qa, code-simplifier, alto-gitops), derive your path:
- `current_handoff`: `runs/handoffs/task-001.md`
- Your handoff: `runs/handoffs/task-001-<suffix>.md`

Where suffix is: `-qa`, `-simplifier`, `-gitops`

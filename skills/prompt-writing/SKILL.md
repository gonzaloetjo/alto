---
name: prompt-writing
description: Use when writing or editing ALTO prompts - templates/CLAUDE.md.*, agents/*.md, or skills/*/SKILL.md. Rules for explicit tool references, paths, and user interactions.
---

# Prompt Writing Discipline

Rules for writing CLAUDE.md, agent prompts, and skills.

## Tool References

**ALWAYS use exact tool names:**
- `AskUserQuestion` not "ask the user"
- `Read` not "read the file"
- `Bash` not "run command"
- `gh issue view` not "check the issue"

## Paths

**ALWAYS use explicit paths:**
- `runs/state.json` not "state file"
- `templates/CLAUDE.md.dev` not "dev template"

## User Choices

**ALWAYS use AskUserQuestion with options:**

```
Use AskUserQuestion:
- Header: "Approach"
- Question: "How to proceed?"
- Options:
  1. Label: "Collaborative", Description: "Work together"
  2. Label: "Procedural", Description: "Follow /alto-self-fix"
```

Never write "ask the user" without specifying the tool and options.

## Efficiency

- **Batch**: Combine related operations
- **No redundant reads**: Read once, reference by variable
- **Explicit outputs**: State what to write where

## Forbidden Patterns

| Bad | Good |
|-----|------|
| "ask the user" | "Use AskUserQuestion with options: ..." |
| "check the issue" | "Run `gh issue view <n>`" |
| "update the file" | "Edit `path/to/file.md`" |
| "validate" | "Run `nix-instantiate --parse ...`" |

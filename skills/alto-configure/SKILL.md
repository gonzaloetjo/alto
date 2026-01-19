---
name: alto-configure
description: Use when configuring ALTO settings including arbiter thresholds, permissions, or verification hooks. Applies during setup orchestrator "Configure ALTO" selection, build orchestrator checkpoints, or when user requests configuration changes.
---

# ALTO Configuration

Shared configuration procedures for setup and build orchestrators.

## Arbiter Thresholds

Use `AskUserQuestion`:
- Header: "Autonomy"
- Question: "How much autonomy should ALTO have before checkpoints?"
- Options:
  1. Label: "Conservative", Description: "500 lines, 20 files, checkpoint every 2 tasks"
  2. Label: "Balanced (Recommended)", Description: "2000 lines, 50 files, checkpoint every 3 tasks"
  3. Label: "Autonomous", Description: "5000 lines, 100 files, checkpoint every 5 tasks"

**After user answers**, use Write tool to create `runs/arbiter/config.json`:

| Selection | max_lines | max_files | task_interval |
|-----------|-----------|-----------|---------------|
| Conservative | 500 | 20 | 2 |
| Balanced | 2000 | 50 | 3 |
| Autonomous | 5000 | 100 | 5 |

**JSON format (use Write tool with this exact structure):**
```json
{
  "max_lines_changed": <max_lines>,
  "max_files_changed": <max_files>,
  "task_checkpoint_interval": <task_interval>
}
```

Example for "Balanced":
```json
{
  "max_lines_changed": 2000,
  "max_files_changed": 50,
  "task_checkpoint_interval": 3
}
```

## Permissions

Use `AskUserQuestion`:
- Header: "Permissions"
- Question: "What permission level for bash commands?"
- Options:
  1. Label: "Supervised (Recommended)", Description: "Prompt for git, npm, docker"
  2. Label: "Autonomous", Description: "Auto-approve most commands"
  3. Label: "Locked", Description: "Prompt for everything"

If NOT "Supervised": Tell user to update `devenv.nix`:
```nix
alto.permissions.profile = "autonomous";  # or "locked"
```
Then `alto-restart`. (Permissions require Nix change - orchestrator cannot modify at runtime.)

## Verification (Existing Projects Only)

Read `runs/verification-config.json`, display current config, then use `AskUserQuestion`:
- Header: "Verification"
- Question: "How would you like to adjust verification?"
- Options:
  1. Label: "Keep current", Description: "No changes"
  2. Label: "Add pattern", Description: "Add verification for new file type"
  3. Label: "Edit command", Description: "Change existing command"
  4. Label: "Remove pattern", Description: "Remove file type verification"

**Use Write tool** to update `runs/verification-config.json` after user answers.

**JSON format:**
```json
{
  "<glob-pattern>": {
    "<check-type>": "<command>"
  }
}
```

Example:
```json
{
  "*.ts": { "typecheck": "npx tsc --noEmit", "lint": "npm run lint" },
  "*.py": { "lint": "ruff check {file}" },
  "*.test.ts": { "test": "npm test -- --related" }
}
```

Check types: `lint`, `typecheck`, `test`, `format`

## New Projects

Skip verification. Say: "Verification starts empty. QA agent configures it when tooling is set up."

## Key Rules

1. Orchestrator writes JSON files - never ask user to edit JSON manually
2. Orchestrator confirms changes after writing
3. Only permissions require user edit (devenv.nix + alto-restart)

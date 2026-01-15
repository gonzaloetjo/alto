---
name: alto-configure
type: technique
triggers:
  - running /alto-configure
  - first time setup
  - before starting new feature
---

# ALTO Configure

Interactive configuration for ALTO before starting a feature.

## When to Use

- First time setup (NEW_PROJECT detected)
- User requests configuration
- Before feature building when settings need adjustment

## Flow

### Step 1: Detect What Needs Configuration

Check current state:
```bash
cat runs/verification-config.json
cat runs/arbiter/config.json
cat runs/planning-config.json
```

### Step 2: Ask About Verification

Use AskUserQuestion:

```
Question: "What verification checks should run after file edits?"
Options:
- TypeScript/JavaScript (typecheck + lint)
- Python (ruff + pytest)
- Go (go vet + go test)
- None (I'll configure manually)
```

Based on answer, update `runs/verification-config.json`:

```json
{
  "*.ts": { "typecheck": "pnpm type:check", "lint": "pnpm lint" },
  "*.tsx": { "typecheck": "pnpm type:check", "lint": "pnpm lint" }
}
```

### Step 3: Ask About Arbiter Thresholds

```
Question: "How much autonomy should ALTO have before checkpoints?"
Options:
- Conservative (500 lines, 20 files, checkpoint every 2 tasks)
- Balanced (2000 lines, 50 files, checkpoint every 3 tasks) [default]
- Autonomous (5000 lines, 100 files, checkpoint every 5 tasks)
- Custom (I'll specify)
```

Update `runs/arbiter/config.json` accordingly.

### Step 4: Ask About Permission Profile (Requires Restart)

```
Question: "What permission level for bash commands?"
Options:
- Supervised (prompt for git, npm, docker) [default]
- Autonomous (auto-approve most commands)
- Locked (prompt for everything)
```

If user changes from default, generate Nix snippet:

```nix
# Add to devenv.nix:
alto.permissions.profile = "autonomous";
```

Tell user:
> "Permission profile requires devenv.nix change. Add the snippet above, then I'll restart to apply."

### Step 5: Apply and Restart (if needed)

If only dynamic configs changed:
> "Configuration updated. Changes take effect immediately."

If permission profile changed:
1. User adds Nix snippet to devenv.nix
2. Run `alto-restart` to apply

### Step 6: Transition to Feature Building

After configuration:
> "Configuration complete. Ready to start feature building."
> "Say 'continue' to begin architecture phase, or describe what you want to build."

## Configuration Reference

### Dynamic (immediate)

| File | Options |
|------|---------|
| `runs/verification-config.json` | File patterns → commands |
| `runs/arbiter/config.json` | `max_lines_changed_without_human`, `max_files_changed_without_human`, `token_checkpoint_interval`, `task_checkpoint_interval` |
| `runs/planning-config.json` | `require_approval`, `replan_strategy`, `fixed_batch_size` |

### Feature Boundary (needs restart)

| Setting | Nix Option |
|---------|------------|
| Permission profile | `alto.permissions.profile` |
| Allow bash | `alto.permissions.allowBash` |
| Deny bash | `alto.permissions.denyBash` |
| Deny read | `alto.permissions.denyRead` |

## Example Session

```
Claude: Welcome to ALTO configuration. Let me ask a few questions to set up your environment.

[AskUserQuestion: verification]
User: TypeScript/JavaScript

Claude: Great, I'll enable typecheck and lint for TS/JS files.
[Updates runs/verification-config.json]

[AskUserQuestion: arbiter]
User: Balanced

Claude: Using balanced thresholds (2000 lines, 50 files, checkpoint every 3 tasks).
[Updates runs/arbiter/config.json]

[AskUserQuestion: permissions]
User: Supervised

Claude: Using supervised mode (default). No restart needed.

Configuration complete. Ready to start feature building.
What would you like to build?
```

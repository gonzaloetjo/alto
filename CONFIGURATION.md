# ALTO Configuration Guide

All configurable options in ALTO, when to configure them, and how.

## Configuration Types

| Type | Location | When Applied | Changed By |
|------|----------|--------------|------------|
| **Static** | `devenv.nix` | On `direnv reload` | User edits file |
| **Runtime** | `runs/*.json` | Immediately | Orchestrator or user |

---

## Static Configuration (devenv.nix)

These options require editing `devenv.nix` and running `direnv reload`.

### Orchestrator Mode

```nix
alto.orchestrator = "setup";  # "setup" | "build" | "dev"
```

| Mode | Purpose | When to Use |
|------|---------|-------------|
| `setup` | Human-interactive | Feature definition, configuration, onboarding |
| `build` | Autonomous execution | Full protocol with architecture, planning, execution |
| `dev` | ALTO development | Developing ALTO itself (not consumer projects) |

**Switch modes**: Use `alto-switch <mode>` or `alto <mode>` (updates devenv.nix automatically).

---

### Arbiter Thresholds

Control when human review checkpoints trigger during autonomous execution.

```nix
alto.arbiter = {
  enable = true;                    # Enable/disable arbiter entirely
  maxLinesChanged = 2000;           # BLOCK if exceeded without review
  maxFilesChanged = 50;             # BLOCK if exceeded without review
  tokenCheckpointInterval = 100000; # Tokens between checkpoints
  taskCheckpointInterval = 3;       # Tasks between checkpoints
};
```

| Preset | Lines | Files | Tasks | Use Case |
|--------|-------|-------|-------|----------|
| Conservative | 500 | 20 | 2 | Unfamiliar codebase, high-risk changes |
| Balanced | 2000 | 50 | 3 | Normal development (default) |
| Autonomous | 5000 | 100 | 5 | Trusted environment, large features |

**Runtime alternative**: Edit `runs/arbiter/config.json` directly (no reload needed).

---

### Permissions

Three-tier permission system controlling what commands Claude can execute.

```nix
alto.permissions = {
  # Global profile
  profile = "supervised";  # "autonomous" | "supervised" | "locked"

  # Tier 1: Auto-allow (no prompt)
  allowBash = [ "ls" "cat" "head" "tail" "grep" "find" "echo" "pwd" "wc" ];

  # Tier 2: Ask user (prompt each time)
  askBash = [ "git" "npm" "pnpm" "yarn" "make" "docker" "python" "python3" "node" ];

  # Tier 3: Always deny (blocked)
  denyBash = [ "rm -rf" "sudo" "chmod" "chown" "curl|sh" "wget|sh" "git push -f" "git reset --hard" ];

  # File read restrictions
  denyRead = [ "./.env" "./.env.*" "./secrets/**" "**/*.pem" "**/*id_rsa*" "**/credentials*" ];
};
```

| Profile | Default Mode | Use Case |
|---------|--------------|----------|
| `autonomous` | acceptEdits | Trusted environments, fast iteration |
| `supervised` | default | Normal development (recommended) |
| `locked` | plan | Untrusted code, security-sensitive |

**Precedence**: deny > ask > allow (deny always wins).

---

### Per-Agent Permissions

Fine-grained control over individual agent capabilities.

```nix
alto.agentPermissions = {
  alto-backend = {
    permissionMode = "acceptEdits";  # "plan" | "acceptEdits" | "default"
    tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
    allowBash = [ "npm" "make" "python" "python3" "pip" "cargo" "go" ];
    askBash = [ "docker" "docker compose" ];
  };
  # ... similar for other agents
};
```

| Agent | Default Mode | Tools | Notes |
|-------|--------------|-------|-------|
| `alto-planner` | acceptEdits | Read, Grep, Glob, LS, Edit | No Bash |
| `alto-feature-finder` | plan | Read, Grep, Glob, LS | Read-only |
| `alto-backend` | acceptEdits | All + Bash | Full implementation |
| `alto-frontend` | acceptEdits | All + Bash | Full implementation |
| `alto-qa` | acceptEdits | All + Bash | Testing focus |
| `alto-docs` | acceptEdits | Read, Grep, Glob, LS, Edit | No Bash |
| `alto-gitops` | default | Read, Grep, Glob, LS, Bash | Prompts for git |
| `alto-reviewer` | plan | Read, Grep, Glob, LS | Read-only |
| `alto-arbiter` | plan | Read, Grep, Glob | Minimal |
| `alto-dev` | acceptEdits | All + WebFetch | ALTO development |

---

### Verification Hooks

Automatic quality checks after file edits (build mode only).

```nix
alto.verification = {
  typecheck = {
    enable = false;
    command = "pnpm type:check";
    matcher = "Edit:*.ts|Edit:*.tsx|Write:*.ts|Write:*.tsx";
  };

  lint = {
    enable = false;
    command = "pnpm lint";
    matcher = "Edit:*.ts|Edit:*.tsx|Edit:*.js|Edit:*.jsx|Write:*.ts|Write:*.tsx|Write:*.js|Write:*.jsx";
  };

  test = {
    enable = false;
    command = "npm test -- --related";
    matcher = "Edit:*.test.*|Edit:*.spec.*|Write:*.test.*|Write:*.spec.*";
  };

  # Custom hooks
  custom = [
    { name = "security-check"; command = "./scripts/security.sh"; matcher = "Edit:src/auth/*"; timeout = 30000; }
  ];
};
```

**Runtime alternative**: Edit `runs/verification-config.json` for dynamic verification.

---

### Planning Configuration

Control the architecture and planning phases.

```nix
alto.planning = {
  requireApproval = true;      # Require user approval after architecture
  replanStrategy = "auto";     # "auto" | "fixed" | "none"
  fixedBatchSize = 5;          # Tasks per batch (when strategy = "fixed")
  architectModel = "opus";     # "opus" | "sonnet"
  plannerModel = "opus";       # "opus" | "sonnet"
};
```

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `auto` | Batch size based on estimated task count | Most projects |
| `fixed` | Always use `fixedBatchSize` | Predictable batching |
| `none` | No replanning | Simple features |

**Cost optimization**: Set `plannerModel = "sonnet"` for cheaper task generation.

---

### Other Options

```nix
alto.runsDir = "runs";              # Runtime state directory
alto.debug = false;                 # Enable event logging to runs/logs/events.jsonl
alto.includeSpawnerSkills = false;  # Include domain skills (api-design, frontend, etc.)
```

---

## Runtime Configuration (runs/*.json)

These files can be edited mid-session without reloading.

### runs/arbiter/config.json

```json
{
  "max_lines_changed_without_human": 2000,
  "max_files_changed_without_human": 50,
  "token_checkpoint_interval": 100000,
  "task_checkpoint_interval": 3,
  "high_risk_bash_prefixes": ["rm -rf /", "sudo rm", "dd if=", "mkfs", "> /dev/"]
}
```

**Changed by**: Orchestrator during configuration, or edit directly.

### runs/verification-config.json

Dynamic verification commands per file pattern.

```json
{
  "*.ts": { "command": "pnpm type:check" },
  "*.tsx": { "command": "pnpm type:check && pnpm lint" },
  "*.py": { "command": "pytest" },
  "*.go": {}
}
```

**Changed by**: QA agent when setting up tooling, or edit directly.

### runs/planning-config.json

```json
{
  "require_approval": true,
  "replan_strategy": "auto",
  "fixed_batch_size": 5,
  "architect_model": "opus",
  "planner_model": "opus"
}
```

**Changed by**: Orchestrator, synced from devenv.nix on deploy.

### runs/orchestrator.json

```json
{
  "orchestrator": "setup",
  "updated_at": "2026-01-16T12:00:00+00:00"
}
```

**Changed by**: `alto-switch` command.

---

## When to Configure

### Setup Mode (First Time)

Setup mode is designed for configuration. The orchestrator will:

1. **Ask about autonomy** → writes `runs/arbiter/config.json`
2. **Ask about permissions** → tells user to edit `devenv.nix` if needed
3. **Skip verification** → QA agent configures when tooling is set up

### Build Mode (Checkpoints)

At arbiter checkpoints and feature completion, the orchestrator offers:
- "Reconfigure" option → same flow as setup mode
- Useful for adjusting thresholds mid-feature

### Dev Mode

Minimal configuration. Dev mode is for ALTO development, not consumer projects.

---

## Quick Reference

### Common Adjustments

| Want to... | Edit | Reload? |
|------------|------|---------|
| Switch modes | `alto-switch <mode>` | Auto |
| More autonomy | `runs/arbiter/config.json` | No |
| Allow more commands | `devenv.nix` → `permissions.allowBash` | Yes |
| Add typecheck hook | `devenv.nix` → `verification.typecheck.enable` | Yes |
| Use cheaper models | `devenv.nix` → `planning.plannerModel = "sonnet"` | Yes |
| Enable debug logging | `devenv.nix` → `alto.debug = true` | Yes |

### Reload Commands

```bash
# After editing devenv.nix
direnv reload

# Or re-enter directory
cd .. && cd -

# Force full refresh
alto-update
```

# ALTO - Autonomous Lifecycle Task Orchestrator

**Multi-agent orchestration for Claude Code with human review gates.**

## What ALTO Provides

- **Session persistence** - State survives across Claude Code sessions via `runs/state.json` and handoffs
- **Human review gates** - Arbiter agent blocks when thresholds exceeded (lines changed, tokens burned, etc.)
- **Structured handoffs** - Context preserved between tasks for cross-session continuity
- **Git-based audit trail** - Run branches and checkpoint reports

## Quick Start

### New Project

```bash
# Initialize ALTO in your project
nix flake init -t github:gonzaloetjo/alto

# Enter the dev shell
devenv shell
# Or keep your shell: devenv shell -- zsh
# Or with fish:       devenv shell -- fish
```

Then start Claude Code:

```bash
claude
```

ALTO detects it's a new project and asks:

```
Welcome to ALTO! This project hasn't been set up yet.

What would you like to do?
○ Set up project
○ Explain ALTO
```

Select "Set up project" and describe what you want to build.

### Existing Project

```bash
cd my-project
devenv shell  # or: devenv shell -- zsh

claude
```

ALTO detects the state and asks:

```
Ready to start. I see your objective.md.

What would you like to do?
○ Start building
○ New feature
○ Show status
```

If work is in progress, it resumes automatically.

### Using direnv (optional)

If you prefer automatic environment activation:

```bash
# Install direnv: https://direnv.net/docs/installation.html
# Add to your shell rc file (e.g. ~/.zshrc):
#   eval "$(direnv hook zsh)"

# Then in your project:
direnv allow
```

Now the environment activates automatically when you `cd` into the project.

### Available Scripts

| Script | Purpose |
|--------|---------|
| `alto-setup` | First-time project initialization |
| `alto-status` | Show current ALTO status |
| `alto-new-run` | Create new run branch |
| `alto-clean` | Clean previous run artifacts |

## What Gets Deployed

When you enter the environment, ALTO automatically creates:

```
your-project/
├── .claude/
│   ├── agents/          # 12 ALTO agents
│   ├── hooks/           # 7 tracking hooks
│   ├── skills/          # Protocol + feature setup skills
│   └── settings.json    # Permissions + hooks config
├── .mcp.json            # MCP servers (includes devenv MCP)
├── runs/
│   ├── state.json       # Current phase, task, role
│   ├── tasks/           # Task definitions
│   ├── handoffs/        # Task outputs + context
│   └── arbiter/         # Human review checkpoints
└── CLAUDE.md            # Orchestrator protocol
```

## Configuration Options

In your `devenv.nix`:

```nix
{ pkgs, ... }:
{
  alto = {
    enable = true;

    # Arbiter thresholds (human review gates)
    arbiter = {
      enable = true;                    # default: true
      maxLinesChanged = 2000;           # BLOCK if exceeded
      maxFilesChanged = 50;             # BLOCK if exceeded
      tokenCheckpointInterval = 100000; # Checkpoint every N tokens
      taskCheckpointInterval = 3;       # Checkpoint every N tasks
    };

    # Planning configuration
    planning = {
      requireApproval = true;           # Gate architecture with user approval
      replanStrategy = "auto";          # auto, fixed, or none
    };

    # Permission settings for Claude Code
    permissions = {
      defaultMode = "bypassPermissions";  # or "askEveryTime", "allowEdits"
      allowBash = [ "git" "make" "npm" "docker" "python3" ];
      askBash = [ "git push" ];
      denyRead = [ "./.env" "./secrets/**" "**/*.pem" ];
      denyBash = [ "rm -rf" "sudo" ];
    };

    # Include domain skills from spawner
    includeSpawnerSkills = false;  # default: false

    # Runtime directory name
    runsDir = "runs";  # default: "runs"
  };
}
```

## Protocol Overview

### State Machine

```
ARCHITECTURE → PLANNING → IN_TASK → BETWEEN_TASKS → (repeat or COMPLETE)
                              ↓
                           BLOCKED (human review required)
```

### Agents

| Agent | Role |
|-------|------|
| `alto-planner` | Generate tasks from milestones |
| `alto-feature-finder` | Analyze codebase, identify features |
| `alto-arbiter` | Human review gates |
| `alto-backend` | Backend implementation |
| `alto-frontend` | Frontend implementation |
| `alto-qa` | Testing and fixes |
| `alto-docs` | Documentation |
| `alto-gitops` | Git commits |
| `alto-recorder` | Handoff summaries |
| `alto-reviewer` | Code quality gate |
| `alto-enforcer` | Protocol compliance |
| `code-simplifier` | Code clarity refinement |

### Task Flow

1. **Architecture** - Orchestrator explores codebase, creates milestones
2. **Planning** - Planner creates task files from milestones
3. **Execution** - Role agents implement tasks
4. **Review** - Reviewer + Enforcer validate
5. **Handoff** - Recorder + GitOps finalize
6. **Arbiter** - Checks thresholds, may BLOCK for human review

## Skills

**Protocol skills** (always included):
- `alto-protocol` - State machine, task/handoff formats
- `alto-feature-setup` - Interactive feature setup

**Domain skills** (opt-in via `includeSpawnerSkills = true`):
- api-design, database-migrations, postgres-wizard, python-backend, queue-workers
- frontend, tailwind-css, ui-design, ux-design, design-systems, color-theory
- docker, logging-strategies, security, testing-strategies, error-handling
- embedded-systems, sensor-fusion, state-management

## Manual Installation (without Nix)

If not using Nix:

1. Copy `agents/` to `.claude/agents/`
2. Copy `hooks/` to `.claude/hooks/`
3. Copy `skills/alto-protocol/` and `skills/alto-feature-setup/` to `.claude/skills/`
4. Copy `templates/CLAUDE.md.template` to `CLAUDE.md`
5. Create `runs/` directory structure manually
6. Create `.claude/settings.json` based on the template in `devenv.nix`

## License

MIT

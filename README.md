# ALTO - Autonomous Lifecycle Task Orchestrator

**Multi-agent orchestration for Claude Code with human review gates.**

## What ALTO Provides

- **Session persistence** - State survives across Claude Code sessions via `runs/state.json` and handoffs
- **Human review gates** - Arbiter agent blocks when thresholds exceeded (lines changed, tokens burned, etc.)
- **Structured handoffs** - Context preserved between tasks for cross-session continuity
- **Git-based audit trail** - Run branches and checkpoint reports

## Quick Start

```bash
# Initialize ALTO in your project
nix flake init -t github:gonzaloetjo/alto

# Enter the dev shell
devenv shell

# ALTO: Deploying Claude Code configuration...
# ALTO: Ready. Start Claude Code and say 'continue' or '/alto-feature-setup' to begin.

claude
> continue
```

That's it. Two commands.

## What Gets Deployed

When you enter the shell, ALTO automatically creates:

```
your-project/
├── .claude/
│   ├── agents/          # 11 ALTO agents
│   ├── hooks/           # 7 tracking hooks
│   ├── skills/          # Protocol + optional domain skills
│   └── settings.json    # Permissions + hooks config
├── runs/
│   ├── state.json       # Current phase, task, role
│   ├── tasks/           # Task definitions
│   ├── handoffs/        # Task outputs + context
│   └── arbiter/         # Human review checkpoints
└── CLAUDE.md            # Orchestrator protocol
```

## Configuration Options

```nix
{ inputs, pkgs, ... }:
{
  imports = [ inputs.alto.devenvModules.default ];

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
PLANNING → IN_TASK → BETWEEN_TASKS → (repeat or COMPLETE)
              ↓
           BLOCKED (human review required)
```

### Agents

| Agent | Role | Model |
|-------|------|-------|
| `alto-planner` | Generate plan and tasks | opus |
| `alto-arbiter` | Human review gates | opus |
| `alto-backend` | Backend implementation | sonnet |
| `alto-frontend` | Frontend implementation | opus |
| `alto-qa` | Testing and fixes | sonnet |
| `alto-docs` | Documentation | sonnet |
| `alto-gitops` | Git commits | haiku |
| `alto-recorder` | Handoff summaries | haiku |
| `alto-reviewer` | Code quality gate | opus |
| `alto-enforcer` | Protocol compliance | sonnet |
| `code-simplifier` | Code clarity refinement | opus |

### Task Flow

1. **Planner** creates task files from `objective.md`
2. **Role agent** (backend/frontend/qa) implements
3. **Reviewer** checks code quality (can reject)
4. **Enforcer** checks protocol compliance (can reject)
5. **Post agents** (recorder, gitops) finalize
6. **Arbiter** runs between tasks if thresholds hit → may BLOCK

## Using with Flakes (Alternative)

If you prefer flakes over the devenv CLI:

<details>
<summary>Plain Flakes</summary>

```nix
{
  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    devenv.url = "github:cachix/devenv";
    alto.url = "github:gonzaloetjo/alto";
  };

  outputs = { self, nixpkgs, devenv, alto, ... }@inputs:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = devenv.lib.mkShell {
        inherit inputs pkgs;
        modules = [
          alto.devenvModules.default
          { alto.enable = true; }
        ];
      };
    };
}
```

Run: `nix develop --no-pure-eval`

</details>

<details>
<summary>flake-parts</summary>

```nix
{
  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    devenv.url = "github:cachix/devenv";
    flake-parts.url = "github:hercules-ci/flake-parts";
    alto.url = "github:gonzaloetjo/alto";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ inputs.devenv.flakeModule ];
      systems = [ "x86_64-linux" "aarch64-darwin" ];

      perSystem = { pkgs, ... }: {
        devenv.shells.default = {
          imports = [ inputs.alto.devenvModules.default ];
          alto.enable = true;
        };
      };
    };
}
```

Run: `nix develop --no-pure-eval`

</details>

## Skills

**Protocol skills** (always included):
- `alto-protocol` - State machine, task/handoff formats
- `alto-feature-setup` - Interactive feature setup checklist

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
6. Create `.claude/settings.json` based on the template in `devenv-module.nix`

## License

MIT

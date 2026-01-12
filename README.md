# LCA Protocol

**Lifecycle Architecture for Claude Code** - A protocol for autonomous AI agents with human review gates.

## What is LCA?

LCA provides:
- **Session persistence** - State survives across Claude Code sessions
- **Human review gates** - Arbiter system blocks when thresholds exceeded
- **Structured handoffs** - Context preserved between tasks
- **Git-based audit trail** - Run branches and checkpoints

## Quick Start

### With devenv.sh (recommended)

Add to your `devenv.nix`:

```nix
{
  inputs.lca-protocol.url = "github:YOUR_USERNAME/lca-protocol";
}
```

```nix
{ inputs, ... }:
{
  imports = [ inputs.lca-protocol.devenvModules.default ];

  lca.enable = true;
}
```

Run `devenv shell` and you're ready.

### Configuration Options

```nix
{
  lca = {
    enable = true;

    # Arbiter thresholds (human review gates)
    arbiter = {
      enable = true;
      maxLinesChanged = 2000;      # BLOCK if exceeded
      maxFilesChanged = 50;        # BLOCK if exceeded
      tokenCheckpointInterval = 100000;
      taskCheckpointInterval = 3;
    };

    # Enable/disable agents
    agents = {
      backend = true;
      frontend = true;
      qa = true;
      docs = true;
      gitops = true;
      planner = true;
      recorder = true;
      reviewer = true;
      enforcer = true;
    };

    # Enable/disable hooks
    hooks = {
      sessionStart = true;
      sessionSummary = true;
      toolRecord = true;
    };

    # Runtime directory
    runsDir = "runs";

    # Add project-specific agents
    extraAgents = {
      my-specialist = {
        description = "Domain specialist for X";
        tools = [ "Read" "Edit" "Bash" ];
        model = "sonnet";
        prompt = "You are a specialist in...";
      };
    };
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

### Directory Structure

```
runs/
├── state.json           # Current state (phase, task, etc.)
├── plan.md              # Architecture and task outline
├── tasks/               # Task definitions
│   ├── task-001.md
│   └── ...
├── handoffs/            # Task outputs and context
│   ├── task-001.md
│   ├── task-001-recorder.md
│   └── ...
├── arbiter/             # Audit checkpoints
│   ├── config.json
│   ├── state.json
│   └── checkpoints/
└── review/              # Review decisions
```

### Agents

| Agent | Role | Model |
|-------|------|-------|
| `lca-planner` | Generate plan and tasks | opus |
| `lca-arbiter` | Human review gates | opus |
| `lca-backend` | Backend implementation | sonnet |
| `lca-frontend` | Frontend implementation | sonnet |
| `lca-qa` | Testing and fixes | sonnet |
| `lca-docs` | Documentation | haiku |
| `lca-gitops` | Git commits | haiku |
| `lca-recorder` | Handoff summaries | haiku |
| `lca-reviewer` | Code review | sonnet |
| `lca-enforcer` | Protocol compliance | sonnet |

### Task Flow

1. **Planner** creates task files
2. **Role agent** (backend/frontend/qa) implements
3. **Reviewer** checks code quality
4. **Enforcer** checks protocol compliance
5. **Post agents** (recorder, gitops) finalize
6. **Arbiter** runs between tasks if thresholds hit

## Why LCA?

Claude Code loses context between sessions. LCA solves this with:

| Problem | LCA Solution |
|---------|--------------|
| Session amnesia | `runs/state.json` + handoffs |
| Runaway autonomous agents | Arbiter with BLOCK severity |
| No audit trail | Run branches + checkpoints |
| Context loss between tasks | Structured handoffs |

See [docs/redundancy-analysis.md](docs/redundancy-analysis.md) for detailed comparison with Claude Code native features.

## Manual Installation (without devenv)

If not using devenv.sh:

1. Copy `agents/`, `hooks/`, `skills/` to `.claude/`
2. Create `runs/` directory structure
3. Add protocol to `CLAUDE.md`

## License

MIT

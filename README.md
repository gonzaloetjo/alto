<p align="center">
  <h1 align="center">ALTO</h1>
  <p align="center">
    <em>Autonomous Lifecycle Task Orchestrator</em>
  </p>
  <p align="center">
    Multi-agent orchestration for Claude Code with human review gates.
  </p>
</p>

---

## Context Distribution

ALTO routes tasks based on where they fall along three axes:

```
[Input]
No Context ◀──────────────────────────────────────▶ Full Context
self-contained                                 context-dependent

[Output]
Deterministic ◀──────────────────────────────────────▶ Judgment
same input = same output                        requires inference

[Process]
Atomic ◀──────────────────────────────────────▶ Compound
single operation                      multiple operations, aware of changes
```

### Routing Examples

- **Code** - Deterministic, no context, atomic
- **Skill** - Judgment, minimal context, atomic
- **Agent** - Judgment, partial context, compound
- **Orchestrator** - Judgment, full context, compound

---

## How It Works

```
objective.md → Architecture → Planning → Execution → Completion
     │              │             │           │           │
     │              │             │           │           └─▶ debug / next feature
     │              │             │           │
     │              │             │           └─▶ role agent → handoff → QA → gitops
     │              │             │                              │
     │              │             │                   runs/handoffs/task-XXX.md
     │              │             │
     │              │             └─▶ planner creates task files
     │              │
     │              └─▶ orchestrator explores, writes milestones
     │
     └─▶ user defines feature (setup mode)
```

Agents never communicate directly. Each writes a structured **handoff** to `runs/handoffs/` which the orchestrator reads and passes to the next agent.

Each phase has arbiter checkpoints for human review. See [ARCHITECTURE.md](ARCHITECTURE.md) for the full lifecycle.

---

## Quick Start

```bash
# Initialize in your project
nix flake init -t github:gonzaloetjo/alto

# Enter the environment
devenv shell

# Start ALTO
alto
```

ALTO will guide you through setup interactively.

---

## Modes

| Mode | Purpose |
|------|---------|
| **setup** | Human-interactive: feature definition, configuration |
| **build** | Autonomous: architecture → planning → execution |
| **dev** | ALTO development (meta) |

Switch modes: `alto dev`, `alto build`, `alto setup`

---

## Commands

| Command | Description |
|---------|-------------|
| `alto` | Start/resume current mode |
| `alto <mode>` | Switch mode and start |
| `alto-status` | Show current state |
| `alto-clean` | Clean run artifacts |
| `alto-new-run` | Start new run branch |
| `alto-update` | Update ALTO |

---

## Configuration

All configuration in `alto.json` (dynamic) or `devenv.nix` (static):

```nix
alto = {
  enable = true;
  orchestrator = "setup";
  arbiter.maxLinesChanged = 2000;
  permissions.profile = "supervised";
};
```

See [OPERATIONS.md](OPERATIONS.md) for all options.

---

## Documentation

| Document | Audience | Content |
|----------|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Humans | Design model, lifecycle |
| [AI-CONTEXT.md](AI-CONTEXT.md) | AI agents | State machine, formats, flow |
| [OPERATIONS.md](OPERATIONS.md) | Operators | Commands, config, troubleshooting |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Contributors | Dev mode, testing, extending |

---

## License

MIT

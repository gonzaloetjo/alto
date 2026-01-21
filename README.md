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

ALTO routes tasks based on where they fall along two axes:

```
Deterministic ◀──────────────────────────────────────▶ Judgment
same input = same output                        requires inference

No Context ◀──────────────────────────────────────▶ Full Context
self-contained                       needs information understanding
```

### Routing

- **Code** - Deterministic, no context
- **Skill** - Judgment, minimal context (task spec only)
- **Agent** - Judgment, partial context (task + state/handoffs)
- **Orchestrator** - Judgment, full context (codebase exploration)

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

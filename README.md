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

### The Axes

**Determinism ↔ Judgment**
- **Deterministic:** Predictable, repeatable logic. Same input, same output.
- **Judgment:** Nuanced reasoning or creative synthesis. No fixed answer.

**Context Scope**
- **None:** The task is self-contained and requires zero project knowledge.
- **Full:** The task requires understanding of the entire codebase and architecture.

### Routing Logic

Tasks are assigned to an executor based on their coordinates within these axes:

| Executor | Logic Type | Context Level |
| --- | --- | --- |
| **Code** | Deterministic | None |
| **Skill** | Judgment | Minimal (task spec only) |
| **Agent** | Judgment | Partial (task + state/handoffs) |
| **Orchestrator** | Judgment | Full (codebase exploration) |

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

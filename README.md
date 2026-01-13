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

## Highlights

- **Session persistence** — State survives across Claude Code sessions
- **Human review gates** — Arbiter blocks when thresholds are exceeded
- **Structured handoffs** — Context preserved between tasks
- **Git audit trail** — Run branches and checkpoint reports

---

## Quick Start

```bash
# Initialize in your project
nix flake init -t github:gonzaloetjo/alto

# Enter the environment
devenv shell

# Start Claude
claude
```

ALTO will guide you through setup interactively.

---

## How It Works

```
ARCHITECTURE → PLANNING → IN_TASK → BETWEEN_TASKS → COMPLETE
                              ↓
                           BLOCKED (human review)
```

**Agents** handle specialized tasks: planning, implementation (backend/frontend), QA, docs, git, and review. The **Arbiter** monitors thresholds and triggers human checkpoints.

---

## Project Structure

After entering the environment:

```
your-project/
├── .claude/
│   ├── agents/        # ALTO agents
│   ├── hooks/         # Tracking hooks
│   ├── skills/        # Protocol skills
│   └── settings.json
├── runs/
│   ├── state.json     # Current phase/task
│   ├── tasks/         # Task definitions
│   ├── handoffs/      # Task outputs
│   └── arbiter/       # Review checkpoints
└── CLAUDE.md          # Orchestrator protocol
```

---

## Configuration

```nix
# devenv.nix
{ pkgs, ... }:
{
  alto = {
    enable = true;

    arbiter = {
      maxLinesChanged = 2000;
      maxFilesChanged = 50;
      tokenCheckpointInterval = 100000;
    };

    permissions = {
      defaultMode = "bypassPermissions";
      allowBash = [ "git" "make" "npm" "docker" ];
      denyBash = [ "rm -rf" "sudo" ];
    };

    # Auto-run verification after file edits
    verification = {
      typecheck.enable = true;
      typecheck.command = "pnpm type:check";
      lint.enable = true;
      lint.command = "pnpm lint";
      test.enable = true;
      test.command = "npm test -- --related";
    };
  };
}
```

<details>
<summary><strong>All options</strong></summary>

| Option | Default | Description |
|--------|---------|-------------|
| `arbiter.enable` | `true` | Enable human review gates |
| `arbiter.maxLinesChanged` | `2000` | Block threshold for lines |
| `arbiter.maxFilesChanged` | `50` | Block threshold for files |
| `arbiter.tokenCheckpointInterval` | `100000` | Checkpoint every N tokens |
| `arbiter.taskCheckpointInterval` | `3` | Checkpoint every N tasks |
| `planning.requireApproval` | `true` | Gate architecture approval |
| `planning.replanStrategy` | `"auto"` | `auto`, `fixed`, or `none` |
| `permissions.defaultMode` | `"bypassPermissions"` | Permission mode |
| `permissions.allowBash` | `[]` | Allowed bash commands |
| `permissions.askBash` | `[]` | Ask-before-run commands |
| `permissions.denyBash` | `[]` | Blocked commands |
| `permissions.denyRead` | `[]` | Blocked file patterns |
| `includeSpawnerSkills` | `false` | Include domain skills |
| `runsDir` | `"runs"` | Runtime directory name |
| `verification.typecheck.enable` | `false` | Auto-run typecheck after TS edits |
| `verification.typecheck.command` | `"pnpm type:check"` | Typecheck command |
| `verification.lint.enable` | `false` | Auto-run linter after edits |
| `verification.lint.command` | `"pnpm lint"` | Lint command |
| `verification.test.enable` | `false` | Auto-run tests after test file edits |
| `verification.test.command` | `"npm test -- --related"` | Test command |
| `verification.custom` | `[]` | Custom verification hooks |

</details>

---

## Scripts

| Command | Description |
|---------|-------------|
| `alto-status` | Show current status |
| `alto-new-run` | Create new run branch |
| `alto-clean` | Clean run artifacts |
| `alto-feature` | Start new feature |

---

## Agents

| Agent | Purpose |
|-------|---------|
| `alto-planner` | Generate tasks from milestones |
| `alto-arbiter` | Human review gates |
| `alto-backend` | Backend implementation |
| `alto-frontend` | Frontend implementation |
| `alto-qa` | Testing and fixes |
| `alto-docs` | Documentation |
| `alto-gitops` | Git operations |
| `alto-reviewer` | Code quality |

---

## Using direnv

For automatic environment activation:

```bash
# After installing direnv (https://direnv.net)
direnv allow
```

---

## Manual Install

Without Nix, copy manually:

1. `agents/` → `.claude/agents/`
2. `hooks/` → `.claude/hooks/`
3. `skills/alto-protocol/`, `skills/alto-feature-setup/` → `.claude/skills/`
4. `templates/CLAUDE.md.template` → `CLAUDE.md`
5. Create `runs/` structure
6. Create `.claude/settings.json`

---

## License

MIT

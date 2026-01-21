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

# Start ALTO
alto
```

ALTO will guide you through setup interactively.

---

## How It Works

ALTO has three orchestrator modes:

| Mode | Purpose |
|------|---------|
| **setup** | Human-interactive: feature definition, configuration, cleanup |
| **build** | Autonomous: architecture → planning → execution → completion |
| **dev** | ALTO development: single `alto-dev` agent with dev-guide skill |

```
SETUP MODE                          BUILD MODE
────────────                        ──────────
• Configure ALTO                    ARCHITECTURE → PLANNING → IN_TASK → COMPLETE
• Write objective.md                                              ↓
• Cleanup between features                                     BLOCKED (checkpoint)
        │                                   │
        └──► "Start building" ──►           └──► "Next feature" ──►
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

    # Orchestrator mode: "setup", "build", or "dev"
    orchestrator = "setup";  # default - start here, switch to build when ready

    arbiter = {
      maxLinesChanged = 2000;
      maxFilesChanged = 50;
      tokenCheckpointInterval = 100000;
    };

    # Three-tier permissions: allow (auto), ask (prompt), deny (block)
    permissions = {
      profile = "supervised";  # autonomous, supervised, or locked
      allowBash = [ "ls" "cat" "grep" "find" "pwd" ];  # auto-approve
      askBash = [ "git" "npm" "make" "docker" ];        # prompt user
      denyBash = [ "rm -rf" "sudo" "git push -f" ];     # always block
      denyRead = [ ".env" "secrets/**" "**/*.pem" ];    # sensitive files
    };

    # Auto-run verification after file edits (static)
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

**Dynamic verification:** Edit `alto.json` → `verification` section mid-session without shell restart. See ARCHITECTURE.md for format.

<details>
<summary><strong>All options</strong></summary>

| Option | Default | Description |
|--------|---------|-------------|
| `orchestrator` | `"setup"` | Mode: `"setup"`, `"build"`, or `"dev"` (ALTO development) |
| `arbiter.enable` | `true` | Enable human review gates |
| `arbiter.maxLinesChanged` | `2000` | Block threshold for lines |
| `arbiter.maxFilesChanged` | `50` | Block threshold for files |
| `arbiter.tokenCheckpointInterval` | `100000` | Checkpoint every N tokens |
| `arbiter.taskCheckpointInterval` | `3` | Checkpoint every N tasks |
| `planning.requireApproval` | `true` | Gate architecture approval |
| `planning.replanStrategy` | `"auto"` | `auto`, `fixed`, or `none` |
| `planning.fixedBatchSize` | `5` | Batch size when replanStrategy = `fixed` |
| `planning.architectModel` | `"opus"` | Model for architecture phase |
| `planning.plannerModel` | `"opus"` | Model for planner agent |
| `permissions.profile` | `"supervised"` | `autonomous`, `supervised`, or `locked` |
| `permissions.allowBash` | `[ls, cat, grep...]` | Auto-approved bash commands |
| `permissions.askBash` | `[git, npm, docker...]` | Prompt-before-run commands |
| `permissions.denyBash` | `[rm -rf, sudo...]` | Always blocked commands |
| `permissions.denyRead` | `[.env, secrets/**...]` | Blocked file patterns |
| `agentPermissions.<agent>` | (see devenv.nix) | Per-agent tools, permissionMode, bash tiers |
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
| `alto` | Main entry point. Resumes current mode session, sends "hi" if no args |
| `alto dev/build/setup` | Switch to specified mode and start Claude |
| `alto-status` | Show current status (includes orchestrator mode) |
| `alto-new-run` | Create new run branch |
| `alto-clean` | Clean run artifacts |
| `alto-nuke` | Full reset (removes .claude/, runs/, CLAUDE.md, objective.md) |
| `alto-feature` | Start new feature |
| `alto-update` | Force update ALTO to latest version |

---

## Agents

| Agent | Mode | Purpose | Permission Mode |
|-------|------|---------|-----------------|
| `alto-planner` | build | Generate tasks from milestones | acceptEdits |
| `alto-feature-finder` | setup, build | Analyze codebase for next steps | plan (read-only) |
| `alto-backend` | build | Backend implementation | acceptEdits |
| `alto-frontend` | build | Frontend implementation | acceptEdits |
| `alto-qa` | build | Testing and verification config | acceptEdits |
| `alto-docs` | build | Documentation | acceptEdits |
| `alto-gitops` | build | Git operations | default (prompts) |
| `alto-reviewer` | build | Code quality review | plan (read-only) |
| `alto-arbiter` | build | Human review gates | plan (read-only) |
| `alto-dev` | dev | ALTO development | acceptEdits |

---

## Permissions

ALTO uses a three-tier permission system:

| Tier | Behavior | Example |
|------|----------|---------|
| **allow** | Auto-approved | `ls`, `cat`, `grep` |
| **ask** | Prompts user | `git commit`, `npm install` |
| **deny** | Always blocked | `rm -rf`, `sudo`, `git push -f` |

**Per-agent restrictions** are enforced through agent prompts and permissionMode:

- **plan** — Read-only mode for analysis agents
- **acceptEdits** — Auto-approves file edits for implementation agents
- **default** — Prompts for each action (git operations)

> **Note:** The `ask` tier and per-agent `permissionMode` require pending devenv enhancements. Currently, `allow` and `deny` work; per-agent modes are documented in agent prompts.

---

## Using direnv

For automatic environment activation:

```bash
# After installing direnv (https://direnv.net)
direnv allow
```

---

## Manual Install

Without Nix, copy manually (based on mode):

**Setup/Build modes:**
1. `agents/` → `.claude/agents/` (select agents for mode)
2. `hooks/` → `.claude/hooks/`
3. `skills/alto-protocol/`, `skills/alto-feature-setup/`, `skills/alto-configure/`, `skills/scope-discipline/` → `.claude/skills/`
4. `templates/CLAUDE.md.setup` or `templates/CLAUDE.md.build` → `CLAUDE.md`
5. Create `runs/` structure
6. Create `.claude/settings.json`

**Dev mode:**
1. `agents/alto-dev.md` → `.claude/agents/`
2. `hooks/changelog-check.py` → `.claude/hooks/`
3. `skills/alto-dev-guide/`, `skills/writing-alto-skills/` → `.claude/skills/`
4. `templates/CLAUDE.md.dev` → `CLAUDE.md`

---

## License

MIT

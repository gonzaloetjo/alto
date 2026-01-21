# ALTO Operations Guide

Reference guide for running, configuring, and troubleshooting ALTO.

---

## Commands

| Command | Description |
|---------|-------------|
| `alto` | Main entry point. Resumes current mode, sends "hi" if no args |
| `alto dev/build/setup` | Switch to specified mode and start Claude |
| `alto-status` | Show current status (phase, branch, orchestrator mode) |
| `alto-switch <mode>` | Switch orchestrator mode (called by `alto <mode>`) |
| `alto-new-run` | Create new run branch, reset state to ARCHITECTURE |
| `alto-clean` | Clean run artifacts (tasks, pending.json) |
| `alto-nuke` | Full reset (removes .claude/, runs/, CLAUDE.md, objective.md) |
| `alto-feature` | Quick guide for starting a new feature |
| `alto-update` | Force update ALTO to latest version |
| `alto-init-test` | Create test project pointing to local ALTO (dev only) |

**Usage:**
```bash
direnv allow        # Activate environment
alto                # Start Claude (resumes session)
alto dev            # Switch to dev mode and start Claude
alto-status         # Check state
alto-update         # Update ALTO to latest version
```

---

## Configuration

### Configuration Types

| Type | Location | When Applied | Changed By |
|------|----------|--------------|------------|
| **Dynamic** | `alto.json` | Immediately | Orchestrator or user |
| **Static** | `devenv.nix` | On `direnv reload` | User edits file |

### alto.json (Dynamic)

Edit mid-session without reloading:

```json
{
  "version": 1,
  "arbiter": {
    "max_lines_changed_without_human": 2000,
    "max_files_changed_without_human": 50,
    "token_checkpoint_interval": 100000,
    "task_checkpoint_interval": 3,
    "high_risk_bash_prefixes": ["rm -rf /", "sudo rm", "dd if=", "mkfs", "> /dev/"]
  },
  "planning": {
    "require_approval": true,
    "replan_strategy": "auto",
    "fixed_batch_size": 5,
    "architect_model": "opus",
    "planner_model": "opus"
  },
  "verification": {
    "*.ts": { "typecheck": "pnpm type:check" },
    "*.tsx": { "typecheck": "pnpm type:check", "lint": "pnpm lint" },
    "*.py": { "test": "pytest" }
  }
}
```

### devenv.nix (Static)

Requires `direnv reload` after changes:

```nix
{ pkgs, ... }:
{
  alto = {
    enable = true;
    orchestrator = "setup";  # "setup" | "build" | "dev"

    arbiter = {
      maxLinesChanged = 2000;
      maxFilesChanged = 50;
      tokenCheckpointInterval = 100000;
      taskCheckpointInterval = 3;
    };

    permissions = {
      profile = "supervised";  # autonomous | supervised | locked
      allowBash = [ "ls" "cat" "grep" "find" "pwd" ];
      askBash = [ "git" "npm" "make" "docker" ];
      denyBash = [ "rm -rf" "sudo" "git push -f" ];
      denyRead = [ ".env" "secrets/**" "**/*.pem" ];
    };

    verification = {
      typecheck.enable = true;
      typecheck.command = "pnpm type:check";
      lint.enable = true;
      lint.command = "pnpm lint";
      test.enable = true;
      test.command = "npm test -- --related";
    };

    planning = {
      requireApproval = true;
      replanStrategy = "auto";  # auto | fixed | none
      fixedBatchSize = 5;
      architectModel = "opus";
      plannerModel = "opus";
    };
  };
}
```

### All Options

| Option | Default | Description |
|--------|---------|-------------|
| `orchestrator` | `"setup"` | Mode: `"setup"`, `"build"`, or `"dev"` |
| `arbiter.enable` | `true` | Enable human review gates |
| `arbiter.maxLinesChanged` | `2000` | Block threshold for lines |
| `arbiter.maxFilesChanged` | `50` | Block threshold for files |
| `arbiter.tokenCheckpointInterval` | `100000` | Checkpoint every N tokens |
| `arbiter.taskCheckpointInterval` | `3` | Checkpoint every N tasks |
| `planning.requireApproval` | `true` | Gate architecture approval |
| `planning.replanStrategy` | `"auto"` | `auto`, `fixed`, or `none` |
| `planning.fixedBatchSize` | `5` | Batch size when strategy = `fixed` |
| `planning.architectModel` | `"opus"` | Model for architecture phase |
| `planning.plannerModel` | `"opus"` | Model for planner agent |
| `permissions.profile` | `"supervised"` | `autonomous`, `supervised`, or `locked` |
| `verification.typecheck.enable` | `false` | Auto-run typecheck after TS edits |
| `verification.lint.enable` | `false` | Auto-run linter after edits |
| `verification.test.enable` | `false` | Auto-run tests after test file edits |
| `verification.custom` | `[]` | Custom verification hooks |

---

## Directory Structure

```
CLAUDE.md                    # Orchestrator protocol (copied from template)
ARCHITECTURE.md              # Design model for humans
AI-CONTEXT.md                # Full context for AI agents
alto.json                    # Dynamic config (arbiter, planning, verification)
objective.md                 # Project goals and requirements
docs/                        # Implementation docs

templates/
├── CLAUDE.md.setup          # Setup orchestrator protocol
├── CLAUDE.md.build          # Build orchestrator protocol
└── CLAUDE.md.dev            # Dev orchestrator protocol

agents/
├── alto-planner.md          # Task generation
├── alto-feature-finder.md   # Codebase analysis
├── alto-backend.md          # Backend implementation
├── alto-frontend.md         # Frontend implementation
├── alto-docs.md             # Documentation
├── alto-gitops.md           # Git operations
├── alto-qa.md               # Testing
├── alto-reviewer.md         # Code review
├── alto-arbiter.md          # Checkpoint auditor
├── alto-dev.md              # ALTO development
└── code-simplifier.md       # Code refinement

hooks/
├── usage-record.py          # Token tracking (Stop/SubagentStop)
├── tool-record.py           # Tool invocation logging (PostToolUse)
├── permission-record.py     # Permission request logging
├── changelog-check.py       # Blocks commit without CHANGELOG
├── session-start.py         # Session initialization
├── session-summary.py       # Session summary generation
├── arbiter-scheduler.py     # Triggers arbiter on thresholds (build)
├── handoff-template.py      # Auto-creates handoff template (build)
├── handoff-validate.py      # Validates handoff sections (build)
├── task-validate.py         # Validates task frontmatter (build)
├── phase-validate.py        # Validates phase transitions (build)
├── review-validate.py       # Validates reviewer output (build)
└── verify-dynamic.py        # Dynamic verification (build)

skills/
├── alto-protocol/           # Task/state/handoff formats
├── alto-feature-setup/      # Interactive feature setup
├── alto-configure/          # Configuration procedures
├── alto-switch/             # Mode switching
├── handoff-writing/         # Handoff format (build)
├── task-writing/            # Task format (build)
├── review-writing/          # Review format (build)
├── scope-discipline/        # Prevent over-engineering
├── alto-dev-guide/          # Dev mode documentation
└── writing-alto-skills/     # Skill authoring (dev)

.claude/
└── settings.json            # Project permissions + hooks

runs/
├── orchestrator.json        # Current mode
├── milestones.md            # High-level steps (build)
├── decisions.md             # Architectural choices (build)
├── plan.md                  # Detailed batch plan
├── state.json               # Current task + phase + role
├── tasks/                   # task-XXX.md files
├── handoffs/                # task-XXX.md outputs
├── review/                  # task-XXX-review.md files
├── usage/                   # usage.jsonl (tokens)
├── tools/                   # usage.jsonl (tool calls)
├── permissions/             # requests.jsonl
├── arbiter/                 # Checkpoint system
│   ├── state.json
│   ├── pending.json
│   ├── decision.json
│   └── checkpoints/
└── notes.md                 # Blocking notes
```

---

## Permissions

### Three-Tier System

| Tier | Behavior | Example |
|------|----------|---------|
| **allow** | Auto-approved | `ls`, `cat`, `grep` |
| **ask** | Prompts user | `git commit`, `npm install` |
| **deny** | Always blocked | `rm -rf`, `sudo`, `git push -f` |

**Precedence:** deny > ask > allow (deny always wins)

### Permission Profiles

| Profile | Default Mode | Use Case |
|---------|--------------|----------|
| `autonomous` | acceptEdits | Trusted environments, fast iteration |
| `supervised` | default | Normal development (recommended) |
| `locked` | plan | Untrusted code, security-sensitive |

### Per-Agent Permissions

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

## Troubleshooting

### Hook Errors

All hooks use `hook_utils.py` for consistent error handling:

```python
from hook_utils import safe_hook

@safe_hook("my-hook")
def main():
    # Hook logic - errors are caught and logged
    pass
```

**Behavior:**
- Errors logged to `runs/errors.jsonl` (not silent failures)
- Hook fails gracefully (returns exit 0, doesn't crash Claude Code)
- User-friendly message to stderr

**Error Log Format:**
```jsonl
{"timestamp":"2026-01-13T10:00:00","hook":"tool-record","error_type":"KeyError","error_message":"missing key","traceback":"..."}
```

### Health Check

`session-start` runs health checks on startup:
- Detects missing `objective.md` or unfilled template
- Reports recent errors in `runs/errors.jsonl`
- Validates state.json structure

### Common Issues

| Issue | Solution |
|-------|----------|
| ALTO not starting | Run `alto-update` to force refresh |
| State stuck | Check `runs/state.json`, delete `runs/arbiter/pending.json` |
| Hooks not running | Check `.claude/settings.json` hook definitions |
| Permission denied | Check `permissions` in `devenv.nix` |
| Old version | Run `alto-update` |

### Reload Commands

```bash
# After editing devenv.nix
direnv reload

# Or re-enter directory
cd .. && cd -

# Force full refresh
alto-update
```

---

## Git Workflow

### Branch Lifecycle

| Branch | Purpose | Merge |
|--------|---------|-------|
| `main` | Stable code | Human decision |
| `run/001` | Feature run | Squash merge when complete |
| `run/002` | Next feature | Same |

### Cleanup (Human Task)

- **Merge** — human decides when ready for main (squash recommended)
- **Delete** — after merging, delete the run branch
- **Abandon** — force-delete incomplete runs

---

## Token Tracking

Token usage is captured out-of-band via Claude Code hooks:

- `Stop` and `SubagentStop` trigger `usage-record.py`
- Records stored in `runs/usage/usage.jsonl`
- Tagged with current `task_id` and role from `runs/state.json`

---

## Manual Installation

Without Nix, copy manually based on mode:

### Setup/Build Modes

1. `agents/` → `.claude/agents/` (select agents for mode)
2. `hooks/` → `.claude/hooks/`
3. `skills/alto-protocol/`, `skills/alto-feature-setup/`, `skills/alto-configure/`, `skills/scope-discipline/` → `.claude/skills/`
4. `templates/CLAUDE.md.setup` or `templates/CLAUDE.md.build` → `CLAUDE.md`
5. Create `runs/` structure
6. Create `.claude/settings.json`

### Dev Mode

1. `agents/alto-dev.md` → `.claude/agents/`
2. `hooks/changelog-check.py` → `.claude/hooks/`
3. `skills/alto-dev-guide/`, `skills/writing-alto-skills/` → `.claude/skills/`
4. `templates/CLAUDE.md.dev` → `CLAUDE.md`

---

## Using direnv

For automatic environment activation:

```bash
# After installing direnv (https://direnv.net)
direnv allow
```

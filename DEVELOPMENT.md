# ALTO Development Guide

Notes for working on ALTO itself.

## Getting Started

Use the `alto-dev` agent which has access to:
- Read, Write, Edit, Grep, Glob - full file access
- Bash - run commands, git, testing
- WebFetch - fetch external documentation

The agent reads `.claude/skills/alto-dev-guide/SKILL.md` first, which contains:
- Documentation URLs for devenv and Claude Code
- Quick reference for common patterns
- ALTO file map
- Testing workflows

The **devenv MCP** is always available for package search and config generation.

## Key Implementation Details

### SessionStart Hook

`hooks/session-start.py`:
- Creates `objective.md` template if missing
- Detects NEW_PROJECT (template placeholders like `[Feature Name]`) vs real content
- Injects `[ALTO: NEW_PROJECT]` or `[ALTO: phase=X, ...]` signal
- Claude reads this signal to decide startup flow (see CLAUDE.md Startup section)

### Native Devenv Pattern

- Module is `devenv.nix` at repo root
- Consumers use `flake: false` + `imports: [alto]` in devenv.yaml
- No flakes required for consumers
- See https://devenv.sh/composing-using-imports/

### Deploy Mechanism

`tasks."alto:deploy"` runs before shell entry:
1. Copies hooks (`hooks/*.py`) to `.claude/hooks/`
2. Copies skills to `.claude/skills/`
3. Creates `runs/` directory structure
4. Initializes `state.json`, `planning-config.json`, arbiter config
5. Writes `CLAUDE.md` from template

### Agent Configuration

Agents defined in `devenv.nix` under `claude.code.agents`:
```nix
claude.code.agents.<name> = {
  description = "...";
  tools = [ "Read" "Edit" "Bash" ];
  model = "opus";  # or "sonnet"
  prompt = readAgentPrompt "<name>";  # reads from agents/<name>.md
};
```

Agent prompts live in `agents/*.md` with YAML frontmatter.

### Hook Configuration

Hooks defined in `devenv.nix` under `claude.code.hooks`:
```nix
claude.code.hooks.<name> = {
  hookType = "SessionStart";  # PostToolUse, Stop, SubagentStop, etc.
  matcher = "Bash";           # for PostToolUse
  command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/script.py";
};
```

Hook scripts receive JSON on stdin, print to stdout (for SessionStart context).

### Debug Mode & Event Logging

Enable verbose event logging for testing and meta-development:

```nix
alto.debug = true;
```

**When disabled (default):** No extra logging. Claude Code's built-in OpenTelemetry handles generic metrics (tokens, tool calls, etc.).

**When enabled:** ALTO-specific events logged to `runs/logs/events.jsonl`:
- `session_start` / `session_end` - Session lifecycle
- `handoff` - Agent handoffs with success/failure

Query logs with `alto-logs`:
```bash
alto-logs              # Show last 20 events
alto-logs --metrics    # Aggregated stats
alto-logs --type handoff --last 50
alto-logs --raw | jq   # Pipe to jq
```

**Note:** Generic tool usage is NOT duplicated to events.jsonl - use Claude Code's `/cost` command or enable OTel export for that data.

### Skill Schema

Skills use YAML frontmatter with structured fields:

```yaml
---
name: skill-name
type: discipline | technique | reference
triggers:
  - editing path/to/file.md
  - running /command-name
---
```

| Field | Purpose |
|-------|---------|
| `type` | `discipline` (rules), `technique` (how-to), `reference` (lookup) |
| `triggers` | Concrete file paths or commands (NOT workflow summaries) |

**Word limits by type:** discipline <300, technique <500, reference <800

**Validation:** `hooks/skill-validate.py` checks on Write/Edit to `skills/*/SKILL.md`.

See `.claude/skills/writing-alto-skills/SKILL.md` for full schema documentation.

## Testing Changes

**WARNING:** Do NOT run `devenv shell` in the ALTO repo itself. It creates consumer agents in `.claude/` that conflict with tracked dev agents.

### Test Layers

| Layer | Command | Purpose | Speed |
|-------|---------|---------|-------|
| Syntax | `alto-validate` | Nix/Python/Bash syntax, frontmatter | <5s |
| Unit | `pytest tests/` | Hook utilities, validators | ~10s |
| Protocol | `alto-test-multi --scenario X` | Multi-turn orchestrator flows | ~$0.08/turn |

### Quick Syntax Checks

```bash
# Run all syntax checks
devenv shell -- alto-validate

# Or manually:
nix-instantiate --parse devenv.nix > /dev/null && echo "OK"
python3 -m py_compile hooks/*.py && echo "OK"
```

### Protocol Testing (Multi-Turn)

Tests orchestrator protocols by simulating human interaction across multiple conversation turns. Each test creates an isolated temp directory, runs Claude with `--print`, and verifies responses/state.

**From ALTO source directory:**

```bash
# Run ALL scenarios (full test suite)
devenv shell -- alto-test-multi --all --verbose

# Run a single scenario
devenv shell -- alto-test-multi --scenario build-blocked-recovery --verbose

# Keep test directory after run (for debugging)
devenv shell -- alto-test-multi --scenario setup-new-project --keep --verbose

# JSON output (for CI)
devenv shell -- alto-test-multi --all --json
```

**Available Scenarios:**

| Scenario | Turns | Cost | What It Tests |
|----------|-------|------|---------------|
| `setup-new-project` | 4 | ~$0.32 | Full setup flow: welcome → "Set up project" → describe project → write objective.md |
| `build-simple-feature` | 2 | ~$0.16 | Build orchestrator executes a simple feature from pre-defined objective.md |
| `build-phase-transitions` | 3 | ~$0.24 | State machine validation: plan → implement → verify, checks all phase transitions are valid |
| `build-handoff-structure` | 2 | ~$0.16 | Verifies handoff files have required sections (## Summary, etc.) and minimum length |
| `setup-configure-flow` | 3 | ~$0.24 | Configuration path: has objective → "Configure ALTO" → "Thresholds" → verify Write tool used |
| `build-blocked-recovery` | 2 | ~$0.16 | Pre-seeds BLOCKED state, verifies orchestrator detects and recovers from blocked state |

**Full suite:** ~16 turns, ~$1.30

See `tests/scenarios/multi-turn/README.md` for scenario YAML format and all assertion types.

### Local Integration Test

Create a **separate directory** to test local changes:

```bash
mkdir -p /tmp/alto-test && cd /tmp/alto-test
git init

# Point to local ALTO
cat > devenv.yaml << 'EOF'
inputs:
  nixpkgs:
    url: github:cachix/devenv-nixpkgs/rolling
  alto:
    url: path:/path/to/your/alto
    flake: false
EOF

cat > devenv.nix << 'EOF'
{ pkgs, lib, inputs, ... }:
{
  imports = [ "${inputs.alto}/devenv.nix" ];
  # ALTO active by default, switch modes with: alto.orchestrator = "build";
}
EOF

# Test
devenv shell -- alto-status
```

### Fresh Install Test (from GitHub)

```bash
mkdir -p /tmp/alto-fresh && cd /tmp/alto-fresh
nix flake init -t github:gonzaloetjo/alto --refresh
devenv shell

# Verify
ls -la .claude/agents/   # Should have agent files
ls -la .claude/hooks/    # Should have .py files
ls -la runs/             # Should have state.json
cat CLAUDE.md            # Should have protocol
```

### Verify Hooks

```bash
# Start claude, then check logs
cat runs/sessions/starts.jsonl
```

## Common Issues

| Problem | Solution |
|---------|----------|
| jq escaping in nix | Use `echo "$(jq ...)"` not complex jq strings |
| Changes not applied | Run `devenv shell` again |
| Remote changes not applied | Use `--refresh` flag |
| Hook not running | Check `.claude/settings.json` has hook |
| Files read-only | Expected - nix store symlinks |

### Nix String Escaping

In `''` strings:
- `''$` → `$` (escape dollar)
- `'''` → `''` (escape quotes)
- `\n` → literal `\n` (not newline) - use actual newlines

## Issues

See [GitHub Issues](https://github.com/gonzaloetjo/alto/issues) or run `gh issue list`.

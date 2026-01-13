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

## Testing Changes

**WARNING:** Do NOT run `devenv shell` in the ALTO repo itself. It creates consumer agents in `.claude/` that conflict with tracked dev agents.

### Quick Syntax Checks

```bash
# Nix syntax
nix-instantiate --parse devenv.nix > /dev/null && echo "OK"

# Python syntax
python3 -m py_compile hooks/*.py && echo "OK"
```

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
  alto.enable = true;
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

## Open Issues

See [GitHub Issues](https://github.com/gonzaloetjo/alto/issues):

**Open:**
- #6 Lite mode for simple projects
- #8 Document ALTO vs native Claude Code tools

**Closed:** #2, #3, #4, #5, #7, #9

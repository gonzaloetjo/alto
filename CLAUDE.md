# ALTO Development

You are developing ALTO itself - a multi-agent orchestration system for Claude Code.

No `devenv shell` needed - just run `claude` directly.

## On Session Start

Use the `alto-dev` agent for most development tasks. It has:
- Full file access (Read, Write, Edit, Grep, Glob)
- Bash for commands, git, testing
- WebFetch for external documentation

The agent reads `.claude/skills/alto-dev-guide/SKILL.md` which contains:
- Documentation URLs for devenv and Claude Code
- Quick reference patterns
- Testing workflows

## Key Files

| File | Purpose |
|------|---------|
| `devenv.nix` | Main ALTO module - options, agents, hooks, scripts |
| `agents/*.md` | Agent prompts (YAML frontmatter + markdown) |
| `hooks/*.py` | Hook implementations |
| `skills/*/SKILL.md` | Skill content |
| `templates/CLAUDE.md.template` | Orchestrator protocol (for consumer projects) |
| `DEVELOPMENT.md` | Development guide |
| `CHANGELOG.md` | Recent changes |
| `ARCHITECTURE.md` | Design documentation |

## Workflow

1. **Check issues** - `gh issue list` for open work
2. **Use alto-dev** - For implementation tasks
3. **Test changes** - See DEVELOPMENT.md for workflows
4. **Commit** - Conventional commits, no co-author line

**Note:** The `session-summary` hook automatically reminds about CHANGELOG when key files are modified without updating it.

## Testing

**WARNING:** Do NOT run `devenv shell` in the ALTO repo itself. It creates consumer agents in `.claude/` that conflict with tracked dev agents.

### Quick syntax checks (no devenv needed)

```bash
# Nix syntax
nix-instantiate --parse devenv.nix > /dev/null && echo "OK"

# Python syntax
python3 -m py_compile hooks/*.py && echo "OK"
```

### Local integration test (separate directory)

```bash
# Create test directory
mkdir -p /tmp/alto-test && cd /tmp/alto-test
git init

# Create devenv.yaml pointing to local ALTO
cat > devenv.yaml << 'EOF'
inputs:
  nixpkgs:
    url: github:cachix/devenv-nixpkgs/rolling
  alto:
    url: path:/home/genge/dev-ash/foundry-nodevenv/cholitas/alto-2
    flake: false
EOF

# Create devenv.nix importing local module
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

### Fresh install test (from GitHub)

```bash
mkdir -p /tmp/alto-fresh && cd /tmp/alto-fresh
nix flake init -t github:gonzaloetjo/alto --refresh
devenv shell
```

## Session End

Before ending a session, create `docs/dev/session-YYYY-MM-DD.md` with:
- Issues closed (with commits and savings)
- Remaining issues
- Key decisions made

See `docs/dev/session-2026-01-13.md` for example format.

## Issues

See [github.com/gonzaloetjo/alto/issues](https://github.com/gonzaloetjo/alto/issues) for open issues.

Run `gh issue list` to check from CLI.

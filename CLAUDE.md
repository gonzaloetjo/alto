# ALTO Development

You are developing ALTO itself - a multi-agent orchestration system for Claude Code.

## On Session Start

Use the `alto-dev` agent for most development tasks. It has:
- Full file access (Read, Write, Edit, Grep, Glob)
- Bash for commands, git, testing
- WebFetch for external documentation

The agent reads `.claude/skills/alto-dev-guide/SKILL.md` which contains:
- Documentation URLs for devenv and Claude Code
- Quick reference patterns
- Testing workflows

The **devenv MCP** is available for package search and config help.

## Key Files

| File | Purpose |
|------|---------|
| `devenv.nix` | Main ALTO module - options, agents, hooks, scripts |
| `agents/*.md` | Agent prompts (YAML frontmatter + markdown) |
| `hooks/*.py` | Hook implementations |
| `skills/*/SKILL.md` | Skill content |
| `templates/CLAUDE.md.template` | Orchestrator protocol (for consumer projects) |
| `docs/DEVELOPMENT.md` | Development guide |
| `CHANGELOG.md` | Recent changes |
| `ARCHITECTURE.md` | Design documentation |

## Workflow

1. **Check issues** - `gh issue list` for open work
2. **Use alto-dev** - For implementation tasks
3. **Test changes** - See docs/DEVELOPMENT.md for workflows
4. **Commit** - Include `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>`

## Testing

```bash
# Fresh install test
mkdir /tmp/test && cd /tmp/test
nix flake init -t github:gonzaloetjo/alto --refresh
devenv shell
```

## Open Issues

- #2 Remove alto-enforcer
- #3 Simplify alto-recorder
- #4 Simplify alto-reviewer
- #5 Hook error handling
- #6 Lite mode
- #7 Handoff validation
- #8 Document ALTO vs native tools
- #9 Branch cleanup

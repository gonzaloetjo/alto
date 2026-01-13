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

## Session End

Before ending a session, create `docs/session-YYYY-MM-DD.md` with:
- Issues closed (with commits and savings)
- Remaining issues
- Key decisions made

See `docs/session-2026-01-13.md` for example format.

## Open Issues

- #4 Simplify alto-reviewer
- #5 Hook error handling
- #6 Lite mode
- #7 Handoff validation
- #8 Document ALTO vs native tools
- #9 Branch cleanup

**Closed:** #2 (enforcer), #3 (recorder)

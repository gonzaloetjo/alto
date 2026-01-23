# Claude Code Knowledge Base

> AI-optimized documentation for Claude Code extensibility. Start here.

## Navigation

| Topic | File | When to Read |
|-------|------|--------------|
| Architecture | [overview.md](overview.md) | Understanding how features interact |
| Built-in Tools | [tools.md](tools.md) | Available tool reference |
| Settings | [settings.md](settings.md) | Configuration and permissions |
| Memory Files | [memory.md](memory.md) | CLAUDE.md format and patterns |
| Rules | [rules.md](rules.md) | Modular instruction files |
| Commands | [commands.md](commands.md) | Custom slash commands |
| Skills | [skills.md](skills.md) | Reusable capabilities |
| Agents | [agents.md](agents.md) | Custom subagents |
| Hooks | [hooks.md](hooks.md) | Event scripting |
| MCP Servers | [mcp.md](mcp.md) | External service connections |
| Permissions | [permissions.md](permissions.md) | Permission modes and patterns |
| Plan Mode | [plan-mode.md](plan-mode.md) | Read-only analysis mode |
| Output Styles | [output-styles.md](output-styles.md) | Behavior customization |
| Quick Reference | [quick-reference.md](quick-reference.md) | Cheat sheet |

---

## Feature Matrix

| Feature | Context Impact | When Loaded | Activation Model |
|---------|---------------|-------------|------------------|
| Settings | Config only | Pre-session | Automatic |
| CLAUDE.md | Adds knowledge | Session start | Automatic |
| Rules | Adds knowledge (path-filtered) | Session start | Deterministic |
| Commands | Becomes your prompt | On `/command` | Explicit only |
| Skills | Adds knowledge OR isolated | On invoke/suggest | Soft or Strong |
| Agents | Isolated context | On delegation | Auto or explicit |
| Hooks | Side effects only | Per tool call | Automatic (matcher) |
| MCP | Adds tools | Session start | Automatic |
| Output Styles | **Replaces** system prompt | On activation | Explicit only |
| Plan Mode | Restricts tools | On toggle | Explicit only |

---

## Key Insight

> **Rules = suggestions. Hooks = enforcement.**
>
> A rule saying "don't edit .env" is parsed by Claude and *maybe* followed.
> A PreToolUse hook blocking .env edits *always* runs and blocks the operation.

---

## Feature Selection Guide

| Need | Use | Why |
|------|-----|-----|
| Always-active constraint | Rule | Deterministic, always in context |
| On-demand procedure | Skill | Lazy loading, saves baseline context |
| Must enforce (block/log) | Hook | Always executes, can't be ignored |
| User-triggered shortcut | Command | Explicit invocation, simple template |
| Isolated specialist | Agent | Separate context, tool restrictions |
| External service | MCP Server | Database, API, service integration |
| Change core behavior | Output Style | Replaces system prompt |
| Safe exploration | Plan Mode | Blocks all modifications |

---

## Skill Activation Model

| Type | Description | When to Use |
|------|-------------|-------------|
| **Soft** | Claude *could* auto-invoke via description matching | Context-dependent procedures |
| **Strong** | Explicitly called (`/skill`) or referenced in agent .md | Predictable workflows |
| **Disabled** | Set `disable-model-invocation: true` | Dangerous operations (deploy, delete) |

---

## File Locations Reference

| File | Scope | Shared |
|------|-------|--------|
| `.claude/settings.json` | Project (team) | Yes |
| `.claude/settings.local.json` | Personal project | No |
| `~/.claude/settings.json` | User global | No |
| `./CLAUDE.md` | Project | Yes |
| `./CLAUDE.local.md` | Personal project | No |
| `~/.claude/CLAUDE.md` | User global | No |
| `.claude/rules/*.md` | Project | Yes |
| `~/.claude/rules/*.md` | User | No |
| `.claude/commands/*.md` | Project | Yes |
| `~/.claude/commands/*.md` | User | No |
| `.claude/skills/*/SKILL.md` | Project | Yes |
| `~/.claude/skills/*/SKILL.md` | User | No |
| `.claude/agents/*.md` | Project | Yes |
| `~/.claude/agents/*.md` | User | No |
| `.mcp.json` | Project | Yes |
| `~/.claude.json` | User | No |

---

## Related

- [overview.md](overview.md) - Context flow and lifecycle diagrams
- [quick-reference.md](quick-reference.md) - Single-page cheat sheet

# Claude Code > Quick Reference

> Single-page cheat sheet for all Claude Code extensibility features.

---

## File Locations

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Team configuration |
| `.claude/settings.local.json` | Personal overrides (gitignored) |
| `~/.claude/settings.json` | User global settings |
| `./CLAUDE.md` | Project memory |
| `./CLAUDE.local.md` | Personal memory (gitignored) |
| `~/.claude/CLAUDE.md` | User global memory |
| `.claude/rules/*.md` | Modular rules |
| `.claude/commands/*.md` | Slash commands |
| `.claude/skills/*/SKILL.md` | Skills |
| `.claude/agents/*.md` | Subagents |
| `.claude/output-styles/*.md` | Output styles |
| `.mcp.json` | MCP servers |

---

## Feature Quick Guide

| Need | Use | Why |
|------|-----|-----|
| Project context | CLAUDE.md | Always loaded |
| Coding standards | Rules | Path-filtered, modular |
| Quick prompt shortcut | Command | Explicit invocation |
| Complex procedure | Skill | Auto-discoverable |
| Isolated specialist | Agent | Separate context |
| Block/log tool calls | Hook | Enforcement |
| External services | MCP | Database, API access |
| Change Claude's role | Output Style | Replaces system prompt |
| Safe exploration | Plan Mode | Blocks modifications |

---

## Frontmatter Reference

### Commands (`.claude/commands/*.md`)

```yaml
---
description: Shown in /help
argument-hint: [arg1] [arg2]
allowed-tools: Bash(git:*), Read
model: haiku
context: fork
agent: code-simplifier
disable-model-invocation: true
---
```

### Skills (`.claude/skills/*/SKILL.md`)

```yaml
---
name: skill-name
description: When to use (keyword-rich)
allowed-tools: Read, Grep, Glob, Bash
model: opus
context: fork
agent: general-purpose
user-invocable: true
disable-model-invocation: false
---
```

### Agents (`.claude/agents/*.md`)

```yaml
---
name: agent-name
description: When to delegate
tools: Read, Grep, Glob
disallowedTools: Write, Edit, Bash
model: sonnet
permissionMode: plan
skills: skill1, skill2
---
```

### Rules (`.claude/rules/*.md`)

```yaml
---
paths:
  - "src/**/*.ts"
  - "test/**/*.spec.ts"
---
```

### Output Styles (`.claude/output-styles/*.md`)

```yaml
---
name: Display Name
description: Shown in menu
keep-coding-instructions: false
---
```

---

## Permission Patterns

```
Tool                    # All uses
Tool(pattern)           # Exact match
Tool(prefix:*)          # Starts with
Tool(*suffix)           # Ends with
Tool(./path/**)         # Path glob
```

### Examples

```json
{
  "allow": [
    "Bash(npm:*)",
    "Bash(git status:*)",
    "Read(./src/**)",
    "Edit(./src/**/*.ts)"
  ],
  "deny": [
    "Bash(rm -rf:*)",
    "Read(.env*)"
  ]
}
```

---

## Hook Events

| Event | When | Exit 2 = |
|-------|------|----------|
| `PreToolUse` | Before tool | Block |
| `PostToolUse` | After tool | (ignored) |
| `PermissionRequest` | Permission prompt | Deny |
| `UserPromptSubmit` | User input | (n/a) |
| `Notification` | Needs attention | (n/a) |
| `Stop` | Response complete | (n/a) |
| `SubagentStop` | Subagent done | (n/a) |
| `SessionStart` | Session begins | (n/a) |
| `SessionEnd` | Session ends | (n/a) |

### Hook Template

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "./script.sh"}
        ]
      }
    ]
  }
}
```

---

## MCP Server Types

### HTTP

```json
{
  "type": "http",
  "url": "https://api.example.com/mcp",
  "headers": {"Authorization": "Bearer ${TOKEN}"}
}
```

### Stdio

```json
{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@package/name"],
  "env": {"VAR": "${VALUE}"}
}
```

---

## Permission Modes

| Mode | Edits | Bash | Description |
|------|-------|------|-------------|
| `default` | Ask | Ask | Normal |
| `acceptEdits` | Auto | Ask | Fast editing |
| `dontAsk` | Auto | Auto | Minimal prompts |
| `bypassPermissions` | Auto | Auto | Skip all |
| `plan` | Block | Block | Read-only |

---

## Dynamic Content (Commands/Skills)

| Syntax | Purpose | Example |
|--------|---------|---------|
| `$ARGUMENTS` | All args | `Fix $ARGUMENTS` |
| `$1`, `$2` | Positional | `Issue #$1` |
| `` !`cmd` `` | Bash output | `` !`git status` `` |
| `@path` | File content | `@README.md` |

---

## Path Glob Patterns

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All .ts files |
| `src/**/*` | Everything in src/ |
| `*.md` | Root markdown only |
| `{a,b}/**` | a/ or b/ |
| `!**/node_modules/**` | Exclude |

---

## Key Insights

> **Rules = suggestions. Hooks = enforcement.**

> **Skills with `context: fork` run in agents.**

> **Warn hook messages only reach user, not Claude.**

> **Agents always run isolated; skills optionally.**

---

## Activation Comparison

| Feature | When Loaded | Auto-Trigger? |
|---------|-------------|---------------|
| Settings | Pre-session | Always |
| CLAUDE.md | Session start | Always |
| Rules | Session start | Always |
| Commands | On `/cmd` | No |
| Skills | On suggest/invoke | Optional |
| Agents | On delegation | Optional |
| Hooks | Per tool call | Always |
| Output Styles | On activate | No |

---

## Tool Availability

| Tool | Default | Plan Mode |
|------|---------|-----------|
| Read | Yes | Yes |
| Glob | Yes | Yes |
| Grep | Yes | Yes |
| Edit | Yes | **No** |
| Write | Yes | **No** |
| Bash | Yes | **No** |
| WebFetch | Yes | **No** |
| Task | Yes | Yes |

---

## Common Configurations

### Security-Focused

```json
{
  "permissions": {
    "deny": ["Bash(curl:*)", "Bash(wget:*)", "Read(.env*)"]
  },
  "sandbox": {"enabled": true}
}
```

### Read-Only Analysis

```json
{
  "permissions": {
    "deny": ["Write", "Edit", "Bash(git commit:*)"],
    "defaultMode": "plan"
  }
}
```

### Fast Development

```json
{
  "permissions": {
    "allow": ["Bash(npm:*)", "Bash(git:*)", "Edit", "Write"],
    "defaultMode": "acceptEdits"
  }
}
```

---

## Related Files

- [index.md](index.md) - Full navigation
- [overview.md](overview.md) - Architecture diagrams

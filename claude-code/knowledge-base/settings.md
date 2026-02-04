# Claude Code > Settings

> Configuration via `settings.json` files.

## File Locations

| File | Scope | Shared | Priority |
|------|-------|--------|----------|
| Managed settings | System-wide (IT deployed) | N/A | 1 (highest) |
| `.claude/settings.local.json` | Personal project | No (gitignored) | 2 |
| `.claude/settings.json` | Team project | Yes (committed) | 3 |
| `~/.claude/settings.json` | User global | No | 4 (lowest) |

---

## Permissions

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run:*)",
      "Bash(git commit:*)",
      "Read(./src/**)",
      "Edit(./src/**)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Write(./)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Read(.env)",
      "Read(.env.*)"
    ],
    "additionalDirectories": [
      "../shared-docs/",
      "../other-project/"
    ],
    "defaultMode": "acceptEdits"
  }
}
```

### Permission Rule Syntax

| Pattern | Matches |
|---------|---------|
| `Tool` | All uses of the tool |
| `Tool(pattern)` | Uses matching pattern |
| `Tool(prefix:*)` | Uses starting with prefix |
| `Tool(*suffix)` | Uses ending with suffix |
| `Tool(./path/**)` | Path glob patterns |

### Default Modes

| Mode | Behavior |
|------|----------|
| `default` | Ask for permission on most operations |
| `acceptEdits` | Auto-accept file edits, ask for others |
| `dontAsk` | Minimal prompts (still asks for dangerous ops) |
| `bypassPermissions` | Skip all prompts |
| `plan` | Research only, no edits |

---

## Sandbox

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["git", "docker"],
    "allowUnsandboxedCommands": true,
    "network": {
      "allowUnixSockets": ["~/.ssh/agent-socket"],
      "allowLocalBinding": true,
      "httpProxyPort": 8080,
      "socksProxyPort": 8081
    }
  }
}
```

---

## Model Configuration

```json
{
  "model": "claude-opus-4-5-20251101",
  "alwaysThinkingEnabled": true
}
```

| Model | Description |
|-------|-------------|
| `claude-opus-4-5-20251101` | Most capable |
| `claude-sonnet-4-20250514` | Balanced |
| `claude-haiku-4-5-20251001` | Fastest |
| `opusplan` | Opus for planning, Sonnet for execution |

---

## Environment Variables

```json
{
  "env": {
    "NODE_ENV": "development",
    "DEBUG": "true",
    "CUSTOM_VAR": "value"
  }
}
```

---

## Hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/validate-bash.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$FILE_PATH\""
          }
        ]
      }
    ]
  },
  "disableAllHooks": false,
  "allowManagedHooksOnly": false
}
```

---

## MCP Servers

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["memory", "github"],
  "disabledMcpjsonServers": ["filesystem"]
}
```

---

## Plugins

```json
{
  "enabledPlugins": {
    "code-simplifier@claude-plugins-official": true,
    "security-guidance@claude-plugins-official": true
  },
  "extraKnownMarketplaces": {
    "acme-tools": {
      "source": {
        "source": "github",
        "repo": "acme-corp/claude-plugins"
      }
    }
  }
}
```

---

## Attribution

```json
{
  "attribution": {
    "commit": "Co-Authored-By: Claude <noreply@anthropic.com>",
    "pr": "Generated with Claude Code"
  }
}
```

---

## Miscellaneous

```json
{
  "cleanupPeriodDays": 30,
  "plansDirectory": "~/.claude/plans",
  "showTurnDuration": true,
  "language": "english",
  "autoUpdatesChannel": "stable",
  "spinnerTipsEnabled": true,
  "terminalProgressBarEnabled": true,
  "respectGitignore": true
}
```

---

## Complete Example

### Team Settings (`.claude/settings.json`)

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run:*)",
      "Bash(npm test:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Read(./src/**)",
      "Read(./test/**)",
      "Edit(./src/**)",
      "Edit(./test/**)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Read(.env*)",
      "Read(./secrets/**)"
    ],
    "defaultMode": "acceptEdits"
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$FILE_PATH\" 2>/dev/null || true"
          }
        ]
      }
    ]
  },
  "attribution": {
    "commit": "Co-Authored-By: Claude <noreply@anthropic.com>"
  }
}
```

### Personal Overrides (`.claude/settings.local.json`)

```json
{
  "permissions": {
    "allow": [
      "Bash(my-custom-script:*)"
    ]
  },
  "env": {
    "MY_API_KEY": "personal-key-here"
  },
  "model": "claude-opus-4-5-20251101",
  "alwaysThinkingEnabled": true
}
```

---

## Settings Inheritance

Settings merge with this priority (highest to lowest):

1. **Managed** - System-wide policies (IT deployed)
2. **Command line** - CLI flags for current session
3. **Local** - `.claude/settings.local.json`
4. **Project** - `.claude/settings.json`
5. **User** - `~/.claude/settings.json`

Arrays are merged (combined), objects are deep-merged, primitives use highest priority.

---

## Related

- [permissions.md](permissions.md) - Permission modes in detail
- [hooks.md](hooks.md) - Hook configuration
- [mcp.md](mcp.md) - MCP server configuration

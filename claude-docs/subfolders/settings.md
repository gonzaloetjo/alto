# Claude Code Settings (`settings.json`)

Settings control Claude Code behavior, permissions, tools, and integrations. They use a hierarchical scope system where more specific settings override general ones.

## File Locations

| File | Scope | Shared | Priority |
|------|-------|--------|----------|
| Managed settings | System-wide (IT deployed) | N/A | 1 (highest) |
| `.claude/settings.local.json` | Personal project | No (gitignored) | 2 |
| `.claude/settings.json` | Team project | Yes (committed) | 3 |
| `~/.claude/settings.json` | User global | No | 4 (lowest) |

## Settings Categories

### Permissions

Control which tools and operations Claude can perform:

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

#### Permission Rule Syntax

| Pattern | Matches |
|---------|---------|
| `Tool` | All uses of the tool |
| `Tool(pattern)` | Uses matching pattern |
| `Tool(prefix:*)` | Uses starting with prefix |
| `Tool(*suffix)` | Uses ending with suffix |
| `Tool(./path/**)` | Path glob patterns |

#### Examples

```json
{
  "permissions": {
    "allow": [
      "Bash(npm:*)",           // Any npm command
      "Bash(git status:*)",    // git status only
      "Bash(forge test:*)",    // forge test commands
      "Read(./src/**)",        // Read anything in src/
      "Edit(./src/**/*.ts)",   // Edit TypeScript in src/
      "WebFetch(domain:api.example.com)"  // Specific domain
    ],
    "deny": [
      "Bash(rm -rf:*)",        // Block recursive delete
      "Bash(sudo:*)",          // Block sudo
      "Read(.env*)",           // Block env files
      "Read(./secrets/**)"     // Block secrets directory
    ]
  }
}
```

#### Default Mode

| Mode | Behavior |
|------|----------|
| `default` | Ask for permission on most operations |
| `acceptEdits` | Auto-accept file edits, ask for other ops |
| `dontAsk` | Minimal prompts (still asks for dangerous ops) |
| `bypassPermissions` | Skip all prompts |
| `plan` | Research only, no edits |

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "disableBypassPermissionsMode": "disable"
  }
}
```

### Sandbox

Isolate Claude's operations in a secure sandbox:

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
    },
    "enableWeakerNestedSandbox": false
  }
}
```

### Model Configuration

```json
{
  "model": "claude-opus-4-5-20251101",
  "alwaysThinkingEnabled": true
}
```

Available models:
- `claude-opus-4-5-20251101` (most capable)
- `claude-sonnet-4-20250514` (balanced)
- `claude-haiku-4-5-20251001` (fastest)

### Environment Variables

```json
{
  "env": {
    "NODE_ENV": "development",
    "DEBUG": "true",
    "CUSTOM_VAR": "value"
  }
}
```

### Hooks

Execute scripts on tool events:

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
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude' 'Needs input'"
          }
        ]
      }
    ]
  },
  "disableAllHooks": false,
  "allowManagedHooksOnly": false
}
```

See [hooks.md](hooks.md) for complete hook documentation.

### MCP Servers

Control Model Context Protocol server access:

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["memory", "github"],
  "disabledMcpjsonServers": ["filesystem"]
}
```

### Plugins

Enable/disable plugins:

```json
{
  "enabledPlugins": {
    "code-simplifier@claude-plugins-official": true,
    "security-guidance@claude-plugins-official": true,
    "building-secure-contracts@trailofbits": true
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

### Attribution

Customize commit and PR attribution:

```json
{
  "attribution": {
    "commit": "Co-Authored-By: Claude <noreply@anthropic.com>",
    "pr": "Generated with Claude Code"
  }
}
```

### Status Line

Custom status line display:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

### File Suggestions

Custom file suggestion behavior:

```json
{
  "fileSuggestion": {
    "type": "command",
    "command": "~/.claude/file-suggestion.sh"
  },
  "respectGitignore": true
}
```

### Miscellaneous

```json
{
  "cleanupPeriodDays": 30,
  "companyAnnouncements": [
    "Welcome to Acme Corp! Review docs at docs.acme.com"
  ],
  "plansDirectory": "~/.claude/plans",
  "showTurnDuration": true,
  "language": "english",
  "autoUpdatesChannel": "stable",
  "spinnerTipsEnabled": true,
  "terminalProgressBarEnabled": true
}
```

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
  },
  "enabledPlugins": {
    "code-simplifier@claude-plugins-official": true
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

### User Global Settings (`~/.claude/settings.json`)

```json
{
  "permissions": {
    "deny": [
      "Bash(sudo:*)",
      "Bash(rm -rf /*:*)"
    ]
  },
  "showTurnDuration": true,
  "spinnerTipsEnabled": true,
  "terminalProgressBarEnabled": true
}
```

## Use Case Examples

### Security-Focused Project

```json
{
  "permissions": {
    "allow": [
      "Read(./src/**)",
      "Edit(./src/**)",
      "Bash(npm run lint:*)",
      "Bash(npm test:*)"
    ],
    "deny": [
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(nc:*)",
      "Read(.env*)",
      "WebFetch"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true
  }
}
```

### Smart Contract Development

```json
{
  "permissions": {
    "allow": [
      "Bash(forge build:*)",
      "Bash(forge test:*)",
      "Bash(forge script:*)",
      "Bash(cast:*)",
      "Read(./src/**)",
      "Read(./test/**)",
      "Edit(./src/**)",
      "Edit(./test/**)"
    ],
    "deny": [
      "Bash(forge script --broadcast:*)"
    ]
  },
  "enabledPlugins": {
    "building-secure-contracts@trailofbits": true
  }
}
```

### Data Science Project

```json
{
  "permissions": {
    "allow": [
      "Bash(python:*)",
      "Bash(pip install:*)",
      "Bash(jupyter:*)",
      "Read(./data/**)",
      "Read(./notebooks/**)",
      "Write(./results/**)"
    ]
  },
  "env": {
    "PYTHONPATH": "./src"
  },
  "model": "claude-opus-4-5-20251101"
}
```

### Read-Only Analysis

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Grep",
      "Glob",
      "Bash(git log:*)",
      "Bash(git show:*)"
    ],
    "deny": [
      "Write",
      "Edit",
      "Bash(git commit:*)",
      "Bash(git push:*)"
    ],
    "defaultMode": "plan"
  }
}
```

## Settings Inheritance

Settings merge with this priority (highest to lowest):

1. **Managed** - System-wide policies (IT deployed)
2. **Command line** - CLI flags for current session
3. **Local** - `.claude/settings.local.json`
4. **Project** - `.claude/settings.json`
5. **User** - `~/.claude/settings.json`

Arrays are merged (combined), objects are deep-merged, primitives use highest priority.

## Tips

1. **Start restrictive**: Begin with minimal permissions, expand as needed
2. **Use local for secrets**: Keep API keys in `settings.local.json`
3. **Share team standards**: Commit `settings.json` with reasonable defaults
4. **Test hooks**: Verify hooks work before committing
5. **Document choices**: Add comments in code if settings need explanation

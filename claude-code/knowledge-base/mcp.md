# Claude Code > MCP

> Model Context Protocol server configuration via `.mcp.json`.

## File Locations

| File | Scope | Shared |
|------|-------|--------|
| `.mcp.json` (project root) | Project (team) | Yes (committed) |
| `~/.claude.json` | User global | No |

---

## Basic Structure

```json
{
  "mcpServers": {
    "server-name": {
      "type": "http|sse|stdio",
      ...configuration
    }
  }
}
```

---

## Server Types

### HTTP Server (Recommended)

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp",
      "headers": {
        "Authorization": "Bearer ${SENTRY_API_KEY}"
      }
    }
  }
}
```

### SSE Server (Legacy)

```json
{
  "mcpServers": {
    "legacy-service": {
      "type": "sse",
      "url": "https://mcp.example.com/sse",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

### Stdio Server (Local)

```json
{
  "mcpServers": {
    "database": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub"],
      "env": {
        "DB_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

---

## Environment Variable Expansion

Use `${VAR}` syntax in any string field:

```json
{
  "mcpServers": {
    "api-service": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}",
        "X-Custom-Header": "${CUSTOM_VALUE:-default}"
      }
    }
  }
}
```

| Syntax | Behavior |
|--------|----------|
| `${VAR}` | Expand variable |
| `${VAR:-default}` | Use default if unset |

---

## Common MCP Servers

### GitHub

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

### Sentry

```json
{
  "mcpServers": {
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp",
      "headers": {
        "Authorization": "Bearer ${SENTRY_AUTH_TOKEN}"
      }
    }
  }
}
```

### PostgreSQL (via dbhub)

```json
{
  "mcpServers": {
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub"],
      "env": {
        "PGCONNECTIONSTRING": "${DATABASE_URL}"
      }
    }
  }
}
```

### Filesystem Access

```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@anthropics/mcp-filesystem",
        "/path/to/allowed/directory"
      ]
    }
  }
}
```

### Memory/Knowledge Base

```json
{
  "mcpServers": {
    "memory": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropics/mcp-memory"]
    }
  }
}
```

### Puppeteer (Browser Automation)

```json
{
  "mcpServers": {
    "puppeteer": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropics/mcp-puppeteer"]
    }
  }
}
```

---

## CLI Management

### Add Server

```bash
# Add HTTP server (project scope)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/ --scope project

# Add stdio server (user scope)
claude mcp add --transport stdio dbhub npx -y @bytebase/dbhub --scope user

# Add with headers
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp \
  --header "Authorization: Bearer \${SENTRY_TOKEN}" \
  --scope project
```

### List Servers

```bash
claude mcp list
```

### Remove Server

```bash
claude mcp remove github
```

---

## Settings Integration

Control MCP server access in `settings.json`:

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["github", "memory"],
  "disabledMcpjsonServers": ["filesystem"]
}
```

| Setting | Effect |
|---------|--------|
| `enableAllProjectMcpServers` | Auto-enable all project MCP servers |
| `enabledMcpjsonServers` | Whitelist specific servers |
| `disabledMcpjsonServers` | Blacklist specific servers |

---

## Complete Example

### Project MCP Configuration (`.mcp.json`)

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "database": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub"],
      "env": {
        "PGCONNECTIONSTRING": "${DATABASE_URL}"
      }
    },
    "memory": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropics/mcp-memory"]
    }
  }
}
```

### Corresponding Settings (`.claude/settings.json`)

```json
{
  "enableAllProjectMcpServers": false,
  "enabledMcpjsonServers": ["github", "memory"],
  "disabledMcpjsonServers": ["database"]
}
```

---

## Security Considerations

1. **Never commit secrets**: Use environment variables for API keys
2. **Limit server access**: Only enable servers you need
3. **Review server capabilities**: Understand what each server can do
4. **Use project scope carefully**: All team members will have access
5. **Validate stdio commands**: Ensure commands are from trusted sources

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not connecting | Check URL, env vars, network |
| Authentication failing | Verify API key, header format |
| Stdio server not starting | Check command exists, npx access |
| Server not appearing | Verify `.mcp.json` syntax, check settings |

---

## Related

- [settings.md](settings.md) - MCP settings integration
- [tools.md](tools.md) - MCP adds additional tools

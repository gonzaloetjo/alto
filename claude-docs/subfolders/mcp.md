# Claude Code MCP Configuration (`.mcp.json`)

MCP (Model Context Protocol) enables Claude to connect to external services and tools. Configuration is stored in `.mcp.json` files.

## File Locations

| File | Scope | Shared |
|------|-------|--------|
| `.mcp.json` (project root) | Project (team) | Yes (committed) |
| `~/.claude.json` | User global | No |

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

## Server Types

### HTTP Server (Recommended)

Connect to HTTP-based MCP endpoints:

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

Server-Sent Events connection (deprecated, use HTTP):

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

Run local processes that communicate via stdin/stdout:

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
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropics/mcp-filesystem", "/allowed/path"]
    }
  }
}
```

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

### Stripe

```json
{
  "mcpServers": {
    "stripe": {
      "type": "http",
      "url": "https://mcp.stripe.com",
      "headers": {
        "Authorization": "Bearer ${STRIPE_API_KEY}"
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

### MySQL (via dbhub)

```json
{
  "mcpServers": {
    "mysql": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub"],
      "env": {
        "MYSQL_CONNECTION_STRING": "${MYSQL_URL}"
      }
    }
  }
}
```

### SQLite (via dbhub)

```json
{
  "mcpServers": {
    "sqlite": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub"],
      "env": {
        "SQLITE_PATH": "./database.sqlite"
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

### Slack

```json
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://mcp.slack.com/v1/mcp",
      "headers": {
        "Authorization": "Bearer ${SLACK_BOT_TOKEN}"
      }
    }
  }
}
```

### Linear

```json
{
  "mcpServers": {
    "linear": {
      "type": "http",
      "url": "https://mcp.linear.app",
      "headers": {
        "Authorization": "Bearer ${LINEAR_API_KEY}"
      }
    }
  }
}
```

## CLI Management

### Add Server

```bash
# Add HTTP server (project scope)
claude mcp add --transport http github https://api.githubcopilot.com/mcp/ --scope project

# Add stdio server (user scope)
claude mcp add --transport stdio dbhub npx -y @bytebase/dbhub --scope user

# Add with environment variables
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
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.dev/mcp",
      "headers": {
        "Authorization": "Bearer ${SENTRY_AUTH_TOKEN}"
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

## Security Considerations

1. **Never commit secrets**: Use environment variables for API keys
2. **Limit server access**: Only enable servers you need
3. **Review server capabilities**: Understand what each server can do
4. **Use project scope carefully**: All team members will have access
5. **Validate stdio commands**: Ensure commands are from trusted sources

## Troubleshooting

**Server not connecting:**
- Check URL is correct
- Verify environment variables are set
- Check network connectivity
- Review server logs

**Authentication failing:**
- Verify API key is valid
- Check header format
- Ensure token hasn't expired

**Stdio server not starting:**
- Check command exists
- Verify npx can access package
- Check for process errors in logs

**Server not appearing:**
- Verify `.mcp.json` syntax
- Check settings don't disable it
- Run `claude mcp list` to verify

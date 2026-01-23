# Claude Code > Permissions

> Permission modes and access control patterns.

## Permission Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `default` | Ask for permission on most operations | Normal development |
| `acceptEdits` | Auto-accept file edits, ask for others | Trusted editing |
| `dontAsk` | Minimal prompts (still asks for dangerous) | Fast iteration |
| `bypassPermissions` | Skip all prompts | Automation |
| `plan` | Read-only, blocks modifications | Safe exploration |

---

## Mode Selection

### Via Settings

```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

### Via CLI

```bash
claude --permission-mode plan
```

### Via Keyboard

`Shift+Tab` cycles through modes during session:
1. **Normal** (default)
2. **Auto-Accept** (`⏵⏵ accept edits on`)
3. **Plan Mode** (`⏸ plan mode on`)

---

## Permission Rules

### Rule Structure

```json
{
  "permissions": {
    "allow": [...],
    "ask": [...],
    "deny": [...]
  }
}
```

| List | Behavior |
|------|----------|
| `allow` | Auto-approve matching operations |
| `ask` | Prompt for confirmation |
| `deny` | Block without prompting |

### Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `Tool` | All uses of the tool |
| `Tool(pattern)` | Uses matching the exact pattern |
| `Tool(prefix:*)` | Uses starting with prefix |
| `Tool(*suffix)` | Uses ending with suffix |
| `Tool(./path/**)` | Path glob patterns |

### Examples

```json
{
  "permissions": {
    "allow": [
      "Bash(npm:*)",           // Any npm command
      "Bash(git status:*)",    // git status only
      "Read(./src/**)",        // Read anything in src/
      "Edit(./src/**/*.ts)"    // Edit TypeScript in src/
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

---

## Tool Availability by Mode

| Tool | default | acceptEdits | dontAsk | bypassPermissions | plan |
|------|---------|-------------|---------|-------------------|------|
| Read | Ask | Allow | Allow | Allow | Allow |
| Glob | Ask | Allow | Allow | Allow | Allow |
| Grep | Ask | Allow | Allow | Allow | Allow |
| Edit | Ask | **Allow** | Allow | Allow | **Block** |
| Write | Ask | **Allow** | Allow | Allow | **Block** |
| Bash | Ask | Ask | Allow | Allow | **Block** |
| WebFetch | Ask | Ask | Allow | Allow | **Block** |
| WebSearch | Ask | Ask | Allow | Allow | **Block** |
| Task | Ask | Allow | Allow | Allow | Allow |

---

## Plan Mode

### Purpose

Safe, read-only code analysis and planning before making changes.

### Available Tools

| Tool | Available | Why |
|------|-----------|-----|
| Read | Yes | Examine files |
| Glob | Yes | Find files |
| Grep | Yes | Search content |
| AskUserQuestion | Yes | Gather requirements |
| ExitPlanMode | Yes | Signal ready to implement |

### Blocked Tools

| Tool | Why Blocked |
|------|-------------|
| Edit | Modifies files |
| Write | Creates/overwrites files |
| Bash | Can execute arbitrary commands |
| WebFetch | External requests |
| WebSearch | External requests |

### Entering Plan Mode

```bash
# Start in plan mode
claude --permission-mode plan

# Or toggle with keyboard
Shift+Tab
```

---

## Additional Directories

Expand Claude's file access beyond the project:

```json
{
  "permissions": {
    "additionalDirectories": [
      "../shared-docs/",
      "../other-project/",
      "~/reference-code/"
    ]
  }
}
```

---

## Sandbox Mode

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
      "allowLocalBinding": true
    }
  }
}
```

| Setting | Description |
|---------|-------------|
| `enabled` | Enable sandbox mode |
| `autoAllowBashIfSandboxed` | Auto-approve Bash when sandboxed |
| `excludedCommands` | Commands that bypass sandbox |
| `allowUnsandboxedCommands` | Allow some commands outside sandbox |

---

## Disabling Bypass Mode

Prevent use of `bypassPermissions`:

```json
{
  "permissions": {
    "disableBypassPermissionsMode": "disable"
  }
}
```

---

## Agent Permissions

Agents can have their own permission modes:

```yaml
---
name: security-auditor
permissionMode: plan
tools: Read, Grep, Glob
disallowedTools: Write, Edit, Bash
---
```

| Field | Description |
|-------|-------------|
| `permissionMode` | Override mode for this agent |
| `tools` | Allowed tools (whitelist) |
| `disallowedTools` | Denied tools (blacklist) |

---

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
    "enabled": true
  }
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

### CI/CD Automation

```json
{
  "permissions": {
    "allow": [
      "Bash(npm:*)",
      "Bash(git:*)",
      "Read",
      "Edit",
      "Write"
    ],
    "deny": [
      "Bash(sudo:*)",
      "Bash(rm -rf /*:*)"
    ],
    "defaultMode": "bypassPermissions"
  }
}
```

---

## Related

- [settings.md](settings.md) - Full settings reference
- [plan-mode.md](plan-mode.md) - Plan mode details
- [agents.md](agents.md) - Agent permission configuration

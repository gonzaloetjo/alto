# Claude Code Hooks

Hooks are scripts that execute in response to Claude Code events. They enable validation, automation, logging, and custom integrations.

## Configuration

Hooks are configured in `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Notification": [...],
    "Stop": [...],
    "SessionStart": [...],
    "SessionEnd": [...]
  }
}
```

## Hook Events

| Event | Fires | Use Cases |
|-------|-------|-----------|
| `PreToolUse` | Before tool execution | Validation, blocking, logging |
| `PostToolUse` | After tool execution | Formatting, notifications, logging |
| `PermissionRequest` | On permission prompt | Auto-approve/deny |
| `UserPromptSubmit` | Before processing user input | Augment prompts |
| `Notification` | When Claude needs attention | Custom notifications |
| `Stop` | When response completes | Logging, cleanup |
| `SubagentStop` | When subagent completes | Process results |
| `PreCompact` | Before conversation compaction | Prevent/allow compaction |
| `SessionStart` | Session begins | Environment setup |
| `SessionEnd` | Session ends | Cleanup, reporting |

## Hook Structure

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/hook-script.sh"
          }
        ]
      }
    ]
  }
}
```

### Matcher Patterns

| Pattern | Matches |
|---------|---------|
| `""` (empty) | All events |
| `"Bash"` | Bash tool only |
| `"Edit\|Write"` | Edit or Write tools |
| `"Bash\|Edit\|Write"` | Multiple tools |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success, continue |
| `1` | Error, log and continue |
| `2` | Block operation (PreToolUse) / Deny (PermissionRequest) |

## Input/Output

Hooks receive JSON on stdin and can output JSON or plain text.

### PreToolUse Input

```json
{
  "session_id": "abc123",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run tests"
  }
}
```

### PostToolUse Input

```json
{
  "session_id": "abc123",
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.ts",
    "old_string": "...",
    "new_string": "..."
  },
  "tool_output": {
    "success": true
  }
}
```

### JSON Output (Optional)

```json
{
  "allow": true,
  "message": "Validation passed",
  "modified_input": { ... }
}
```

## Examples

### Command Validation (PreToolUse)

Block dangerous commands:

```bash
#!/bin/bash
# .claude/hooks/validate-bash.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block dangerous patterns
if echo "$COMMAND" | grep -qE '(rm -rf /|mkfs|dd if=|:(){ :|fork bomb)'; then
  echo "BLOCKED: Dangerous command detected" >&2
  exit 2
fi

# Block sudo
if echo "$COMMAND" | grep -qE '^sudo '; then
  echo "BLOCKED: sudo commands not allowed" >&2
  exit 2
fi

exit 0
```

Configuration:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/validate-bash.sh"
          }
        ]
      }
    ]
  }
}
```

### Auto-Formatting (PostToolUse)

Format files after editing:

```bash
#!/bin/bash
# .claude/hooks/auto-format.sh

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# Format based on extension
case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.md)
    npx prettier --write "$FILE_PATH" 2>/dev/null
    ;;
  *.py)
    python -m black "$FILE_PATH" 2>/dev/null
    ;;
  *.go)
    gofmt -w "$FILE_PATH" 2>/dev/null
    ;;
  *.rs)
    rustfmt "$FILE_PATH" 2>/dev/null
    ;;
  *.sol)
    forge fmt "$FILE_PATH" 2>/dev/null
    ;;
esac

exit 0
```

Configuration:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/auto-format.sh"
          }
        ]
      }
    ]
  }
}
```

### Command Logging (PostToolUse)

Log all commands to a file:

```bash
#!/bin/bash
# .claude/hooks/log-commands.sh

INPUT=$(cat)
SESSION=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TOOL=$(echo "$INPUT" | jq -r '.tool_name // "unknown"')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // .tool_input.file_path // "N/A"')

LOG_FILE="$HOME/.claude/command-log.txt"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date -Iseconds)] [$SESSION] $TOOL: $COMMAND" >> "$LOG_FILE"
exit 0
```

### Read-Only SQL Validation

Ensure only SELECT queries are executed:

```bash
#!/bin/bash
# .claude/hooks/validate-sql.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Check if this is a database command
if ! echo "$COMMAND" | grep -qiE '(psql|mysql|sqlite3|mongo)'; then
  exit 0
fi

# Block write operations
if echo "$COMMAND" | grep -qiE '(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)'; then
  echo "BLOCKED: Only SELECT queries allowed" >&2
  exit 2
fi

exit 0
```

### Desktop Notifications

Send notification when Claude needs input:

```bash
#!/bin/bash
# .claude/hooks/notify.sh

INPUT=$(cat)
TITLE=$(echo "$INPUT" | jq -r '.title // "Claude Code"')
MESSAGE=$(echo "$INPUT" | jq -r '.message // "Needs your attention"')

# Linux
if command -v notify-send &>/dev/null; then
  notify-send "$TITLE" "$MESSAGE"
# macOS
elif command -v osascript &>/dev/null; then
  osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\""
fi

exit 0
```

Configuration:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/notify.sh"
          }
        ]
      }
    ]
  }
}
```

### Session Logging

Log session start/end:

```bash
#!/bin/bash
# .claude/hooks/session-start.sh

INPUT=$(cat)
SESSION=$(echo "$INPUT" | jq -r '.session_id')
PROJECT=$(pwd)

LOG_FILE="$HOME/.claude/sessions.log"
echo "[$(date -Iseconds)] SESSION START: $SESSION in $PROJECT" >> "$LOG_FILE"
exit 0
```

```bash
#!/bin/bash
# .claude/hooks/session-end.sh

INPUT=$(cat)
SESSION=$(echo "$INPUT" | jq -r '.session_id')
DURATION=$(echo "$INPUT" | jq -r '.duration_seconds // 0')

LOG_FILE="$HOME/.claude/sessions.log"
echo "[$(date -Iseconds)] SESSION END: $SESSION (${DURATION}s)" >> "$LOG_FILE"
exit 0
```

Configuration:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [{"type": "command", "command": "./.claude/hooks/session-start.sh"}]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [{"type": "command", "command": "./.claude/hooks/session-end.sh"}]
      }
    ]
  }
}
```

### Auto-Lint on Write

Run linter after file writes:

```bash
#!/bin/bash
# .claude/hooks/auto-lint.sh

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

case "$FILE_PATH" in
  *.ts|*.tsx)
    npx eslint --fix "$FILE_PATH" 2>/dev/null
    ;;
  *.py)
    python -m pylint "$FILE_PATH" 2>/dev/null || true
    ;;
  *.sol)
    solhint "$FILE_PATH" 2>/dev/null || true
    ;;
esac

exit 0
```

### Git Commit Validation

Validate commit messages:

```bash
#!/bin/bash
# .claude/hooks/validate-commit.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Check if this is a git commit
if ! echo "$COMMAND" | grep -q "git commit"; then
  exit 0
fi

# Extract commit message
MESSAGE=$(echo "$COMMAND" | grep -oP '(?<=-m ")[^"]+' || echo "$COMMAND" | grep -oP "(?<=-m ')[^']+")

# Validate conventional commit format
if ! echo "$MESSAGE" | grep -qE '^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+'; then
  echo "WARNING: Commit message doesn't follow conventional commits format" >&2
  echo "Format: type(scope): description" >&2
  echo "Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert" >&2
  # Just warn, don't block
  exit 0
fi

exit 0
```

### Prompt Augmentation (UserPromptSubmit)

Add context to user prompts:

```bash
#!/bin/bash
# .claude/hooks/augment-prompt.sh

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt')

# Add project context
CONTEXT="[Project: $(basename $(pwd)), Branch: $(git branch --show-current 2>/dev/null || echo 'N/A')]"

# Output modified prompt as JSON
jq -n --arg prompt "$CONTEXT $PROMPT" '{"prompt": $prompt}'
```

## Hook File Organization

```
.claude/
├── hooks/
│   ├── validate-bash.sh
│   ├── auto-format.sh
│   ├── log-commands.sh
│   ├── notify.sh
│   └── session-log.sh
└── settings.json
```

## Multiple Hooks

Chain multiple hooks for an event:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {"type": "command", "command": "./.claude/hooks/auto-format.sh"},
          {"type": "command", "command": "./.claude/hooks/auto-lint.sh"},
          {"type": "command", "command": "./.claude/hooks/log-changes.sh"}
        ]
      }
    ]
  }
}
```

Hooks execute in order. If any hook exits with code 2 (for PreToolUse), the operation is blocked.

## Hook Scopes

Hooks can be defined at multiple levels:

| Location | Scope |
|----------|-------|
| `.claude/settings.json` | Project (team) |
| `.claude/settings.local.json` | Personal project |
| `~/.claude/settings.json` | User global |
| Managed settings | System-wide |

## Disabling Hooks

```json
{
  "disableAllHooks": true
}
```

Or allow only managed (IT-deployed) hooks:

```json
{
  "allowManagedHooksOnly": true
}
```

## Best Practices

1. **Keep hooks fast**: Long-running hooks slow down Claude
2. **Handle errors gracefully**: Exit 0 if hook completes, even on non-fatal errors
3. **Use exit 2 sparingly**: Only block when truly necessary
4. **Log for debugging**: Write to log files for troubleshooting
5. **Make scripts executable**: `chmod +x .claude/hooks/*.sh`
6. **Test independently**: Test scripts outside Claude first
7. **Document behavior**: Comment what each hook does

## Troubleshooting

**Hook not running:**
- Check script is executable
- Verify path is correct
- Check matcher pattern matches tool

**Hook blocking unexpectedly:**
- Check exit code (2 blocks)
- Add debug logging to script
- Test with simple input

**Hook output not visible:**
- Hooks run in background
- Use log files for debugging
- Check stderr output

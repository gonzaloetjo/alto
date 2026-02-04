# Claude Code > Hooks

> Event scripting for validation, automation, and logging.

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

---

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

---

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

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success, continue |
| `1` | Error, log and continue |
| `2` | Block operation (PreToolUse) / Deny (PermissionRequest) |

---

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

---

## Examples

### Command Validation (PreToolUse)

Block dangerous commands:

```bash
#!/bin/bash
# .claude/hooks/validate-bash.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block dangerous patterns
if echo "$COMMAND" | grep -qE '(rm -rf /|mkfs|dd if=)'; then
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

### Desktop Notifications

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

### Command Logging

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

---

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

Hooks execute in order. If any PreToolUse hook exits with code 2, the operation is blocked.

---

## Hook Scopes

| Location | Scope |
|----------|-------|
| `.claude/settings.json` | Project (team) |
| `.claude/settings.local.json` | Personal project |
| `~/.claude/settings.json` | User global |
| Managed settings | System-wide |

---

## Key Insight

> **Rules are suggestions. Hooks are enforcement.**
>
> A rule saying "don't edit .env" is parsed by Claude and *maybe* followed.
> A PreToolUse hook blocking .env edits *always* runs and blocks the operation.

### Hook Limitations

| Limitation | Issue |
|------------|-------|
| PreToolUse cannot see result | Runs before tool executes |
| PostToolUse cannot modify result | Result already in context |
| Warn messages only reach user | Claude doesn't see warn output |
| Skill-scoped hooks may not trigger | Known issue in plugins |

---

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

---

## Best Practices

1. **Keep hooks fast**: Long-running hooks slow down Claude
2. **Handle errors gracefully**: Exit 0 if hook completes, even on non-fatal errors
3. **Use exit 2 sparingly**: Only block when truly necessary
4. **Log for debugging**: Write to log files for troubleshooting
5. **Make scripts executable**: `chmod +x .claude/hooks/*.sh`
6. **Test independently**: Test scripts outside Claude first

---

## Related

- [settings.md](settings.md) - Hook configuration location
- [rules.md](rules.md) - Suggestions (not enforcement)
- [permissions.md](permissions.md) - Permission rules

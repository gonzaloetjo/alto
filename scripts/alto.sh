#!/usr/bin/env bash
# ALTO main entry point - Start Claude with automatic session resume per mode
# Environment variables:
#   RUNS_DIR - Directory for ALTO runtime state
# Runtime packages (via devenv): jq

set -e

# Handle mode switching: alto dev, alto setup, alto build, alto switch X
case "$1" in
  setup|build|dev)
    exec alto-switch "$1"
    ;;
  switch)
    shift
    exec alto-switch "$@"
    ;;
esac

# Not an ALTO project? Just run claude
if [ ! -f "$RUNS_DIR/orchestrator.json" ]; then
  exec claude "$@"
fi

# Read current mode
CURRENT_MODE=$(jq -r '.orchestrator // "setup"' "$RUNS_DIR/orchestrator.json")

# Check for existing session
MODES_FILE="$RUNS_DIR/sessions/modes.json"
SESSION_ID=""

if [ -f "$MODES_FILE" ]; then
  SESSION_ID=$(jq -r ".[\"$CURRENT_MODE\"].session_id // empty" "$MODES_FILE" 2>/dev/null || true)
fi

# Default prompt if none provided
if [ $# -eq 0 ]; then
  PROMPT="hi"
else
  PROMPT="$*"
fi

if [ -n "$SESSION_ID" ]; then
  # Validate session exists
  if [ -d "$HOME/.claude/session-env/$SESSION_ID" ]; then
    echo "Resuming $CURRENT_MODE session..."
    exec claude --resume "$SESSION_ID" "$PROMPT"
  else
    echo "Previous session expired. Starting fresh $CURRENT_MODE session..."
    jq ".[\"$CURRENT_MODE\"] = null" "$MODES_FILE" > "$MODES_FILE.tmp" && mv "$MODES_FILE.tmp" "$MODES_FILE"
  fi
fi

echo "Starting new $CURRENT_MODE session..."
exec claude "$PROMPT"

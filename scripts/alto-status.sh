#!/usr/bin/env bash
# ALTO status - Show ALTO status
# Environment variables:
#   RUNS_DIR - Directory for ALTO runtime state
#   ORCHESTRATOR - Current orchestrator mode

if [ ! -f "$RUNS_DIR/state.json" ]; then
  echo "ALTO not initialized. Run 'alto-setup' first."
  exit 1
fi

PHASE=$(jq -r '.phase // "none"' "$RUNS_DIR/state.json")
COMPLETED=$(jq -r '.completed_task_ids | length' "$RUNS_DIR/state.json")

# Count remaining tasks (exclude completed)
COMPLETED_IDS=$(jq -r '.completed_task_ids[]?' "$RUNS_DIR/state.json" 2>/dev/null)
REMAINING=0
if [ -d "$RUNS_DIR/tasks" ]; then
  for task_file in "$RUNS_DIR/tasks"/task-*.md; do
    [ -f "$task_file" ] || continue
    task_id=$(basename "$task_file" .md)
    if ! echo "$COMPLETED_IDS" | grep -q "^$task_id$"; then
      REMAINING=$((REMAINING + 1))
    fi
  done
fi

# Get current orchestrator
CURRENT_ORCH="$ORCHESTRATOR"

echo "ALTO Status"
echo "==========="
echo "Orchestrator: $CURRENT_ORCH"
echo "Branch: $(jq -r '.run_branch // "none"' "$RUNS_DIR/state.json")"
echo "Phase: $PHASE"
echo "Current Task: $(jq -r '.current_task_id // "none"' "$RUNS_DIR/state.json")"
echo "Completed: $COMPLETED tasks"
echo "Remaining: $REMAINING tasks"

# Feature complete check
if [ "$REMAINING" -eq 0 ] && [ "$COMPLETED" -gt 0 ]; then
  echo ""
  echo ">>> FEATURE COMPLETE <<<"
fi

echo ""
echo "Recent handoffs:"
ls -t "$RUNS_DIR/handoffs/" 2>/dev/null | head -5 || echo "  (none)"

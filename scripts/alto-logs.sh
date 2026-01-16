#!/usr/bin/env bash
# ALTO logs - Query event log (debug mode)
# Environment variables:
#   RUNS_DIR - Directory for ALTO runtime state

EVENTS_FILE="$RUNS_DIR/logs/events.jsonl"

usage() {
  echo "ALTO Logs - Query event log (debug mode)"
  echo ""
  echo "Usage: alto-logs [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --type TYPE    Filter by event type"
  echo "  --last N       Show last N events (default: 20)"
  echo "  --metrics      Show aggregated metrics"
  echo "  --raw          Output raw JSON"
  echo "  --help         Show this help"
  echo ""
  echo "Event types: session_start, session_end, handoff, decision, phase_change"
}

LAST_N=20
EVENT_TYPE=""
SHOW_METRICS=false
RAW_OUTPUT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type) EVENT_TYPE="$2"; shift 2 ;;
    --last) LAST_N="$2"; shift 2 ;;
    --metrics) SHOW_METRICS=true; shift ;;
    --raw) RAW_OUTPUT=true; shift ;;
    --help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

if [ ! -f "$EVENTS_FILE" ]; then
  echo "No events logged. Enable debug mode: alto.debug = true;"
  exit 0
fi

if [ "$SHOW_METRICS" = true ]; then
  echo "ALTO Metrics"
  echo "============"
  TOTAL=$(wc -l < "$EVENTS_FILE")
  echo "Total events: $TOTAL"
  echo ""
  echo "Events by type:"
  jq -r '.event' "$EVENTS_FILE" | sort | uniq -c | sort -rn
  exit 0
fi

FILTER="."
if [ -n "$EVENT_TYPE" ]; then
  FILTER="select(.event == \"$EVENT_TYPE\")"
fi

if [ "$RAW_OUTPUT" = true ]; then
  tail -n "$LAST_N" "$EVENTS_FILE" | jq -c "$FILTER"
else
  echo "Recent events (last $LAST_N):"
  echo ""
  tail -n "$LAST_N" "$EVENTS_FILE" | jq -r "$FILTER | \"\(.ts | split(\"T\")[1] | split(\".\")[0]) [\(.event)] \(if .agent then .agent else \"\" end)\""
fi

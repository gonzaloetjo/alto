#!/usr/bin/env bash
# ALTO switch - Switch orchestrator mode and start Claude
# Environment variables:
#   RUNS_DIR - Directory for ALTO runtime state
#   ALTO_SRC - Path to ALTO source directory
#   JQ_BIN - Path to jq binary
#   SED_BIN - Path to sed binary

TARGET="$1"

# Read current mode from orchestrator.json (runtime value, not nix-time)
if [ -f "$RUNS_DIR/orchestrator.json" ]; then
  CURRENT=$("$JQ_BIN" -r '.orchestrator // "setup"' "$RUNS_DIR/orchestrator.json")
else
  CURRENT="setup"
fi

# Detect if we're in ALTO source repo (not a consumer project)
if [ -f "templates/CLAUDE.md.dev" ]; then
  echo "ERROR: Cannot switch orchestrator modes in the ALTO source repo."
  echo ""
  echo "You're developing ALTO itself. Mode switching is for consumer projects."
  echo "In the ALTO repo, you work directly with the source files."
  exit 1
fi

if [ -z "$TARGET" ]; then
  echo "ALTO Switch"
  echo "==========="
  echo ""
  echo "Current orchestrator: $CURRENT"
  echo ""
  echo "Usage: alto-switch <orchestrator>"
  echo ""
  echo "Available orchestrators:"
  echo "  setup  - Human-interactive (feature definition, configuration, cleanup)"
  echo "  build  - Autonomous execution (architecture, planning, execution, replan)"
  echo "  dev    - ALTO development (single alto-dev agent with dev-guide skill)"
  exit 0
fi

if [ "$TARGET" != "setup" ] && [ "$TARGET" != "build" ] && [ "$TARGET" != "dev" ]; then
  echo "Error: Invalid orchestrator '$TARGET'"
  echo "Valid options: setup, build, dev"
  exit 1
fi

if [ "$TARGET" = "$CURRENT" ]; then
  echo "Already using '$TARGET' orchestrator."
  exit 0
fi

# Check devenv.nix exists
if [ ! -f "devenv.nix" ]; then
  echo "Error: devenv.nix not found in current directory"
  exit 1
fi

echo "Switching from '$CURRENT' to '$TARGET'..."

# Update devenv.nix - update existing or add new line
if grep -q 'alto\.orchestrator\s*=' devenv.nix; then
  "$SED_BIN" -i 's/alto\.orchestrator\s*=\s*[^;]*/alto.orchestrator = "'"$TARGET"'"/' devenv.nix
  echo "Updated devenv.nix: alto.orchestrator = \"$TARGET\""
else
  # Add after opening brace
  "$SED_BIN" -i 's/^{$/{\n  alto.orchestrator = "'"$TARGET"'";/' devenv.nix
  echo "Added to devenv.nix: alto.orchestrator = \"$TARGET\""
fi

# Also update runs/orchestrator.json for tooling that reads mode at runtime
if [ -d "$RUNS_DIR" ]; then
  cat > "$RUNS_DIR/orchestrator.json" << ORCH_EOF
{
  "orchestrator": "$TARGET",
  "updated_at": "$(date -Iseconds)"
}
ORCH_EOF
fi

# Copy the correct CLAUDE.md for the new mode
if [ -f "$ALTO_SRC/templates/CLAUDE.md.$TARGET" ]; then
  rm -f CLAUDE.md 2>/dev/null || true
  cp "$ALTO_SRC/templates/CLAUDE.md.$TARGET" CLAUDE.md
  echo "Updated CLAUDE.md for $TARGET mode"
fi

echo ""
echo "Switched to $TARGET mode."
echo ""

# Automatically start alto
exec alto

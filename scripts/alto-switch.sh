#!/usr/bin/env bash
# ALTO switch - Switch orchestrator mode and start Claude
# Environment variables:
#   RUNS_DIR - Directory for ALTO runtime state
#   ALTO_SRC - Path to ALTO source directory
# Runtime packages (via devenv): jq, gnused

TARGET="$1"

# Read current mode from orchestrator.json (runtime value, not nix-time)
if [ -f "$RUNS_DIR/orchestrator.json" ]; then
  CURRENT=$(jq -r '.orchestrator // "setup"' "$RUNS_DIR/orchestrator.json")
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
  echo "Already in '$TARGET' mode."
  # Start alto (same as after successful switch)
  exec alto
fi

# Check devenv.nix exists
if [ ! -f "devenv.nix" ]; then
  echo "Error: devenv.nix not found in current directory"
  exit 1
fi

echo "Switching from '$CURRENT' to '$TARGET'..."

# Update devenv.nix - update existing or add new line
if grep -q 'alto\.orchestrator\s*=' devenv.nix; then
  sed -i 's/alto\.orchestrator\s*=\s*[^;]*/alto.orchestrator = "'"$TARGET"'"/' devenv.nix
  echo "Updated devenv.nix: alto.orchestrator = \"$TARGET\""
else
  # Add after opening brace
  sed -i 's/^{$/{\n  alto.orchestrator = "'"$TARGET"'";/' devenv.nix
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

# Redeploy skills for the new mode
rm -rf .claude/skills/* 2>/dev/null || true

# Skills available to all orchestrators
cp -r "$ALTO_SRC"/skills/alto-switch .claude/skills/ 2>/dev/null || true

# Shared ALTO skills (setup and build)
if [ "$TARGET" != "dev" ]; then
  cp -r "$ALTO_SRC"/skills/alto-protocol .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/alto-feature-setup .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/alto-configure .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/handoff-writing .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/task-writing .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/review-writing .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/scope-discipline .claude/skills/ 2>/dev/null || true
fi

# Dev-specific skills
if [ "$TARGET" = "dev" ]; then
  cp -r "$ALTO_SRC"/skills/alto-dev-guide .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/writing-alto-skills .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/alto-self-fix .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/prompt-writing .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/alto-test-protocol .claude/skills/ 2>/dev/null || true
fi

echo "Redeployed skills for $TARGET mode"

echo ""
echo "Switched to $TARGET mode."
echo ""

# Automatically start alto
exec alto

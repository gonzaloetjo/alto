#!/usr/bin/env bash
# ALTO deploy - Deploy ALTO files for devenv shell entry
# Environment variables:
#   ALTO_SRC - Path to ALTO source directory
#   RUNS_DIR - Directory for ALTO runtime state
#   ORCHESTRATOR - Current orchestrator mode (setup|build|dev)
#   DEBUG_ENABLED - Whether debug mode is enabled (true|false)
#   INCLUDE_SPAWNER_SKILLS - Whether to include spawner skills (true|false)
#   ARBITER_MAX_LINES - Max lines changed without human review
#   ARBITER_MAX_FILES - Max files changed without human review
#   ARBITER_TOKEN_INTERVAL - Tokens between arbiter checkpoints
#   ARBITER_TASK_INTERVAL - Tasks between arbiter checkpoints
#   PLANNING_REQUIRE_APPROVAL - Require user approval after architecture (true|false)
#   PLANNING_REPLAN_STRATEGY - How to determine replan frequency (auto|fixed|none)
#   PLANNING_FIXED_BATCH_SIZE - Batch size when replanStrategy = 'fixed'
#   PLANNING_ARCHITECT_MODEL - Model for architecture phase
#   PLANNING_PLANNER_MODEL - Model for planner agent

# Create .claude directory for hooks and skills
mkdir -p .claude/hooks .claude/skills

# Copy hook scripts (referenced by native hook commands)
cp -r "$ALTO_SRC"/hooks/*.py .claude/hooks/ 2>/dev/null || true

# Remove old skills before copying (they're read-only from nix store)
rm -rf .claude/skills/* 2>/dev/null || true

# Copy skills available to all orchestrators
cp -r "$ALTO_SRC"/skills/alto-switch .claude/skills/ 2>/dev/null || true

# Copy shared ALTO skills (setup and build orchestrators)
if [ "$ORCHESTRATOR" != "dev" ]; then
  cp -r "$ALTO_SRC"/skills/alto-protocol .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/alto-feature-setup .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/alto-configure .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/scope-discipline .claude/skills/ 2>/dev/null || true
fi

# Copy dev-specific skills (dev orchestrator only)
if [ "$ORCHESTRATOR" = "dev" ]; then
  cp -r "$ALTO_SRC"/skills/alto-dev-guide .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/writing-alto-skills .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/alto-self-fix .claude/skills/ 2>/dev/null || true
  cp -r "$ALTO_SRC"/skills/prompt-writing .claude/skills/ 2>/dev/null || true
fi

if [ "$INCLUDE_SPAWNER_SKILLS" = "true" ]; then
  cp -r "$ALTO_SRC"/skills/spawner .claude/skills/ 2>/dev/null || true
fi

# Ensure .claude files are writable (they come read-only from nix store)
chmod -R +w .claude/ 2>/dev/null || true

# Create runs directory structure
mkdir -p "$RUNS_DIR"/{tasks,handoffs,arbiter/checkpoints,review,sessions,usage,tools,logs}

# Write debug config for hooks to read
cat > "$RUNS_DIR/debug-config.json" << DEBUG_EOF
{
  "debug": $DEBUG_ENABLED
}
DEBUG_EOF

# Initialize state.json if not exists
if [ ! -f "$RUNS_DIR/state.json" ]; then
  cat > "$RUNS_DIR/state.json" << 'STATE_EOF'
{
  "protocol": "alto-v1",
  "run_branch": null,
  "phase": null,
  "current_task_id": null,
  "current_role": null,
  "completed_task_ids": [],
  "last_handoff": null,
  "estimated_tasks": null,
  "replan_every": null,
  "needs_architect": false,
  "updated_at": null
}
STATE_EOF
fi

# Initialize sessions/modes.json if not exists
if [ ! -f "$RUNS_DIR/sessions/modes.json" ]; then
  echo '{"setup": null, "build": null, "dev": null}' > "$RUNS_DIR/sessions/modes.json"
fi

# Initialize arbiter config (always overwrite to keep in sync)
cat > "$RUNS_DIR/arbiter/config.json" << ARBITER_EOF
{
  "max_lines_changed_without_human": $ARBITER_MAX_LINES,
  "max_files_changed_without_human": $ARBITER_MAX_FILES,
  "token_checkpoint_interval": $ARBITER_TOKEN_INTERVAL,
  "task_checkpoint_interval": $ARBITER_TASK_INTERVAL,
  "high_risk_bash_prefixes": ["rm -rf /", "sudo rm", "dd if=", "mkfs", "> /dev/"]
}
ARBITER_EOF

# Initialize arbiter state if not exists
if [ ! -f "$RUNS_DIR/arbiter/state.json" ]; then
  cat > "$RUNS_DIR/arbiter/state.json" << 'ARBSTATE_EOF'
{
  "last_checkpoint_at": null,
  "tokens_since_checkpoint": 0,
  "tasks_since_checkpoint": 0,
  "checkpoint_count": 0
}
ARBSTATE_EOF
fi

# Write planning config (always overwrite to keep in sync)
cat > "$RUNS_DIR/planning-config.json" << PLANNING_EOF
{
  "require_approval": $PLANNING_REQUIRE_APPROVAL,
  "replan_strategy": "$PLANNING_REPLAN_STRATEGY",
  "fixed_batch_size": $PLANNING_FIXED_BATCH_SIZE,
  "architect_model": "$PLANNING_ARCHITECT_MODEL",
  "planner_model": "$PLANNING_PLANNER_MODEL"
}
PLANNING_EOF

# Initialize verification config if not exists (user can modify mid-session)
if [ ! -f "$RUNS_DIR/verification-config.json" ]; then
  cat > "$RUNS_DIR/verification-config.json" << 'VERIFY_EOF'
{
  "*.ts": {},
  "*.tsx": {},
  "*.py": {},
  "*.go": {}
}
VERIFY_EOF
fi

# Write orchestrator config (always overwrite to keep in sync)
cat > "$RUNS_DIR/orchestrator.json" << ORCH_EOF
{
  "orchestrator": "$ORCHESTRATOR",
  "updated_at": "$(date -Iseconds)"
}
ORCH_EOF

# Copy orchestrator-specific CLAUDE.md (always overwrite to match orchestrator)
# setup = human-interactive, build = autonomous execution
# Remove first to handle read-only files from previous deploys
rm -f CLAUDE.md 2>/dev/null || true
cp "$ALTO_SRC/templates/CLAUDE.md.$ORCHESTRATOR" CLAUDE.md 2>/dev/null || true

echo "ALTO deployed"

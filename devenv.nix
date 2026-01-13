{ config, lib, pkgs, ... }:

let
  cfg = config.alto;
  altoSrc = ./.;

  # Helper to read agent file and strip YAML frontmatter
  # Agent files have format: ---\nfrontmatter\n---\ncontent
  # We want just the content after the second ---
  readAgentPrompt = name:
    let
      content = builtins.readFile "${altoSrc}/agents/${name}.md";
      # Split by "---" and take everything after the second occurrence
      parts = lib.splitString "---" content;
      # parts[0] is empty (before first ---), parts[1] is frontmatter, parts[2+] is content
      promptParts = lib.drop 2 parts;
    in
      lib.concatStringsSep "---" promptParts;

in
{
  options.alto = {
    enable = lib.mkEnableOption "ALTO (Autonomous Lifecycle Task Orchestrator) for Claude Code";

    # Arbiter thresholds
    arbiter = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable arbiter agent for human review gates";
      };

      maxLinesChanged = lib.mkOption {
        type = lib.types.int;
        default = 2000;
        description = "BLOCK if more lines changed without human review";
      };

      maxFilesChanged = lib.mkOption {
        type = lib.types.int;
        default = 50;
        description = "BLOCK if more files changed without human review";
      };

      tokenCheckpointInterval = lib.mkOption {
        type = lib.types.int;
        default = 100000;
        description = "Tokens between arbiter checkpoints";
      };

      taskCheckpointInterval = lib.mkOption {
        type = lib.types.int;
        default = 3;
        description = "Tasks between arbiter checkpoints";
      };
    };

    # Permission defaults
    permissions = {
      defaultMode = lib.mkOption {
        type = lib.types.enum [ "bypassPermissions" "askEveryTime" "allowEdits" ];
        default = "bypassPermissions";
        description = "Default permission mode for Claude Code";
      };

      allowBash = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "git" "make" "npm" "pnpm" "yarn" "docker" "docker compose" "ls" "cat" "mkdir" "python" "python3" "node" ];
        description = "Bash commands to allow without prompting";
      };

      askBash = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "git push" ];
        description = "Bash commands that require confirmation";
      };

      denyRead = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "./.env" "./.env.*" "./secrets/**" "**/*.pem" "**/*id_rsa*" ];
        description = "File patterns to deny reading";
      };

      denyBash = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "rm -rf" "sudo" ];
        description = "Bash commands to always deny";
      };
    };

    # Include spawner skills
    includeSpawnerSkills = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Include domain skills from spawner (api-design, frontend, etc.)";
    };

    # Runtime directory name
    runsDir = lib.mkOption {
      type = lib.types.str;
      default = "runs";
      description = "Directory for ALTO runtime state";
    };

    # Planning configuration
    planning = {
      requireApproval = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Require user approval after architecture phase. Set false for fully autonomous.";
      };

      replanStrategy = lib.mkOption {
        type = lib.types.enum [ "auto" "fixed" "none" ];
        default = "auto";
        description = "How to determine replan frequency. 'auto' = based on estimated task count, 'fixed' = use fixedBatchSize, 'none' = no replanning.";
      };

      fixedBatchSize = lib.mkOption {
        type = lib.types.int;
        default = 5;
        description = "Batch size when replanStrategy = 'fixed'. Ignored for 'auto' or 'none'.";
      };

      architectModel = lib.mkOption {
        type = lib.types.enum [ "opus" "sonnet" ];
        default = "opus";
        description = "Model for architecture phase (orchestrator exploration).";
      };

      plannerModel = lib.mkOption {
        type = lib.types.enum [ "opus" "sonnet" ];
        default = "opus";
        description = "Model for planner agent (task file generation).";
      };
    };
  };

  config = lib.mkIf cfg.enable {
    # Ensure python3 and jq are available for hooks
    packages = [ pkgs.python3 pkgs.jq ];

    # ALTO scripts
    scripts = {
      # First-time project setup
      alto-setup = {
        exec = ''
          echo "ALTO Setup"
          echo "=========="
          echo ""

          # Check if already initialized
          if [ -f objective.md ]; then
            echo "Project already initialized (objective.md exists)."
            echo "Use 'alto-feature' to start a new feature."
            exit 0
          fi

          # Create objective.md template
          cat > objective.md << 'OBJECTIVE_EOF'
# Project Objective

## Overview
<!-- Describe what this project does -->

## Feature 1: [Feature Name]

### Goal
<!-- What should this feature accomplish? -->

### Requirements
- 1.1 [Requirement]
- 1.2 [Requirement]

### Definition of Done
- [ ] [Criteria]
- [ ] [Criteria]
- [ ] `make check` passes (or equivalent)

OBJECTIVE_EOF

          echo "Created objective.md"
          echo ""
          echo "Next steps:"
          echo "1. Edit objective.md to describe your project"
          echo "2. Run 'claude' and describe what you want to build"
          echo "3. ALTO will handle architecture, planning, and execution"
        '';
        description = "Initialize ALTO for a new project";
      };

      # Start a new feature (interactive, runs in Claude)
      alto-feature = {
        exec = ''
          echo "Starting new feature setup..."
          echo ""
          echo "This will:"
          echo "1. Mark previous feature complete (if any)"
          echo "2. Create a new run branch"
          echo "3. Guide you through feature definition"
          echo ""
          echo "Run 'claude' and say: /alto-feature-setup"
        '';
        description = "Start a new feature (interactive)";
      };

      # Create new run branch (mechanical)
      alto-new-run = {
        exec = ''
          RUNS_DIR="${cfg.runsDir}"

          # Get next run number
          LAST_RUN=$(git branch -l 'run/*' 2>/dev/null | sed 's/.*run\///' | sort -n | tail -1)
          if [ -z "$LAST_RUN" ]; then
            RUN_NUM=1
          else
            RUN_NUM=$((LAST_RUN + 1))
          fi

          BRANCH_NAME="run/$(printf '%03d' $RUN_NUM)"

          # Create branch
          git checkout -b "$BRANCH_NAME"

          # Reset state
          cat > "$RUNS_DIR/state.json" << STATE_EOF
{
  "protocol": "alto-v1",
  "run_branch": "$BRANCH_NAME",
  "phase": "ARCHITECTURE",
  "current_task_id": null,
  "current_role": null,
  "completed_task_ids": [],
  "last_handoff": null,
  "estimated_tasks": null,
  "replan_every": null,
  "needs_architect": false,
  "updated_at": "$(date -Iseconds)"
}
STATE_EOF

          echo "Created branch: $BRANCH_NAME"
          echo "State reset to ARCHITECTURE phase"
        '';
        description = "Create new run branch and reset state";
      };

      # Clean previous run artifacts (mechanical)
      alto-clean = {
        exec = ''
          RUNS_DIR="${cfg.runsDir}"

          # Remove stale arbiter trigger
          rm -f "$RUNS_DIR/arbiter/pending.json"

          # Clear tasks (but keep handoffs for context)
          rm -f "$RUNS_DIR/tasks/"*.md 2>/dev/null

          # Clear milestones/decisions (regenerated each run)
          rm -f "$RUNS_DIR/milestones.md" "$RUNS_DIR/decisions.md" 2>/dev/null

          echo "Cleaned previous run artifacts"
          echo "Handoffs preserved in $RUNS_DIR/handoffs/"
        '';
        description = "Clean previous run artifacts";
      };

      # Show ALTO status
      alto-status = {
        exec = ''
          RUNS_DIR="${cfg.runsDir}"

          if [ ! -f "$RUNS_DIR/state.json" ]; then
            echo "ALTO not initialized. Run 'alto-setup' first."
            exit 1
          fi

          echo "ALTO Status"
          echo "==========="
          echo "Branch: $(jq -r '.run_branch // "none"' "$RUNS_DIR/state.json")"
          echo "Phase: $(jq -r '.phase // "none"' "$RUNS_DIR/state.json")"
          echo "Current Task: $(jq -r '.current_task_id // "none"' "$RUNS_DIR/state.json")"
          echo "Completed: $(jq -r '.completed_task_ids | length' "$RUNS_DIR/state.json") tasks"

          echo ""
          echo "Recent handoffs:"
          ls -t "$RUNS_DIR/handoffs/" 2>/dev/null | head -5 || echo "  (none)"
        '';
        description = "Show ALTO status";
      };
    };

    # Enable Claude Code integration
    claude.code.enable = true;

    # Permissions via native devenv options (per-tool structure)
    claude.code.permissions = {
      Bash = {
        allow = map (cmd: "${cmd}:*") cfg.permissions.allowBash;
        deny = map (cmd: "${cmd}:*") cfg.permissions.denyBash;
      };
      Read = {
        deny = cfg.permissions.denyRead;
      };
    };

    # MCP servers via native devenv options
    claude.code.mcpServers = {
      devenv = {
        type = "stdio";
        command = "devenv";
        args = [ "mcp" ];
        env = { DEVENV_ROOT = "."; };
      };
    };

    # Hooks via native devenv options (now supports all hookTypes as strings)
    claude.code.hooks = {
      # SessionStart hook
      session-start = {
        hookType = "SessionStart";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-start.py";
      };

      # PostToolUse hooks for different tools
      tool-record-bash = {
        hookType = "PostToolUse";
        matcher = "Bash";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tool-record.py";
      };
      tool-record-edit = {
        hookType = "PostToolUse";
        matcher = "Edit";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tool-record.py";
      };
      tool-record-write = {
        hookType = "PostToolUse";
        matcher = "Write";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tool-record.py";
      };

      # PermissionRequest hook
      permission-record = {
        hookType = "PermissionRequest";
        matcher = "*";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/permission-record.py";
      };

      # Stop hooks
      usage-record-stop = {
        hookType = "Stop";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/usage-record.py";
      };
      arbiter-scheduler-stop = {
        hookType = "Stop";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/arbiter-scheduler.py";
      };
      session-summary-stop = {
        hookType = "Stop";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-summary.py";
      };

      # SubagentStop hooks
      usage-record-subagent = {
        hookType = "SubagentStop";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/usage-record.py";
      };
      arbiter-scheduler-subagent = {
        hookType = "SubagentStop";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/arbiter-scheduler.py";
      };
      session-summary-subagent = {
        hookType = "SubagentStop";
        command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-summary.py";
      };
    };

    # Agents via native devenv options (now supports model)
    claude.code.agents = {
      alto-planner = {
        description = "Creates task files from milestones. Use after architecture phase to generate next batch of tasks.";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
        model = cfg.planning.plannerModel;
        prompt = readAgentPrompt "alto-planner";
      };
      alto-feature-finder = {
        description = "Analyzes codebase and objective.md to identify features and suggest next steps. Use when starting a new feature.";
        tools = [ "Read" "Grep" "Glob" "LS" ];
        model = "opus";
        prompt = readAgentPrompt "alto-feature-finder";
      };
      alto-backend = {
        description = "Implements backend tasks only. Use for API, ingestion, DB, workers, and server-side logic.";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
        model = "opus";
        prompt = readAgentPrompt "alto-backend";
      };
      alto-frontend = {
        description = "Implements frontend tasks only. Use for UI, charts, client state, and frontend build tooling.";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
        model = "opus";
        prompt = readAgentPrompt "alto-frontend";
      };
      alto-qa = {
        description = "Runs checks/tests, diagnoses failures, and fixes them with minimal diffs. Use when check_command fails or to stabilize before commit.";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
        model = "opus";
        prompt = readAgentPrompt "alto-qa";
      };
      alto-docs = {
        description = "Writes implementation documentation for readers. Updates docs/ based on plan structure.";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
        model = "opus";
        prompt = readAgentPrompt "alto-docs";
      };
      alto-gitops = {
        description = "Handles branch/commit/push hygiene. Use after a task passes checks.";
        tools = [ "Read" "Edit" "Bash" ];
        model = "opus";
        prompt = readAgentPrompt "alto-gitops";
      };
      alto-recorder = {
        description = "Records task changes in handoffs. Internal coordination for task-to-task context.";
        tools = [ "Read" "Edit" ];
        model = "opus";
        prompt = readAgentPrompt "alto-recorder";
      };
      alto-reviewer = {
        description = "Reviews code quality after role agent completes. Can reject back to role agent.";
        tools = [ "Read" "Bash" ];
        model = "opus";
        prompt = readAgentPrompt "alto-reviewer";
      };
      alto-enforcer = {
        description = "Enforces ALTO protocol compliance. Checks handoffs, file locations, state updates.";
        tools = [ "Read" ];
        model = "opus";
        prompt = readAgentPrompt "alto-enforcer";
      };
      alto-arbiter = {
        description = "Periodic blackhat checkpoint auditor. Runs only when runs/arbiter/pending.json exists. Decides if human review is needed.";
        tools = [ "Read" "Grep" "Glob" "LS" "Bash" "Edit" ];
        model = "opus";
        prompt = readAgentPrompt "alto-arbiter";
      };
    };

    # Deploy ALTO files using tasks (runs before shell entry, skips if up-to-date)
    tasks."alto:deploy" = {
      exec = ''
        ALTO_SRC="${altoSrc}"
        RUNS_DIR="${cfg.runsDir}"

        # Create .claude directory for hooks and skills
        mkdir -p .claude/hooks .claude/skills

        # Copy hook scripts (referenced by native hook commands)
        cp -r "$ALTO_SRC"/hooks/*.py .claude/hooks/ 2>/dev/null || true

        # Copy ALTO protocol skills
        cp -r "$ALTO_SRC"/skills/alto-protocol .claude/skills/ 2>/dev/null || true
        cp -r "$ALTO_SRC"/skills/alto-feature-setup .claude/skills/ 2>/dev/null || true

        ${lib.optionalString cfg.includeSpawnerSkills ''
          cp -r "$ALTO_SRC"/skills/spawner .claude/skills/ 2>/dev/null || true
        ''}

        # Create runs directory structure
        mkdir -p "$RUNS_DIR"/{tasks,handoffs,arbiter/checkpoints,review,sessions,usage,tools}

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

        # Initialize arbiter config (always overwrite to keep in sync)
        cat > "$RUNS_DIR/arbiter/config.json" << 'ARBITER_EOF'
{
  "max_lines_changed_without_human": ${toString cfg.arbiter.maxLinesChanged},
  "max_files_changed_without_human": ${toString cfg.arbiter.maxFilesChanged},
  "token_checkpoint_interval": ${toString cfg.arbiter.tokenCheckpointInterval},
  "task_checkpoint_interval": ${toString cfg.arbiter.taskCheckpointInterval},
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
        cat > "$RUNS_DIR/planning-config.json" << 'PLANNING_EOF'
{
  "require_approval": ${lib.boolToString cfg.planning.requireApproval},
  "replan_strategy": "${cfg.planning.replanStrategy}",
  "fixed_batch_size": ${toString cfg.planning.fixedBatchSize},
  "architect_model": "${cfg.planning.architectModel}",
  "planner_model": "${cfg.planning.plannerModel}"
}
PLANNING_EOF

        # Copy CLAUDE.md (always overwrite to keep protocol in sync)
        cp "$ALTO_SRC/templates/CLAUDE.md.template" CLAUDE.md 2>/dev/null || true

        echo "ALTO deployed"
      '';
      # Run before shell entry
      before = [ "devenv:enterShell" ];
    };
  };
}

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

    # Orchestrator selection
    orchestrator = lib.mkOption {
      type = lib.types.enum [ "setup" "build" ];
      default = "build";
      description = ''
        Which orchestrator mode to use:
        - setup: Human-interactive phase. Feature definition, configuration, cleanup, onboarding.
        - build: Autonomous execution. Full protocol: architecture, planning, execution, replan.

        Note: "dev" mode is for ALTO development only and uses the tracked agents/ directory.
      '';
    };

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

    # Permission configuration
    permissions = {
      # Global permission profile
      profile = lib.mkOption {
        type = lib.types.enum [ "autonomous" "supervised" "locked" ];
        default = "supervised";
        description = ''
          Permission profile:
          - autonomous: broad allows, minimal prompts (for trusted environments)
          - supervised: balanced allows/asks, safe defaults (recommended)
          - locked: minimal allows, strict denies (for untrusted code)
        '';
      };

      # Three-tier bash permissions (allow > ask > deny precedence: deny wins)
      allowBash = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "ls" "cat" "head" "tail" "grep" "find" "echo" "pwd" "wc" ];
        description = "Bash commands to allow without prompting (Tier 1 - auto-allow)";
      };

      askBash = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "git" "npm" "pnpm" "yarn" "make" "docker" "python" "python3" "node" ];
        description = "Bash commands that require confirmation (Tier 2 - prompt)";
      };

      denyBash = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "rm -rf" "sudo" "chmod" "chown" "curl|sh" "wget|sh" "git push -f" "git reset --hard" ];
        description = "Bash commands to always deny (Tier 3 - blocked)";
      };

      denyRead = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "./.env" "./.env.*" "./secrets/**" "**/*.pem" "**/*id_rsa*" "**/credentials*" ];
        description = "File patterns to deny reading";
      };
    };

    # Per-agent permission configuration
    # Each agent has: permissionMode, tools, and optional Bash restrictions
    # permissionMode: plan (read-only), acceptEdits (auto-approve edits), default (prompts)
    agentPermissions = {
      # Planner - creates tasks, no bash needed
      alto-planner = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "acceptEdits";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
          # No Bash - planners don't execute code
        };
        description = "Permission config for alto-planner agent";
      };

      # Feature finder - analysis only, read-only
      alto-feature-finder = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "plan";
          tools = [ "Read" "Grep" "Glob" "LS" ];
          # No Bash, no Edit - pure analysis
        };
        description = "Permission config for alto-feature-finder agent";
      };

      # Backend - full implementation permissions
      alto-backend = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "acceptEdits";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
          allowBash = [ "npm" "make" "python" "python3" "pip" "cargo" "go" ];
          askBash = [ "docker" "docker compose" ];
        };
        description = "Permission config for alto-backend agent";
      };

      # Frontend - full implementation permissions
      alto-frontend = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "acceptEdits";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
          allowBash = [ "npm" "pnpm" "yarn" "node" "npx" ];
          askBash = [ "vite" "webpack" "esbuild" ];
        };
        description = "Permission config for alto-frontend agent";
      };

      # QA - testing permissions
      alto-qa = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "acceptEdits";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
          allowBash = [ "npm test" "npm run test" "pytest" "cargo test" "go test" "make test" ];
          askBash = [ "npm install" "pip install" ];
        };
        description = "Permission config for alto-qa agent";
      };

      # Docs - documentation only
      alto-docs = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "acceptEdits";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
          # No Bash - docs don't need to execute
        };
        description = "Permission config for alto-docs agent";
      };

      # GitOps - git operations with careful tiers
      alto-gitops = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "default";  # Prompts for each action
          tools = [ "Read" "Grep" "Glob" "LS" "Bash" ];
          allowBash = [ "git status" "git log" "git diff" "git branch" "git show" ];
          askBash = [ "git add" "git commit" "git checkout" "git merge" "git pull" ];
          denyBash = [ "git push -f" "git reset --hard" "git clean -fd" ];
        };
        description = "Permission config for alto-gitops agent";
      };

      # Reviewer - read-only code review
      alto-reviewer = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "plan";
          tools = [ "Read" "Grep" "Glob" "LS" ];
          # No Bash, no Edit - reviewers only read
        };
        description = "Permission config for alto-reviewer agent";
      };

      # Arbiter - minimal permissions for human review decisions
      alto-arbiter = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "plan";
          tools = [ "Read" "Grep" "Glob" ];
          # Minimal - just reads state and makes decisions
        };
        description = "Permission config for alto-arbiter agent";
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

    # Verification hooks - auto-run after file edits
    verification = {
      typecheck = {
        enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Run typecheck after editing source files";
        };
        command = lib.mkOption {
          type = lib.types.str;
          default = "pnpm type:check";
          description = "Typecheck command to run";
        };
        matcher = lib.mkOption {
          type = lib.types.str;
          default = "Edit:*.ts|Edit:*.tsx|Write:*.ts|Write:*.tsx";
          description = "File patterns to trigger typecheck (PostToolUse matcher)";
        };
      };

      lint = {
        enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Run linter after editing source files";
        };
        command = lib.mkOption {
          type = lib.types.str;
          default = "pnpm lint";
          description = "Lint command to run";
        };
        matcher = lib.mkOption {
          type = lib.types.str;
          default = "Edit:*.ts|Edit:*.tsx|Edit:*.js|Edit:*.jsx|Write:*.ts|Write:*.tsx|Write:*.js|Write:*.jsx";
          description = "File patterns to trigger lint (PostToolUse matcher)";
        };
      };

      test = {
        enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = "Run tests after editing test files";
        };
        command = lib.mkOption {
          type = lib.types.str;
          default = "npm test -- --related";
          description = "Test command to run";
        };
        matcher = lib.mkOption {
          type = lib.types.str;
          default = "Edit:*.test.*|Edit:*.spec.*|Write:*.test.*|Write:*.spec.*";
          description = "File patterns to trigger tests (PostToolUse matcher)";
        };
      };

      custom = lib.mkOption {
        type = lib.types.listOf (lib.types.submodule {
          options = {
            name = lib.mkOption {
              type = lib.types.str;
              description = "Hook name identifier";
            };
            command = lib.mkOption {
              type = lib.types.str;
              description = "Command to run";
            };
            matcher = lib.mkOption {
              type = lib.types.str;
              description = "PostToolUse matcher pattern";
            };
            timeout = lib.mkOption {
              type = lib.types.int;
              default = 30000;
              description = "Timeout in milliseconds";
            };
          };
        });
        default = [];
        description = "Custom verification hooks";
        example = lib.literalExpression ''
          [
            { name = "security-check"; command = "./scripts/security.sh"; matcher = "Edit:src/auth/*"; }
            { name = "format"; command = "prettier --write"; matcher = "Write:*.json"; }
          ]
        '';
      };
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
      # First-time project setup info
      alto-setup = {
        exec = ''
          echo "ALTO Setup"
          echo "=========="
          echo ""
          echo "Run 'claude' to start."
          echo "ALTO will create objective.md and guide you through setup."
        '';
        description = "Show ALTO setup instructions";
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

      # Restart Claude with fresh devenv config
      alto-restart = {
        exec = ''
          # Find Claude's PID (parent of this bash process)
          CLAUDE_PID=$(ps -o ppid= -p $$ | tr -d ' ')

          if [ -z "$CLAUDE_PID" ] || [ "$CLAUDE_PID" = "1" ]; then
            echo "Error: Could not find Claude process"
            exit 1
          fi

          echo "Restarting Claude with fresh configuration..."
          echo "Session will continue automatically."

          # Spawn background process to:
          # 1. Wait for this script to return to Claude
          # 2. Kill Claude
          # 3. Reload devenv and restart Claude with --continue
          nohup sh -c "
            sleep 0.5
            kill $CLAUDE_PID 2>/dev/null
            sleep 0.2
            cd \"$PWD\"
            exec devenv shell claude -- --continue
          " > /tmp/alto-restart.log 2>&1 &

          # Give background process time to start
          sleep 0.1
        '';
        description = "Restart Claude with fresh devenv configuration";
      };

      # Show ALTO status
      alto-status = {
        exec = ''
          RUNS_DIR="${cfg.runsDir}"

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
          CURRENT_ORCH="${cfg.orchestrator}"

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
        '';
        description = "Show ALTO status";
      };

      # Switch between orchestrators
      alto-switch = {
        exec = ''
          TARGET="$1"
          CURRENT="${cfg.orchestrator}"

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
            echo ""
            echo "To switch, update devenv.nix:"
            echo "  alto.orchestrator = \"setup\";  # or \"build\""
            echo ""
            echo "Then run: alto-restart"
            exit 0
          fi

          if [ "$TARGET" != "setup" ] && [ "$TARGET" != "build" ]; then
            echo "Error: Invalid orchestrator '$TARGET'"
            echo "Valid options: setup, build"
            exit 1
          fi

          if [ "$TARGET" = "$CURRENT" ]; then
            echo "Already using '$TARGET' orchestrator."
            exit 0
          fi

          echo "Switching from '$CURRENT' to '$TARGET'..."
          echo ""
          echo "To complete the switch:"
          echo ""
          echo "1. Update devenv.nix:"
          echo "   alto.orchestrator = \"$TARGET\";"
          echo ""
          echo "2. Run: alto-restart"
          echo ""
          echo "This will reload devenv and continue your Claude session."
        '';
        description = "Switch between setup and build orchestrators";
      };
    };

    # Enable Claude Code integration
    claude.code.enable = true;

    # Permissions via native devenv options
    # Three tiers: allow (auto-approve), ask (prompt), deny (block)
    claude.code.permissions = {
      # Global permission mode based on profile
      defaultMode = {
        autonomous = "acceptEdits";
        supervised = "default";
        locked = "plan";
      }.${cfg.permissions.profile};

      # Prevent dangerous bypass mode in supervised/locked profiles
      disableBypassPermissionsMode = cfg.permissions.profile != "autonomous";

      # Per-tool permission rules
      rules = {
        Bash = {
          allow = map (cmd: "${cmd}:*") cfg.permissions.allowBash;
          ask = map (cmd: "${cmd}:*") cfg.permissions.askBash;
          deny = map (cmd: "${cmd}:*") cfg.permissions.denyBash;
        };
        Read = {
          deny = cfg.permissions.denyRead;
        };
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

    # Hooks - deployed based on orchestrator selection
    # Shared hooks are deployed to all orchestrators
    # Build-specific hooks only deployed when orchestrator == "build"
    claude.code.hooks = lib.mkMerge [
      # Shared hooks (all orchestrators)
      {
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

        # PreToolUse hook for changelog check
        changelog-check = {
          hookType = "PreToolUse";
          matcher = "Bash";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/changelog-check.py";
        };

        # Stop hooks (shared)
        usage-record-stop = {
          hookType = "Stop";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/usage-record.py";
        };
        session-summary-stop = {
          hookType = "Stop";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-summary.py";
        };

        # SubagentStop hooks (shared)
        usage-record-subagent = {
          hookType = "SubagentStop";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/usage-record.py";
        };
        session-summary-subagent = {
          hookType = "SubagentStop";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-summary.py";
        };
      }

      # Build-specific hooks (autonomous execution)
      (lib.mkIf (cfg.orchestrator == "build") {
        # Dynamic verification (reads from runs/verification-config.json)
        verify-dynamic = {
          hookType = "PostToolUse";
          matcher = "Edit|Write";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/verify-dynamic.py";
        };

        # Arbiter scheduler (triggers checkpoints)
        arbiter-scheduler-stop = {
          hookType = "Stop";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/arbiter-scheduler.py";
        };
        arbiter-scheduler-subagent = {
          hookType = "SubagentStop";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/arbiter-scheduler.py";
        };

        # Handoff validation
        handoff-validate-subagent = {
          hookType = "SubagentStop";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/handoff-validate.py";
        };
      })

      # Verification hooks (user-configured, static) - builder only
      (lib.mkIf (cfg.orchestrator == "build" && cfg.verification.typecheck.enable) {
        verify-typecheck = {
          hookType = "PostToolUse";
          matcher = cfg.verification.typecheck.matcher;
          command = cfg.verification.typecheck.command;
        };
      })
      (lib.mkIf (cfg.orchestrator == "build" && cfg.verification.lint.enable) {
        verify-lint = {
          hookType = "PostToolUse";
          matcher = cfg.verification.lint.matcher;
          command = cfg.verification.lint.command;
        };
      })
      (lib.mkIf (cfg.orchestrator == "build" && cfg.verification.test.enable) {
        verify-test = {
          hookType = "PostToolUse";
          matcher = cfg.verification.test.matcher;
          command = cfg.verification.test.command;
        };
      })
      (lib.mkIf (cfg.orchestrator == "build") (lib.listToAttrs (map (hook: {
        name = "verify-custom-${hook.name}";
        value = {
          hookType = "PostToolUse";
          matcher = hook.matcher;
          command = hook.command;
          timeout = hook.timeout;
        };
      }) cfg.verification.custom)))
    ];

    # Agents with per-agent permissionMode from agentPermissions config
    # Deployed based on orchestrator selection
    claude.code.agents = lib.mkMerge [
      # Setup-specific agents (minimal - human-interactive phase)
      (lib.mkIf (cfg.orchestrator == "setup") {
        alto-feature-finder = {
          description = "Analyzes codebase and objective.md to identify features and suggest next steps. Use when starting a new feature.";
          tools = cfg.agentPermissions.alto-feature-finder.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-feature-finder.permissionMode;
          prompt = readAgentPrompt "alto-feature-finder";
        };
      })

      # Build-specific agents (full autonomous execution)
      (lib.mkIf (cfg.orchestrator == "build") {
        alto-planner = {
          description = "Creates task files from milestones. Use after architecture phase to generate next batch of tasks.";
          tools = cfg.agentPermissions.alto-planner.tools;
          model = cfg.planning.plannerModel;
          permissionMode = cfg.agentPermissions.alto-planner.permissionMode;
          prompt = readAgentPrompt "alto-planner";
        };
        alto-feature-finder = {
          description = "Analyzes codebase and objective.md to identify features and suggest next steps. Use when starting a new feature.";
          tools = cfg.agentPermissions.alto-feature-finder.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-feature-finder.permissionMode;
          prompt = readAgentPrompt "alto-feature-finder";
        };
        alto-backend = {
          description = "Implements backend tasks only. Use for API, ingestion, DB, workers, and server-side logic.";
          tools = cfg.agentPermissions.alto-backend.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-backend.permissionMode;
          prompt = readAgentPrompt "alto-backend";
        };
        alto-frontend = {
          description = "Implements frontend tasks only. Use for UI, charts, client state, and frontend build tooling.";
          tools = cfg.agentPermissions.alto-frontend.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-frontend.permissionMode;
          prompt = readAgentPrompt "alto-frontend";
        };
        alto-qa = {
          description = "Writes tests for implementations and fixes failures. Runs after role agents to ensure test coverage.";
          tools = cfg.agentPermissions.alto-qa.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-qa.permissionMode;
          prompt = readAgentPrompt "alto-qa";
        };
        alto-docs = {
          description = "Writes implementation documentation for readers. Updates docs/ based on plan structure.";
          tools = cfg.agentPermissions.alto-docs.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-docs.permissionMode;
          prompt = readAgentPrompt "alto-docs";
        };
        alto-gitops = {
          description = "Handles branch/commit/push hygiene. Use after a task passes checks.";
          tools = cfg.agentPermissions.alto-gitops.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-gitops.permissionMode;
          prompt = readAgentPrompt "alto-gitops";
        };
        alto-reviewer = {
          description = "Reviews code quality after role agent completes. Can reject back to role agent.";
          tools = cfg.agentPermissions.alto-reviewer.tools;
          model = "sonnet";
          permissionMode = cfg.agentPermissions.alto-reviewer.permissionMode;
          prompt = readAgentPrompt "alto-reviewer";
        };
        alto-arbiter = {
          description = "Periodic blackhat checkpoint auditor. Runs only when runs/arbiter/pending.json exists. Decides if human review is needed.";
          tools = cfg.agentPermissions.alto-arbiter.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-arbiter.permissionMode;
          prompt = readAgentPrompt "alto-arbiter";
        };
      })
    ];

    # Deploy ALTO files using tasks (runs before shell entry)
    tasks."alto:deploy" = {
      exec = ''
        ALTO_SRC="${altoSrc}"
        RUNS_DIR="${cfg.runsDir}"

        # Create .claude directory for hooks and skills
        mkdir -p .claude/hooks .claude/skills

        # Copy hook scripts (referenced by native hook commands)
        cp -r "$ALTO_SRC"/hooks/*.py .claude/hooks/ 2>/dev/null || true

        # Copy shared ALTO skills (all orchestrators)
        cp -r "$ALTO_SRC"/skills/alto-protocol .claude/skills/ 2>/dev/null || true
        cp -r "$ALTO_SRC"/skills/alto-feature-setup .claude/skills/ 2>/dev/null || true
        cp -r "$ALTO_SRC"/skills/alto-configure .claude/skills/ 2>/dev/null || true
        cp -r "$ALTO_SRC"/skills/scope-discipline .claude/skills/ 2>/dev/null || true

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
        cat > "$RUNS_DIR/orchestrator.json" << 'ORCH_EOF'
{
  "orchestrator": "${cfg.orchestrator}",
  "updated_at": "$(date -Iseconds)"
}
ORCH_EOF

        # Copy orchestrator-specific CLAUDE.md (always overwrite to match orchestrator)
        # setup = human-interactive, build = autonomous execution
        # Remove first to handle read-only files from previous deploys
        rm -f CLAUDE.md 2>/dev/null || true
        cp "$ALTO_SRC/templates/CLAUDE.md.${cfg.orchestrator}" CLAUDE.md 2>/dev/null || true

        echo "ALTO deployed"
      '';
      # Run before shell entry
      before = [ "devenv:enterShell" ];
    };
  };
}

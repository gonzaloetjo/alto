{ config, lib, pkgs, ... }:

let
  cfg = config.alto;
  # Use config.devenv.root for monorepo support (devenv 1.10+)
  # Falls back to ./. for compatibility
  altoSrc = config.devenv.root or ./.;

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
    # Orchestrator selection
    orchestrator = lib.mkOption {
      type = lib.types.enum [ "setup" "build" "dev" ];
      default = "setup";
      description = ''
        Which orchestrator mode to use:
        - setup: Human-interactive phase. Feature definition, configuration, cleanup, onboarding.
        - build: Autonomous execution. Full protocol: architecture, planning, execution, replan.
        - dev: ALTO development mode. Single alto-dev agent with dev-guide skill.
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

      # Dev - full permissions for ALTO development
      alto-dev = lib.mkOption {
        type = lib.types.attrs;
        default = {
          permissionMode = "acceptEdits";
          tools = [ "Read" "Write" "Grep" "Glob" "Edit" "Bash" "WebFetch" ];
          allowBash = [ "git" "nix-instantiate" "python3" "gh" ];
          askBash = [ "devenv" ];
        };
        description = "Permission config for alto-dev agent";
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

    # Debug mode - enables verbose event logging for meta-development
    debug = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Enable debug mode with verbose event logging.
        Logs ALTO events to runs/logs/events.jsonl for analysis.
        Use for ALTO development and testing, not for normal projects.
      '';
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

  config = {
    # Ensure python3, jq, and yq are available for hooks and test harness
    packages = [ pkgs.python3 pkgs.jq pkgs.yq-go ];

    # Common environment variables available to all scripts and hooks
    env = {
      ALTO_SRC = altoSrc;
      ALTO_RUNS_DIR = cfg.runsDir;
      ALTO_ORCHESTRATOR = cfg.orchestrator;
      ALTO_DEBUG = lib.boolToString cfg.debug;
    };

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

      # Initialize a test project (also available as scripts/alto-init-test.sh)
      alto-init-test = {
        exec = ''
          ${altoSrc}/scripts/alto-init-test.sh "$@"
        '';
        description = "Create/update a test project that imports local ALTO";
      };

      # Nuke everything - full reset of ALTO state
      alto-nuke = {
        exec = ''
          echo "Nuking ALTO state..."
          rm -rf .claude/ runs/ CLAUDE.md objective.md 2>/dev/null || true
          echo "Reloading environment..."
          direnv reload 2>/dev/null || echo "Run 'direnv reload' or re-enter the directory"
        '';
        description = "Full reset - removes .claude/, runs/, CLAUDE.md, objective.md";
      };

      # Test harness for meta-development
      # WARNING: Uses --dangerously-skip-permissions for automated testing.
      # Only run with trusted scenarios. For CI/autonomous use, consider containers.
      # See: https://devenv.sh/containers/
      alto-test-run = {
        exec = ''
          export ALTO_SRC="${altoSrc}"
          exec "${altoSrc}/scripts/alto-test-run.sh" "$@"
        '';
        description = "Run isolated ALTO test scenarios";
      };

      # Query event logs (debug mode)
      alto-logs = {
        exec = ''
          export RUNS_DIR="${cfg.runsDir}"
          exec "${altoSrc}/scripts/alto-logs.sh" "$@"
        '';
        description = "Query ALTO event logs (debug mode)";
      };

      # Show ALTO status
      alto-status = {
        exec = ''
          export RUNS_DIR="${cfg.runsDir}"
          export ORCHESTRATOR="${cfg.orchestrator}"
          exec "${altoSrc}/scripts/alto-status.sh" "$@"
        '';
        description = "Show ALTO status";
      };

      # Switch between orchestrators
      alto-switch = {
        exec = ''
          export RUNS_DIR="${cfg.runsDir}"
          export ALTO_SRC="${altoSrc}"
          export JQ_BIN="${pkgs.jq}/bin/jq"
          export SED_BIN="${pkgs.gnused}/bin/sed"
          exec "${altoSrc}/scripts/alto-switch.sh" "$@"
        '';
        description = "Switch orchestrator mode and start Claude";
      };

      # Shell wrapper for automatic session resume per mode
      alto = {
        exec = ''
          export RUNS_DIR="${cfg.runsDir}"
          export JQ_BIN="${pkgs.jq}/bin/jq"
          exec "${altoSrc}/scripts/alto.sh" "$@"
        '';
        description = "Start Claude with automatic session resume per mode";
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
    # Note: disableBypassPermissionsMode removed - devenv expects boolean but
    # Claude Code expects string "disable". This is a devenv bug.
    # TODO: Re-enable when devenv fixes this

    # MCP servers via native devenv options
    claude.code.mcpServers = {
      devenv = {
        type = "stdio";
        command = "devenv";
        args = [ "mcp" ];
        env = { DEVENV_ROOT = altoSrc; };
      };
    };

    # Expose alto scripts as Claude Code slash commands
    claude.code.commands = {
      alto-status = {
        exec = "alto-status";
        description = "Show ALTO status (phase, tasks, orchestrator)";
      };
      alto-logs = {
        exec = "alto-logs --metrics";
        description = "Show ALTO event metrics (debug mode)";
      };
      alto-clean = {
        exec = "alto-clean";
        description = "Clean previous run artifacts";
      };
    };

    # Hooks - deployed based on orchestrator selection
    # Shared hooks are deployed to setup/build orchestrators
    # Dev mode has minimal hooks (just changelog-check)
    claude.code.hooks = lib.mkMerge [
      # Dev-only hooks (minimal for ALTO development)
      (lib.mkIf (cfg.orchestrator == "dev") {
        # PreToolUse hook for changelog check
        changelog-check = {
          hookType = "PreToolUse";
          matcher = "Bash";
          command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/changelog-check.py";
        };
      })

      # Shared hooks (setup and build orchestrators)
      (lib.mkIf (cfg.orchestrator != "dev") {
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
      })

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

      # Dev-specific agents (ALTO development)
      (lib.mkIf (cfg.orchestrator == "dev") {
        alto-dev = {
          description = "ALTO development agent. Full file access, bash, and WebFetch for documentation.";
          tools = cfg.agentPermissions.alto-dev.tools;
          model = "opus";
          permissionMode = cfg.agentPermissions.alto-dev.permissionMode;
          prompt = readAgentPrompt "alto-dev";
        };
      })
    ];

    # Deploy ALTO files using tasks (runs before shell entry)
    # Uses status check for caching - skips if orchestrator matches (devenv 1.2+)
    tasks."alto:deploy" = {
      exec = ''
        export ALTO_SRC="${altoSrc}"
        export RUNS_DIR="${cfg.runsDir}"
        export ORCHESTRATOR="${cfg.orchestrator}"
        export DEBUG_ENABLED="${lib.boolToString cfg.debug}"
        export INCLUDE_SPAWNER_SKILLS="${lib.boolToString cfg.includeSpawnerSkills}"
        export ARBITER_MAX_LINES="${toString cfg.arbiter.maxLinesChanged}"
        export ARBITER_MAX_FILES="${toString cfg.arbiter.maxFilesChanged}"
        export ARBITER_TOKEN_INTERVAL="${toString cfg.arbiter.tokenCheckpointInterval}"
        export ARBITER_TASK_INTERVAL="${toString cfg.arbiter.taskCheckpointInterval}"
        export PLANNING_REQUIRE_APPROVAL="${lib.boolToString cfg.planning.requireApproval}"
        export PLANNING_REPLAN_STRATEGY="${cfg.planning.replanStrategy}"
        export PLANNING_FIXED_BATCH_SIZE="${toString cfg.planning.fixedBatchSize}"
        export PLANNING_ARCHITECT_MODEL="${cfg.planning.architectModel}"
        export PLANNING_PLANNER_MODEL="${cfg.planning.plannerModel}"
        exec "${altoSrc}/scripts/alto-deploy.sh"
      '';
      # Status check for caching - returns 0 if deploy can be skipped
      # Skips if orchestrator.json exists and matches current orchestrator
      status = ''
        [ -f "${cfg.runsDir}/orchestrator.json" ] && \
        [ "$(${pkgs.jq}/bin/jq -r '.orchestrator' "${cfg.runsDir}/orchestrator.json" 2>/dev/null)" = "${cfg.orchestrator}" ] && \
        [ -d ".claude/hooks" ] && \
        [ -f "CLAUDE.md" ]
      '';
      # Run before shell entry
      before = [ "devenv:enterShell" ];
    };

    # Force update ALTO to latest version (bypasses Nix cache)
    # If this script is broken, run: bash <(curl -fsSL https://raw.githubusercontent.com/gonzaloetjo/alto/main/scripts/alto-reset.sh)
    scripts.alto-update = {
      exec = ''
        set -e
        echo "=== ALTO Update ==="

        # Ensure ?ref=main is in devenv.yaml
        if grep -q 'github:gonzaloetjo/alto$' devenv.yaml 2>/dev/null; then
          echo "[1/4] Adding ?ref=main to devenv.yaml..."
          ${pkgs.gnused}/bin/sed -i 's|github:gonzaloetjo/alto$|github:gonzaloetjo/alto?ref=main|' devenv.yaml
        else
          echo "[1/4] devenv.yaml OK"
        fi

        echo "[2/4] Removing .devenv and devenv.lock..."
        rm -rf .devenv devenv.lock

        echo "[3/4] Prefetching latest ALTO from GitHub..."
        nix flake prefetch github:gonzaloetjo/alto --refresh 2>/dev/null || true

        echo "[4/4] Running devenv update..."
        devenv update

        echo ""
        echo "Done! Run 'direnv reload' to activate."
      '';
      description = "Force update ALTO (removes lock, clears cache)";
    };

    # ALTO repo config - Claude edits this line to switch modes
    alto.orchestrator = lib.mkDefault "setup";  # "setup" | "build" | "dev"

    # ALTO source repo uses autonomous mode (auto-approve edits)
    # Consumer projects override this with their own profile
    alto.permissions.profile = lib.mkDefault "autonomous";
  };
}

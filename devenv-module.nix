{ config, lib, pkgs, ... }:

let
  cfg = config.alto;
  altoSrc = ./.;

  # Extract prompt body from agent .md file (everything after the YAML frontmatter)
  readAgentPrompt = file: builtins.readFile file;

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
  };

  config = lib.mkIf cfg.enable {
    # Ensure python3 and jq are available for hooks
    packages = [ pkgs.python3 pkgs.jq ];

    # Enable Claude Code integration
    claude.code.enable = true;

    # Configure permissions
    claude.code.permissions = {
      defaultMode = cfg.permissions.defaultMode;
      allow = map (cmd: "Bash(${cmd}:*)") cfg.permissions.allowBash;
      ask = map (cmd: "Bash(${cmd}:*)") cfg.permissions.askBash;
      deny = (map (pat: "Read(${pat})") cfg.permissions.denyRead)
           ++ (map (cmd: "Bash(${cmd}:*)") cfg.permissions.denyBash);
    };

    # Configure MCP servers - include devenv's built-in MCP for config assistance
    claude.code.mcpServers = {
      devenv = {
        type = "stdio";
        command = "devenv";
        args = [ "mcp" ];
        env = {
          DEVENV_ROOT = config.devenv.root;
        };
      };
    };

    # Configure hooks
    claude.code.hooks = {
      SessionStart = [
        {
          hooks = [{
            type = "command";
            command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-start.py";
          }];
        }
      ];

      PostToolUse = [
        {
          matcher = "Bash";
          hooks = [{
            type = "command";
            command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tool-record.py";
          }];
        }
        {
          matcher = "Edit";
          hooks = [{
            type = "command";
            command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tool-record.py";
          }];
        }
        {
          matcher = "Write";
          hooks = [{
            type = "command";
            command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/tool-record.py";
          }];
        }
      ];

      PermissionRequest = [
        {
          matcher = "*";
          hooks = [{
            type = "command";
            command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/permission-record.py";
          }];
        }
      ];

      Stop = [
        {
          hooks = [
            {
              type = "command";
              command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/usage-record.py";
            }
            {
              type = "command";
              command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/arbiter-scheduler.py";
            }
            {
              type = "command";
              command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-summary.py";
            }
          ];
        }
      ];

      SubagentStop = [
        {
          hooks = [
            {
              type = "command";
              command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/usage-record.py";
            }
            {
              type = "command";
              command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/arbiter-scheduler.py";
            }
            {
              type = "command";
              command = "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-summary.py";
            }
          ];
        }
      ];
    };

    # Configure agents - using native devenv agent format
    claude.code.agents = {
      alto-planner = {
        description = "Generates and maintains runs/plan.md and writes tasks under runs/tasks/. Use at session start.";
        model = "opus";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-planner.md";
      };

      alto-arbiter = {
        description = "Periodic blackhat checkpoint auditor. Runs when runs/arbiter/pending.json exists.";
        model = "opus";
        tools = [ "Read" "Grep" "Glob" "LS" "Bash" "Edit" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-arbiter.md";
      };

      alto-backend = {
        description = "Implements backend tasks. Use for API, DB, workers, server-side logic.";
        model = "sonnet";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-backend.md";
      };

      alto-frontend = {
        description = "Implements frontend tasks. Use for UI, charts, client state, build tooling.";
        model = "opus";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-frontend.md";
      };

      alto-qa = {
        description = "Runs checks/tests, diagnoses failures, fixes with minimal diffs.";
        model = "sonnet";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-qa.md";
      };

      alto-docs = {
        description = "Writes implementation documentation. Updates docs/ based on plan structure.";
        model = "sonnet";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-docs.md";
      };

      alto-gitops = {
        description = "Handles branch/commit/push hygiene. Use after task passes checks.";
        model = "haiku";
        tools = [ "Read" "Edit" "Bash" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-gitops.md";
      };

      alto-recorder = {
        description = "Records task changes in handoffs for task-to-task context.";
        model = "haiku";
        tools = [ "Read" "Edit" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-recorder.md";
      };

      alto-reviewer = {
        description = "Reviews code quality after role agent completes. Can reject back to role.";
        model = "opus";
        tools = [ "Read" "Bash" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-reviewer.md";
      };

      alto-enforcer = {
        description = "Enforces ALTO protocol compliance. Checks handoffs, file locations, state.";
        model = "sonnet";
        tools = [ "Read" ];
        prompt = readAgentPrompt "${altoSrc}/agents/alto-enforcer.md";
      };

      code-simplifier = {
        description = "Simplifies code for clarity and maintainability. Preserves functionality.";
        model = "opus";
        tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
        prompt = readAgentPrompt "${altoSrc}/agents/code-simplifier.md";
      };
    };

    # Deploy ALTO runtime files on shell entry
    # (hooks scripts, skills, runs/ structure, CLAUDE.md, arbiter config)
    enterShell = ''
      _alto_deploy() {
        local ALTO_SRC="${altoSrc}"
        local RUNS_DIR="${cfg.runsDir}"

        echo "ALTO: Deploying runtime files..."

        # Create directories
        mkdir -p .claude/hooks .claude/skills

        # Copy hook scripts (referenced by claude.code.hooks)
        cp -r "$ALTO_SRC"/hooks/*.py .claude/hooks/ 2>/dev/null || true

        # Copy ALTO protocol skills
        cp -r "$ALTO_SRC"/skills/alto-protocol .claude/skills/ 2>/dev/null || true
        cp -r "$ALTO_SRC"/skills/alto-feature-setup .claude/skills/ 2>/dev/null || true

        # Optionally copy spawner skills
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
  "phase": "PLANNING",
  "current_task_id": null,
  "current_role": null,
  "completed_task_ids": [],
  "last_handoff": null,
  "updated_at": null
}
STATE_EOF
        fi

        # Initialize arbiter config
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

        # Copy CLAUDE.md (always overwrite to keep protocol in sync)
        cp "$ALTO_SRC/templates/CLAUDE.md.template" CLAUDE.md 2>/dev/null || true

        echo "ALTO: Ready. Start Claude Code and say 'continue' or '/alto-feature-setup' to begin."
      }

      _alto_deploy
    '';
  };
}

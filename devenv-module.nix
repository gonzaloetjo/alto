{ config, lib, pkgs, ... }:

let
  cfg = config.lca;
  lcaRoot = ./.;

  # Helper to read agent file content
  readAgent = name: builtins.readFile (lcaRoot + "/agents/${name}.md");

  # Helper to read hook file content
  readHook = name: builtins.readFile (lcaRoot + "/hooks/${name}");

in
{
  options.lca = {
    enable = lib.mkEnableOption "LCA Protocol for Claude Code";

    # Arbiter configuration
    arbiter = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable the arbiter agent for human review gates";
      };

      maxLinesChanged = lib.mkOption {
        type = lib.types.int;
        default = 2000;
        description = "Maximum lines changed before requiring human review";
      };

      maxFilesChanged = lib.mkOption {
        type = lib.types.int;
        default = 50;
        description = "Maximum files changed before requiring human review";
      };

      tokenCheckpointInterval = lib.mkOption {
        type = lib.types.int;
        default = 100000;
        description = "Token usage threshold between arbiter checkpoints";
      };

      taskCheckpointInterval = lib.mkOption {
        type = lib.types.int;
        default = 3;
        description = "Number of tasks between arbiter checkpoints";
      };
    };

    # Agent selection
    agents = {
      backend = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-backend agent";
      };

      frontend = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-frontend agent";
      };

      qa = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-qa agent";
      };

      docs = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-docs agent";
      };

      gitops = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-gitops agent";
      };

      planner = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-planner agent";
      };

      recorder = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-recorder agent";
      };

      reviewer = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-reviewer agent";
      };

      enforcer = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable lca-enforcer agent";
      };
    };

    # Hooks configuration
    hooks = {
      sessionStart = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable session-start hook for state tracking";
      };

      sessionSummary = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable session-summary hook";
      };

      toolRecord = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Enable tool-record hook for usage tracking";
      };
    };

    # Runtime directories
    runsDir = lib.mkOption {
      type = lib.types.str;
      default = "runs";
      description = "Directory for LCA runtime state (state.json, tasks/, handoffs/)";
    };

    # Custom role agents (project-specific)
    extraAgents = lib.mkOption {
      type = lib.types.attrsOf (lib.types.submodule {
        options = {
          description = lib.mkOption {
            type = lib.types.str;
            description = "Agent description";
          };
          tools = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ "Read" "Grep" "Glob" "Edit" "Bash" ];
            description = "Tools available to agent";
          };
          model = lib.mkOption {
            type = lib.types.enum [ "opus" "sonnet" "haiku" ];
            default = "sonnet";
            description = "Model to use for agent";
          };
          prompt = lib.mkOption {
            type = lib.types.str;
            description = "Agent prompt/instructions";
          };
        };
      });
      default = {};
      description = "Additional project-specific agents";
    };
  };

  config = lib.mkIf cfg.enable {
    # Create runs directory structure on devenv activation
    enterShell = ''
      mkdir -p ${cfg.runsDir}/{tasks,handoffs,arbiter/checkpoints,review,sessions,usage,tools}

      # Initialize state.json if not exists
      if [ ! -f ${cfg.runsDir}/state.json ]; then
        cat > ${cfg.runsDir}/state.json << 'EOF'
{
  "protocol": "lca-v1",
  "run_branch": null,
  "phase": "PLANNING",
  "current_task_id": null,
  "current_role": null,
  "completed_task_ids": [],
  "last_handoff": null,
  "updated_at": null
}
EOF
      fi

      # Initialize arbiter config if not exists
      if [ ! -f ${cfg.runsDir}/arbiter/config.json ]; then
        cat > ${cfg.runsDir}/arbiter/config.json << 'EOF'
{
  "max_lines_changed_without_human": ${toString cfg.arbiter.maxLinesChanged},
  "max_files_changed_without_human": ${toString cfg.arbiter.maxFilesChanged},
  "token_checkpoint_interval": ${toString cfg.arbiter.tokenCheckpointInterval},
  "task_checkpoint_interval": ${toString cfg.arbiter.taskCheckpointInterval},
  "high_risk_bash_prefixes": ["rm -rf /", "sudo rm", "dd if=", "mkfs", "> /dev/"]
}
EOF
      fi
    '';

    # Configure Claude Code agents
    claude.code.agents = lib.mkMerge [
      # Core LCA agents
      (lib.mkIf cfg.agents.planner {
        lca-planner = {
          description = "Generates and maintains runs/plan.md and writes tasks under runs/tasks/";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
          model = "opus";
          prompt = readAgent "lca-planner";
        };
      })

      (lib.mkIf cfg.arbiter.enable {
        lca-arbiter = {
          description = "Periodic blackhat checkpoint auditor. Decides if human review is needed.";
          tools = [ "Read" "Grep" "Glob" "LS" "Bash" "Edit" ];
          model = "opus";
          prompt = readAgent "lca-arbiter";
        };
      })

      (lib.mkIf cfg.agents.backend {
        lca-backend = {
          description = "Implements backend tasks. Use for API, DB, workers, server-side logic.";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
          model = "sonnet";
          prompt = readAgent "lca-backend";
        };
      })

      (lib.mkIf cfg.agents.frontend {
        lca-frontend = {
          description = "Implements frontend tasks. Use for UI, components, client state.";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
          model = "sonnet";
          prompt = readAgent "lca-frontend";
        };
      })

      (lib.mkIf cfg.agents.qa {
        lca-qa = {
          description = "Runs checks/tests, diagnoses failures, fixes with minimal diffs.";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" "Bash" ];
          model = "sonnet";
          prompt = readAgent "lca-qa";
        };
      })

      (lib.mkIf cfg.agents.docs {
        lca-docs = {
          description = "Writes implementation documentation for readers.";
          tools = [ "Read" "Grep" "Glob" "LS" "Edit" ];
          model = "haiku";
          prompt = readAgent "lca-docs";
        };
      })

      (lib.mkIf cfg.agents.gitops {
        lca-gitops = {
          description = "Handles branch/commit/push hygiene after tasks pass checks.";
          tools = [ "Read" "Edit" "Bash" ];
          model = "haiku";
          prompt = readAgent "lca-gitops";
        };
      })

      (lib.mkIf cfg.agents.recorder {
        lca-recorder = {
          description = "Records task changes in handoffs for task-to-task context.";
          tools = [ "Read" "Edit" ];
          model = "haiku";
          prompt = readAgent "lca-recorder";
        };
      })

      (lib.mkIf cfg.agents.reviewer {
        lca-reviewer = {
          description = "Reviews code quality after role agent completes.";
          tools = [ "Read" "Bash" ];
          model = "sonnet";
          prompt = readAgent "lca-reviewer";
        };
      })

      (lib.mkIf cfg.agents.enforcer {
        lca-enforcer = {
          description = "Enforces LCA protocol compliance.";
          tools = [ "Read" ];
          model = "sonnet";
          prompt = readAgent "lca-enforcer";
        };
      })

      # Extra project-specific agents
      cfg.extraAgents
    ];

    # Configure Claude Code hooks
    claude.code.hooks = lib.mkMerge [
      (lib.mkIf cfg.hooks.sessionStart {
        lca-session-start = {
          enable = true;
          name = "LCA Session Start";
          hookType = "PostToolUse";
          matcher = ".*";
          command = readHook "session-start.py";
        };
      })

      (lib.mkIf cfg.hooks.toolRecord {
        lca-tool-record = {
          enable = true;
          name = "LCA Tool Record";
          hookType = "PostToolUse";
          matcher = ".*";
          command = readHook "tool-record.py";
        };
      })
    ];

    # Add LCA protocol skill
    claude.code.skills.lca-protocol = {
      description = "LCA task/state/handoff protocol for Claude Code subagents";
      content = builtins.readFile (lcaRoot + "/skills/lca-protocol/SKILL.md");
    };
  };
}

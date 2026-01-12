# ALTO Session Context

> Temporary file for cross-session continuity

## What We Did This Session (2026-01-12)

### Background
- Started in `challenge-001-plantops` project which had an ALTO (Lifecycle Architecture) protocol for Claude Code autonomous agents
- User wanted to extract the coding architecture into a reusable module

### Analysis: ALTO vs Claude Code Native
We analyzed redundancy between ALTO protocol and Claude Code's built-in features:

**What's NOT redundant (unique value):**
- Session persistence (`runs/state.json`, handoffs) - Claude loses context between sessions
- Human review gates (arbiter with BLOCK severity)
- Git-based audit trail (run branches, checkpoints)
- Structured handoffs for cross-session context

**What IS redundant:**
- `alto-planner` duplicates `EnterPlanMode`
- Role agents duplicate `Task` tool with subagent_type
- Task tracking duplicates `TodoWrite`

### Decision: Use devenv.sh approach
Inspired by https://devenv.sh/integrations/claude-code/ which uses declarative Nix config to generate `.claude/` structure.

### Naming Evolution
1. `alto-protocol` → too generic, conflicts with other ALTO meanings
2. `agents-state-machine` (ASM) → okay but bland
3. **ALTO** → Autonomous Lifecycle Task Orchestrator
   - Named after El Alto, Bolivia (Cholitas Valley theme)
   - "alto" = "high" in Spanish (high-level orchestrator)
   - "alto" = "stop" in Spanish (perfect for arbiter BLOCK!)

### What Was Created
```
alto/
├── flake.nix              # Nix flake entry
├── devenv-module.nix      # alto.enable, alto.arbiter, etc.
├── agents/alto-*.md       # 10 agents
├── hooks/                 # 7 tracking hooks
├── skills/alto-protocol/  # Protocol skill
├── runs/                  # Initial state templates
├── templates/             # CLAUDE.md, ARCHITECTURE.md templates
└── docs/                  # Redundancy analysis
```

### Session 2 (2026-01-12 continued)

**Identified missing items:**
1. ~~**ARCHITECTURE.md template is too generic**~~ - Fixed in session 1
2. **Missing `alto-feature-setup` skill** - Interactive skill for setting up new features (now added)
3. **Missing `alto-recorder` in SKILL.md role list** - Fixed

**Added:**
- `skills/alto-feature-setup/SKILL.md` - Copied from plantops and renamed lca → alto
- Fixed `skills/alto-protocol/SKILL.md` - Added missing `alto-recorder` to role list

### Pending Issues
1. **Cursor untitled file issue** - When opening folders, Cursor creates untitled file (Nix config issue, couldn't investigate due to permission blocks)

### Next Steps
- Review `devenv-module.nix` file by file (user requested)
- Push to GitHub: `gh repo create alto --public --source=. --push`
- Update plantops to use alto as a devenv module (dogfooding)

## Source Project Reference
The original architecture came from:
- `challenge-001-plantops/ARCHITECTURE.md`
- `challenge-001-plantops/CLAUDE.md`
- `challenge-001-plantops/.claude/`
- `challenge-001-plantops/runs/`

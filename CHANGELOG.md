# Changelog

All notable changes to ALTO.

## [Unreleased]

### Added
- **Debug mode with event logging** (Issue #30):
  - `alto.debug` option (default false) - enables verbose event logging
  - Events logged to `runs/logs/events.jsonl` when enabled
  - ALTO-specific events: `session_start`, `session_end`, `handoff`
  - `alto-logs` script to query event logs (`--metrics`, `--type`, `--raw`)
  - Generic tool usage NOT duplicated (Claude Code OTel handles this)
  - `hook_utils.py`: `log_event()`, `is_debug_mode()`, `get_events()`, `get_session_metrics()`
- **Test harness for meta-development** (Issue #30):
  - `alto-test-run` script - run isolated test scenarios
  - `tests/scenarios/` directory with YAML scenario definitions
  - Initial scenarios: `simple-hello-world`, `setup-feature-definition`
  - JSON output option (`--json`) for programmatic use
  - Warning: uses `--dangerously-skip-permissions`, for trusted scenarios only
- **Dev orchestrator meta-development workflow** (Issue #30):
  - `skills/alto-self-fix/SKILL.md` - Procedural workflow for ALTO self-improvement
  - `skills/prompt-writing/SKILL.md` - Discipline for writing explicit prompts/protocols
  - Lighter `templates/CLAUDE.md.dev` - Uses AskUserQuestion for approach choice
  - Safeguard: `alto-restart` blocked in dev mode (prevents self-restart)
  - Branch naming convention: `issue-<number>-<description>`
- **Three-orchestrator model** (Issue #29):
  - `alto.orchestrator` option: `"setup"` (human-interactive), `"build"` (autonomous), or `"dev"` (ALTO development)
  - **Setup mode**: Feature definition, configuration, cleanup, onboarding
  - **Build mode**: Architecture, planning, execution, replan, arbiter checkpoints
  - **Dev mode**: Single `alto-dev` agent with dev-specific skills and minimal hooks
  - Conditional agent deployment per mode
  - Conditional hook deployment per mode (dev has only changelog-check)
  - Conditional skill deployment per mode (dev has alto-dev-guide, writing-alto-skills)
- `templates/CLAUDE.md.setup` - Setup orchestrator protocol
- `templates/CLAUDE.md.build` - Build orchestrator protocol
- `templates/CLAUDE.md.dev` - Dev orchestrator protocol (ALTO development)
- `skills/alto-configure/SKILL.md` - Shared configuration procedures (setup/build)
- `skills/alto-dev-guide/SKILL.md` - Documentation URLs and patterns (dev mode)
- `skills/writing-alto-skills/SKILL.md` - Skill authoring methodology (dev mode)
- `agents/alto-dev.md` - ALTO development agent with full access
- **`alto-switch` script enhanced** (Issue #31):
  - Now modifies `devenv.nix` directly and runs `alto-restart`
  - Usage: `alto-switch build` or `alto-switch setup` or `alto-switch dev`
  - Detects ALTO source repo and blocks (mode switching is for consumer projects)
  - CLAUDE.md templates updated to use `alto-switch` instead of manual instructions
- `alto-status` now shows current orchestrator mode
- Reconfiguration option at arbiter checkpoints (build mode)
- Reconfiguration option at feature completion (build mode)
- `alto-qa` agent now updates `runs/verification-config.json` when new tooling is set up
- ARCHITECTURE.md index with anchor links
- Skills section in ARCHITECTURE.md covering all skill types (discipline, technique, reference)
- `changelog-check.py` hook - PreToolUse hook that blocks `git commit` if key files staged without CHANGELOG.md

### Changed
- ARCHITECTURE.md refactored: 819→730 lines, 25→18 sections, consolidated redundant content
- Removed unified `templates/CLAUDE.md.template` (replaced by setup/build/dev templates)
- Unified ALTO development approach via orchestrator switch (tracked `.claude/` removed)
- `.gitignore` now ignores entire `.claude/` directory (deployed by devenv)
- To switch modes: run `alto-switch <mode>` (modifies devenv.nix and restarts automatically)
- Removed `alto.enable` option - ALTO activates on import (no explicit enable needed)
- Deploy task now removes CLAUDE.md before copying to handle read-only files
- ARCHITECTURE.md reorganized with Orchestrator Modes section
- README.md updated with orchestrator mode documentation
- All AskUserQuestion options now use explicit Label/Description format

- Three-tier permission system via devenv's Claude Code integration:
  - `permissions.profile` option: autonomous, supervised, or locked
  - `permissions.allowBash` - commands auto-approved (ls, cat, grep, etc.)
  - `permissions.askBash` - commands that prompt user (git, npm, docker)
  - `permissions.denyBash` - commands always blocked (rm -rf, sudo, git push -f)
  - `permissions.denyRead` - sensitive file patterns (.env, secrets/**, *.pem)
- Global permission settings from profile:
  - `defaultMode` - autonomous=acceptEdits, supervised=default, locked=plan
  - `disableBypassPermissionsMode` - enabled for supervised/locked profiles
- Per-agent permission configuration via `agentPermissions` options:
  - `permissionMode` per agent (plan, acceptEdits, default, dontAsk, bypassPermissions)
  - Per-agent tool restrictions from config
- `hook_utils.py` module with shared utilities for all hooks (Issue #5):
  - `@safe_hook` decorator for graceful error handling
  - Errors logged to `runs/errors.jsonl` instead of crashing
  - `health_check()` function for ALTO setup validation
  - Common JSON/state utilities
- Health check warnings on session start (detects setup issues)
- `current_handoff` field in state.json - explicit path for role agents
- Pre-created handoff templates - orchestrator creates file, agents just Edit
- Branch lifecycle documentation (Issue #9):
  - Debug mode (`phase = "DEBUG"`) for testing before merge
  - Next Feature mode with `alto-clean` + `alto-new-run` scripts
  - Handoffs preserved across runs for context continuity
- `alto-status` now shows remaining tasks and `>>> FEATURE COMPLETE <<<` indicator
- `alto-feature-finder` reads `runs/notes.md` for follow-ups from previous runs
- `session-summary` hook now reminds about CHANGELOG when key files modified without it
- `handoff-validate.py` hook for deterministic handoff validation
- `alto.verification` options for automated quality hooks:
  - `typecheck` - Run type checker after editing TS/TSX files
  - `lint` - Run linter after editing source files
  - `test` - Run tests after editing test files
  - `custom` - Define custom verification hooks
- `alto-dev` agent for ALTO development with Write, Edit, Bash, WebFetch
- `alto-dev-guide` skill with comprehensive documentation references
- `alto-feature-finder` agent for codebase analysis when starting features
- `alto-feature` script to start new feature setup
- SessionStart hook auto-creates `objective.md` template if missing
- SessionStart hook detects NEW_PROJECT vs real content, injects status signal
- Interactive startup flow with AskUserQuestion in CLAUDE.md
- Devenv MCP server configured for package search and config generation
- Discipline skills pattern for shared agent practices (Issue #15):
  - `scope-discipline` skill with warning signs and recovery steps
  - Agent prompts reference discipline skills via `## Disciplines` section
  - Reference-based activation (not discovery-based like superpowers)

### Changed
- CLAUDE.md.template trimmed from 302 to 186 lines (38% reduction):
  - Converted prose to bullet points
  - Tables instead of verbose explanations
  - Keeps critical sections explicit (AskUserQuestion, debug summary, state updates)
  - Follows AGENTS.md best practice: scannable, actionable, concise
  - Protocol Files table restored with all 9 referenced files
  - Skill reference made explicit with file path for fast lookup
- Added `docs/dev/template-comparison.md` documenting behavior analysis
- Agent permission modes updated for principle of least privilege:
  - `alto-arbiter`, `alto-feature-finder`, `alto-reviewer` now use `plan` mode (read-only)
  - `alto-gitops` uses `default` mode (prompts for each git operation)
  - Implementation agents (`backend`, `frontend`, `qa`, `docs`) use `acceptEdits`
- `alto-arbiter` tools reduced to `Read`, `Grep`, `Glob` (no Bash/Edit for auditor)
- `alto-reviewer` tools reduced to `Read`, `Grep`, `Glob`, `LS` (no Bash for reviewer)
- `alto-gitops` tools expanded to include `Grep`, `Glob`, `LS` for better context
- `alto-reviewer` now uses Sonnet instead of Opus (~60% cost reduction) (Issue #4)
- Remove `check_command` from task format - replaced with "How to Verify" section
  - More flexible: supports tests, manual checks, project-specific validation
  - Role agents decide how to verify based on task context
- `objective.md` template now has "Testing & Verification" section
  - Guides users to define project-specific test commands
  - Includes acceptance criteria patterns
  - Examples for different project types (npm, terraform, manual)
- `alto-qa` redesigned as **test writer** (not just fixer)
  - Runs after role agents via `post:` array
  - Writes tests following objective.md patterns
  - Fixes failures as secondary responsibility
  - Pipeline: role → alto-qa → code-simplifier → gitops
- `alto-recorder` no longer runs per-task; handoffs aggregated at session end (Issue #3)
  - Removed from `post:` arrays in task definitions
  - `session-summary.py` now extracts handoff summaries for cross-session context
  - Within-session context preserved by Claude's conversation memory
- Redesigned README for clarity: centered header, highlights section, collapsible config, horizontal dividers
- Renamed `devenv-module.nix` to `devenv.nix` for native devenv pattern
- Converted `enterShell` to `tasks."alto:deploy"` for cleaner deployment
- Simplified `alto-setup` script (hook handles objective.md creation)
- CLAUDE.md startup now reads hook's `[ALTO: NEW_PROJECT]` signal
- Split architect and planner responsibilities (Issue #1)
- Refactored alto-feature-setup to use scripts + feature-finder (Issue #10)
- CLAUDE.md template audit (10 issues fixed):
  - Boot now uses `alto-new-run` script instead of manual git
  - Resume table includes COMPLETED and DEBUG phases
  - Removed "phase is null" condition (state.json always exists)
  - Feature completion uses `alto-status` for exit condition
  - Simplified Feature Completion (follow-up analysis moved to feature-finder)
  - Removed "New feature" from startup options
  - Feature Completion is now separate section, not part of execution loop

### Fixed
- `.gitignore` now tracks `.claude/` source files (agents, skills) but ignores `settings.json`
- jq escaping in `alto-status` script (use separate echo+jq calls)
- Removed `disableBypassPermissionsMode` setting (devenv bug: expects boolean, Claude Code expects string "disable")

### Removed
- `permissions.defaultMode` option - replaced by three-tier system (allow/ask/deny)
- Flake-parts templates (native devenv only now)
- Redundant flake.nix template options
- `alto-enforcer` agent - replaced by `handoff-validate.py` hook (Issue #2)
  - ~5-10s → ~50ms per task (no LLM call)
  - Zero token cost for validation
  - Deterministic checks (no hallucination risk)
- `alto-recorder` agent - handoffs now aggregated by `session-summary.py` (Issue #3)
  - ~2-3s saved per task (no haiku call)
  - 10 tasks = ~20-30s total savings
  - Zero token cost for recording

## [0.1.0] - 2026-01-12

### Added
- Initial ALTO protocol implementation
- 12 core agents (planner, backend, frontend, qa, docs, gitops, recorder, reviewer, enforcer, arbiter)
- Arbiter human review gates with configurable thresholds
- Hooks for session tracking, tool recording, usage monitoring
- Skills: alto-protocol, alto-feature-setup
- State machine: ARCHITECTURE → PLANNING → IN_TASK → BETWEEN_TASKS → BLOCKED
- Handoff system for cross-session context
- Git-based audit trail with run branches

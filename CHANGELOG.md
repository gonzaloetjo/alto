# Changelog

All notable changes to ALTO.

## [Unreleased]

### Added
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

### Changed
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

### Removed
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

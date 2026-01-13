# Changelog

All notable changes to ALTO.

## [Unreleased]

### Added
- `alto-dev` agent for ALTO development with Write, Edit, Bash, WebFetch
- `alto-dev-guide` skill with comprehensive documentation references
- `alto-feature-finder` agent for codebase analysis when starting features
- `alto-feature` script to start new feature setup
- SessionStart hook auto-creates `objective.md` template if missing
- SessionStart hook detects NEW_PROJECT vs real content, injects status signal
- Interactive startup flow with AskUserQuestion in CLAUDE.md
- Devenv MCP server configured for package search and config generation

### Changed
- Redesigned README for clarity: centered header, highlights section, collapsible config, horizontal dividers
- Renamed `devenv-module.nix` to `devenv.nix` for native devenv pattern
- Converted `enterShell` to `tasks."alto:deploy"` for cleaner deployment
- Simplified `alto-setup` script (hook handles objective.md creation)
- CLAUDE.md startup now reads hook's `[ALTO: NEW_PROJECT]` signal
- Split architect and planner responsibilities (Issue #1)
- Refactored alto-feature-setup to use scripts + feature-finder (Issue #10)

### Fixed
- jq escaping in `alto-status` script (use separate echo+jq calls)

### Removed
- Flake-parts templates (native devenv only now)
- Redundant flake.nix template options

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

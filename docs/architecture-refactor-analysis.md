# ARCHITECTURE.md Refactor Analysis

Analysis of current structure with proposed improvements.

## Current Stats

- **Lines:** 819
- **Sections:** 25 (per index)
- **Diagrams:** 4 ASCII diagrams (keep all)
- **Tables:** 15

---

## What's Working Well

### Keep As-Is

1. **All diagrams** - The 4 ASCII diagrams are excellent:
   - Orchestrator Modes box diagram
   - Agent & Flow diagram (Build Mode)
   - Hooks diagram
   - Execution Loop / Task Lifecycle diagrams

2. **Index** - Useful for navigation, keep at top

3. **Overview** - Concise 4-bullet summary

4. **Orchestrator Modes** - Clear separation, good diagram

5. **Directory Structure** - Comprehensive, well-annotated

---

## Issues Identified

### 1. Redundant Content

| Location A | Location B | Overlap |
|------------|------------|---------|
| Orchestrator Modes (L74-85) | Interactive Startup (L211-238) | Both explain what each mode does |
| Orchestration Flow Boot (L335-356) | Agent Flow Diagram box (L111-118) | Both describe architecture phase outputs |
| State Phases table (L400-408) | Orchestration Flow sections | Phases described twice |
| Role Agents table (L414-426) | Directory Structure agents list (L270-281) | Agent list duplicated with slight variations |
| Branch Lifecycle (L770-818) | Interactive Startup "Completed" (L238) | Feature completion covered twice |

**Estimated redundancy:** ~80-100 lines

### 2. Scattered Related Content

These topics are split across non-adjacent sections:

| Topic | Locations | Better Grouping |
|-------|-----------|-----------------|
| **Agents** | Role Agents (L412), Model Assignment (L495), Directory Structure (L270) | Single "Agents" section |
| **Configuration** | Configuration Timing (L580), Verification Hooks (L609), Dynamic Verification (L659) | Single "Configuration" section |
| **Task execution** | Task Format (L512), Handoff Contract (L536), Orchestration Flow (L331) | Single "Task System" section |
| **Human checkpoints** | Arbiter System (L550), Branch Lifecycle completion (L789), Interactive Startup blocked (L236) | Single "Human Intervention" section |

### 3. Section Ordering Issues

Current order feels arbitrary. Suggested logical flow:

```
OVERVIEW (what is ALTO)
  ↓
GETTING STARTED (modes, scripts, startup)
  ↓
CORE CONCEPTS (agents, tasks, handoffs, skills)
  ↓
BUILD FLOW (phases, execution loop, arbiter)
  ↓
CONFIGURATION (devenv, dynamic, verification)
  ↓
INTERNALS (hooks, tracking, permissions, files)
```

### 4. Inconsistent Depth

| Section | Lines | Issue |
|---------|-------|-------|
| Verification Hooks | 84 | Very detailed, could be separate doc |
| Permissions Model | 10 | Too brief for importance |
| Token Tracking | 7 | Minimal |
| Hook Error Handling | 29 | Good depth |

### 5. Missing Content

- No "Quick Reference" for common operations
- No troubleshooting section
- No "How to extend ALTO" section

---

## Proposed New Structure

```
# ALTO Architecture

## Index

## Overview (keep)

## Quick Start
  - Scripts table (from Devenv Scripts)
  - Mode switching (from Orchestrator Modes)

## Orchestrator Modes (keep diagram)
  - Setup Mode
  - Build Mode
  - Switching modes
  (absorb Interactive Startup content here)

## Agents
  - Role Agents table (merge Mode column, Model column, Constraints)
  - Post-agent flow
  - Agent communication model (from Communication Model)

## Skills
  - Current Skills table
  - Skill types
  - Adding skills

## Task System
  - Task format
  - Handoff contract
  - Task lifecycle diagram (keep)

## Build Flow (keep diagrams)
  - State phases table
  - Boot sequence
  - Execution loop
  - Replan logic

## Human Intervention
  - Arbiter system
  - Checkpoints
  - Feature completion (from Branch Lifecycle)
  - Debug mode

## Configuration
  - Configuration timing table
  - Static config (devenv.nix)
  - Dynamic config (JSON files)
  - Verification hooks

## Files & Directories
  - Directory structure (keep)
  - Protocol files table

## Internals
  - Claude Code integration
  - Hooks architecture
  - Hook error handling
  - Token tracking
  - Permissions model

## Branch Lifecycle
  - Branch strategy
  - Cleanup
  (remove Feature Completion - moved to Human Intervention)

## Extending ALTO (new)
  - Adding agents
  - Adding hooks
  - Adding skills
```

---

## Specific Changes

### Merge: Role Agents + Model Assignment + Directory agents

**Current (3 places):**
- L270-281: Directory listing with "(build only)" notes
- L414-426: Table with Mode, Primary responsibility, Constraints
- L495-508: Table with Model, Rationale

**Proposed (1 table):**

```markdown
| Agent | Mode | Model | Purpose | Constraints |
|-------|------|-------|---------|-------------|
| alto-planner | build | opus | Create tasks from milestones | runs/ only, no Bash |
| alto-feature-finder | both | opus | Analyze codebase | read-only |
| alto-backend | build | sonnet | API, DB, workers | allowed_paths |
| alto-frontend | build | opus | UI implementation | allowed_paths |
| alto-qa | build | sonnet | Tests, verification config | post-role |
| alto-docs | build | sonnet | Documentation | docs/ only |
| alto-gitops | build | haiku | Git operations | after checks |
| alto-reviewer | build | opus | Quality gate | read-only |
| alto-arbiter | build | opus | Checkpoint auditor | arbiter/ only |
| code-simplifier | build | opus | Code refinement | touched files |
```

**Savings:** ~30 lines

### Merge: Interactive Startup into Orchestrator Modes

Interactive Startup just restates mode behaviors. Absorb into mode descriptions:

**Current Orchestrator Modes:**
- Setup Mode handles: (4 bullets)
- Build Mode handles: (5 bullets)

**Current Interactive Startup:**
- Setup Mode (Human-Interactive): (7 bullets across 2 scenarios)
- Build Mode (Autonomous): (5 bullets across 4 scenarios)

**Proposed:** Add "Startup Behavior" subsection under each mode in Orchestrator Modes.

**Savings:** ~25 lines (eliminate separate section)

### Merge: Configuration sections

**Current (3 sections):**
- Configuration Timing (L580-606): 26 lines
- Verification Hooks (L609-690): 82 lines
- Dynamic Verification (part of above): embedded

**Proposed (1 section with subsections):**
```
## Configuration
### When Configs Apply (timing table)
### Static Configuration (devenv.nix)
### Dynamic Configuration (JSON files)
### Verification Hooks
```

Same content, better organized. No line savings but clearer navigation.

### Move: Feature Completion from Branch Lifecycle to Human Intervention

Branch Lifecycle should only cover git branches. Feature completion is about human decision points.

### Remove: Redundant phase descriptions

Orchestration Flow describes phases procedurally. State Phases table describes them definitionally. Keep only the table, let flow section reference it.

---

## Diagrams Assessment

| Diagram | Lines | Verdict |
|---------|-------|---------|
| Orchestrator Modes | 22 | **KEEP** - Clear mode visualization |
| Agent & Flow | 66 | **KEEP** - Essential architecture view |
| Hooks | 12 | **KEEP** - Shows hook flow |
| Execution Loop | 18 | **KEEP** - Critical for understanding |
| Task Lifecycle | 23 | **KEEP** - Shows post-agent flow |

All diagrams provide value. No changes recommended.

---

## Estimated Impact

| Metric | Current | Proposed |
|--------|---------|----------|
| Lines | 819 | ~700-720 |
| Sections | 25 | 13-15 |
| Tables | 15 | ~12 |
| Diagrams | 4 | 4 |
| Redundancy | ~80-100 lines | ~0 |

**Benefits:**
- Single source of truth for each concept
- Logical reading flow
- Easier to maintain
- Still comprehensive

---

## Implementation Plan

### Phase 1: Consolidate (no content loss)
1. Merge agent tables into single comprehensive table
2. Merge Interactive Startup into Orchestrator Modes
3. Create unified Configuration section
4. Move Feature Completion to Human Intervention section

### Phase 2: Reorganize
1. Reorder sections per proposed structure
2. Update index
3. Add section cross-references where needed

### Phase 3: Polish
1. Remove remaining redundancy
2. Add Quick Reference section
3. Add Extending ALTO section
4. Verify all links work

---

## Questions Before Proceeding

1. **Quick Reference section:** Should it include command cheatsheet?
2. **Extending ALTO section:** How detailed? Just pointers or full guide?
3. **Troubleshooting:** Worth adding? Common issues list?
4. **Separate docs:** Should Verification Hooks be its own doc given depth?

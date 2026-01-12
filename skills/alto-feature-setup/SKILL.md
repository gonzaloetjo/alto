# ALTO Feature Setup

Interactive skill for setting up a new feature. Follow this checklist when user says "start feature X".

## Checklist

### 0. Mark Previous Feature Complete (if applicable)

Before setting up a new feature, close out the previous completed feature:

- [ ] Read the previous run's final QA handoff: `runs/handoffs/task-XXX-recorder.md` (the last recorder handoff)
- [ ] Read `runs/state.json` to confirm:
  - `phase` is `BETWEEN_TASKS` (run complete)
  - All expected tasks in `completed_task_ids`
- [ ] Update `objective.md`:
  - Mark all Definition of Done items as `[x]` (checked)
  - Add completion metadata after DoD section:
    ```markdown
    **Completed:** run/NNN (YYYY-MM-DD) — N tests passing
    ```
- [ ] Update Implementation Order section if it has status markers
- [ ] Verify: grep the feature section for any remaining `[ ]` (unchecked items)

**Example transformation:**
```markdown
# Before
### Definition of Done
- [ ] Button component with 4 variants
- [ ] StatusBadge component for status indicators
- [ ] `make check` passes

# After
### Definition of Done
- [x] Button component with 4 variants
- [x] StatusBadge component for status indicators
- [x] `make check` passes

**Completed:** run/005 (2026-01-10) — 139 tests passing
```

### 1. Define Feature in objective.md
- [ ] Read current objective.md
- [ ] Discuss feature scope with user
- [ ] Add Feature N section:
  - Goal statement
  - Current problems (if refactor)
  - Numbered requirements (N.1, N.2, etc.)
  - Definition of Done (checkboxes)
  - Skills available (if relevant)

### 2. Prepare Skills
- [ ] Check `.spawner/skills/` for relevant skills
- [ ] Copy to `.claude/skills/`:
  ```bash
  cp -r .spawner/skills/<category>/<skill> .claude/skills/
  ```
- [ ] Verify: `ls .claude/skills/`

### 3. Create Run Branch
- [ ] Get next run number (check existing branches)
- [ ] Create branch:
  ```bash
  git checkout -b run/<NNN>
  ```

### 4. Clean Previous Run Artifacts
- [ ] Check `runs/arbiter/pending.json` - delete if exists (stale trigger)
- [ ] Check `runs/notes.md` - note any unresolved blockers from previous run
- [ ] Find last handoff from previous run: `ls -t runs/handoffs/ | head -1`

### 5. Update State
- [ ] Write `runs/state.json`:
  ```json
  {
    "protocol": "alto-v1",
    "run_branch": "run/<NNN>",
    "phase": "PLANNING",
    "current_task_id": null,
    "current_role": null,
    "completed_task_ids": [],
    "last_handoff": "runs/handoffs/<previous-run-final-handoff>",
    "updated_at": "<ISO-8601>"
  }
  ```
  Note: `last_handoff` provides context continuity from the previous run.

### 6. Verify Setup
- [ ] objective.md has Feature N
- [ ] Skills in .claude/skills/
- [ ] On branch run/<NNN>
- [ ] state.json phase=PLANNING
- [ ] No stale arbiter pending.json

### 7. Handoff to User

Tell user:
> Feature N setup complete. Start a new Claude Code session.
> Say "continue" or "start" to begin autonomous execution.
>
> The orchestrator will:
> 1. See phase=PLANNING → invoke alto-planner
> 2. Planner creates tasks from objective.md
> 3. Execution loop runs role agents

---

## Notes
- This is INTERACTIVE - Claude follows it WITH the user
- Autonomous orchestrator starts in a NEW session
- User defines features conversationally here
- After setup, user starts fresh session for autonomous work

## Pre-configured (no setup needed per feature)
These are already installed and work automatically:
- **Hooks**: session-start, session-summary, tool-record, usage-record, arbiter-scheduler
- **Plugins**: security-guidance (warns on security patterns), code-simplifier (post agent)
- **Directories**: runs/, .claude/agents/, .claude/hooks/

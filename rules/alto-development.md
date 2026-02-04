# ALTO Development Rules

> Rules for developing ALTO itself - combining Claude Code best practices with ALTO protocol awareness.

---

## Part 1: Claude Code Best Practices

### Rule 1: Feature Selection Matrix

**Trigger**: Deciding between rule, skill, hook, or command

| Need | Use | Why |
|------|-----|-----|
| Always-active constraint | Rule | Deterministic, always in context |
| On-demand procedure | Skill | Lazy loading, saves baseline context |
| Must enforce (block/log) | Hook | Always executes, can't be ignored |
| User-triggered shortcut | Command | Explicit invocation |

> **Key insight**: Rules suggest. Hooks enforce.

---

### Rule 2: Size Limits

**Trigger**: Writing orchestrator templates or agent prompts

- Keep under 300 lines (60 lines ideal)
- Use `file:line` references, not code snippets
- Progressive disclosure: reference docs, don't embed

---

### Rule 3: Provide Alternatives

**Trigger**: Writing any constraint

- BAD: "Never use --foo-bar flag"
- GOOD: "Use --baz instead of --foo-bar because X"

---

### Rule 4: Skill Activation Safety

**Trigger**: Creating skill for dangerous operations (deploy, delete, reset)

```yaml
disable-model-invocation: true
user-invocable: true
```

---

### Rule 5: Hook Limitations

| Limitation | Detail |
|------------|--------|
| PreToolUse cannot see result | Runs before tool executes |
| PostToolUse cannot modify | Result already in context |
| Warn only reaches user | Claude doesn't see warn output |

---

## Part 2: ALTO Protocol Awareness

### Rule 6: Valid Phase Transitions

**Trigger**: Editing `phase-validate.py` or state management

```
None → ARCHITECTURE
ARCHITECTURE → PLANNING, BLOCKED
PLANNING → IN_TASK, BETWEEN_TASKS, BLOCKED
IN_TASK → BETWEEN_TASKS, BLOCKED
BETWEEN_TASKS → IN_TASK, PLANNING, COMPLETED, BLOCKED
BLOCKED → ARCHITECTURE, PLANNING, IN_TASK, BETWEEN_TASKS
COMPLETED → DEBUG, ARCHITECTURE
DEBUG → COMPLETED
```

Keep `VALID_TRANSITIONS` dict in `phase-validate.py` in sync.

---

### Rule 7: File Structure

**Trigger**: Creating or moving files

| Directory | Contents |
|-----------|----------|
| `agents/*.md` | Agent prompts |
| `hooks/*.py` | Hook implementations |
| `skills/*/SKILL.md` | Skills |
| `rules/*.md` | Always-loaded rules |
| `rules/formats/*.md` | Path-targeted format rules |
| `templates/CLAUDE.md.*` | Orchestrator templates |
| `runs/tasks/*.md` | Task files (planner output) |
| `runs/handoffs/*.md` | Handoffs (agent output) |
| `runs/review/*.md` | Reviews (reviewer output) |

---

### Rule 8: Validation Hook Sync

**Trigger**: Changing format rules or validation hooks

| Format Rule | Validation Hook | Keep In Sync |
|-------------|-----------------|--------------|
| `formats/task.md` | `task-validate.py` | Required fields |
| `formats/handoff.md` | `handoff-validate.py` | Required sections |
| `formats/review.md` | `review-validate.py` | Status format |

---

### Rule 9: Change Impact Matrix

**Trigger**: Making changes to ALTO source

| When You Change | Also Update |
|-----------------|-------------|
| Agent prompt | Check format rule reference |
| Hook logic | Check `devenv.nix` wiring |
| Phase transitions | `phase-validate.py` VALID_TRANSITIONS |
| Task format | `task-validate.py` field checks |
| State.json fields | Hooks that read/write state |
| New agent | `devenv.nix` + PROTOCOL.md |
| New hook | `devenv.nix` + PROTOCOL.md |
| New skill | `skills/<name>/SKILL.md` + deploy script |
| New rule | `rules/<name>.md` + deploy script (if conditional) |

---

### Rule 10: Agent Output Formats

**Trigger**: Creating or modifying agents

| Agent Category | Output Location | Format Rule |
|----------------|-----------------|-------------|
| planner | `runs/tasks/*.md` | `formats/task.md` |
| impl (backend, frontend) | `runs/handoffs/*.md` | `formats/handoff.md` |
| tester | `runs/handoffs/*.md` | `formats/handoff.md` |
| reviewer | `runs/review/*.md` | `formats/review.md` |
| controller | decision only | — |
| support | varies | — |

---

## Part 3: Quick Lookups

### Key Files

| Need | Read |
|------|------|
| Protocol actions | `PROTOCOL.md` |
| Architecture overview | `ARCHITECTURE.md` |
| Hook/agent syntax | `skills/alto-dev-guide/SKILL.md` |
| Orchestrator behavior | `templates/CLAUDE.md.{mode}` |
| Deploy logic | `scripts/alto-deploy.sh` |

### Validation Before Commit

```bash
nix-instantiate --parse devenv.nix > /dev/null && echo "Nix OK"
python3 -m py_compile hooks/*.py && echo "Python OK"
```

### Testing

```bash
alto-test-run --scenario <name> --keep
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Embed code in prompts | Use `file:line` references |
| Add style rules | Use linters |
| Say "don't do X" | Say "do Y instead" |
| Auto-invoke dangerous skills | Set `disable-model-invocation: true` |
| Change format without hook | Update validation hook too |
| Add phase without transition | Update `VALID_TRANSITIONS` |
| Write 500-line CLAUDE.md | Keep under 300, reference docs |

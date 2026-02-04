# ALTO Development Rules

> Distilled rules for ALTO dev mode based on Claude Code best practices research.

---

## Rule 1: Rule Placement

**Trigger**: Writing a new rule for agent behavior

**Action**:
- Single agent only → embed in that agent's `.md` file
- Multiple agents → create `rules/*.md` file

**Rationale**: Reduces context bloat; rules always load for their scope.

---

## Rule 2: Feature Selection Matrix

**Trigger**: Deciding between rule, skill, hook, or command

**Action**: Use this matrix:

| Need | Use | Why |
|------|-----|-----|
| Always-active constraint | Rule | Deterministic, always in context |
| On-demand procedure | Skill | Lazy loading, saves baseline context |
| Must enforce (block/log) | Hook | Always executes, can't be ignored |
| User-triggered shortcut | Command | Explicit invocation, simple template |
| Warn user (not Claude) | Hook warn | Warn only reaches user, not Claude |

**Rationale**: Context budget is finite (~180k usable); wrong choice wastes tokens.

---

## Rule 3: CLAUDE.md/Agent.md Size Limits

**Trigger**: Writing orchestrator templates or agent prompts

**Action**:
- Keep under 300 lines (60 lines ideal)
- Use `file:line` references, not code snippets
- Progressive disclosure: reference docs, don't embed

**Rationale**: "May or may not be relevant" system message = non-universal rules get ignored.

---

## Rule 4: Provide Alternatives, Not Just Negatives

**Trigger**: Writing any constraint or rule

**Action**:
- BAD: "Never use --foo-bar flag"
- GOOD: "Use --baz instead of --foo-bar because X"

**Rationale**: Agent gets stuck when it thinks it must use a forbidden thing but has no alternative.

---

## Rule 5: Don't Use LLM for Linter Work

**Trigger**: Tempted to add style rules (formatting, naming)

**Action**: Use deterministic tools (eslint, prettier, ruff, black) instead

**Rationale**: LLMs are expensive/slow; linters are fast/reliable.

---

## Rule 6: Skill Activation Safety

**Trigger**: Creating skill for dangerous operations (deploy, delete, reset)

**Action**:
```yaml
---
disable-model-invocation: true
user-invocable: true
---
```

**Rationale**: Prevents accidental triggering via description matching.

---

## Rule 7: Agent Path Restrictions

**Trigger**: Creating task for implementation agent

**Action**: Always include explicit `allowed_paths` in task frontmatter

```yaml
---
allowed_paths:
  - backend/**
  - src/api/**
---
```

**Rationale**: Prevents scope creep; agent can only touch relevant files.

---

## Rule 8: Hook Limitations Awareness

**Trigger**: Designing hook-based validation

**Action**: Know these limitations:

| Limitation | Detail |
|------------|--------|
| PreToolUse cannot see result | Runs before tool executes |
| PostToolUse cannot modify result | Already in context |
| Warn messages only reach user | Claude doesn't see warn output |
| Skill-scoped hooks may not trigger | Known issue in plugins |

**Rationale**: Design around actual capabilities, not assumed ones.

---

## Rule 9: Context Management in Multi-Agent Systems

**Trigger**: Designing orchestrator with multiple agents

**Action**:
- Use subagents for investigation (separate context window)
- Keep handoffs concise (they enter next agent's context)
- Clear context between unrelated tasks

**Rationale**: 200k window, ~20k baseline; subagents prevent context pollution.

---

## Rule 10: Prompt Writing Discipline

**Trigger**: Writing any ALTO prompt (templates, agents, skills)

**Action**: Follow `rules/prompt-writing.md`:
- Explicit tool names: `AskUserQuestion` not "ask user"
- Explicit paths: `runs/state.json` not "state file"
- Always specify `AskUserQuestion` with Header, Question, Options

**Rationale**: Ambiguous prompts cause tool selection errors.

---

## Quick Reference

| Don't | Do Instead |
|-------|------------|
| Embed code snippets | Use `file:line` references |
| Add style rules | Use linters (prettier, ruff) |
| Say "don't do X" | Say "do Y instead of X because Z" |
| Auto-invoke dangerous skills | Set `disable-model-invocation: true` |
| Let agents touch any file | Specify `allowed_paths` |
| Assume hooks can modify results | Design for actual capabilities |
| Write 500-line CLAUDE.md | Keep under 300 lines, reference docs |
| Put universal rules in skills | Put in `rules/*.md` |

---
name: review-writing
description: Use when writing code review results. Provides exact format required for runs/review/*.md files with APPROVED/REJECTED status.
---

# Review Writing

## Template

Review files go in `runs/review/task-{ID}-review.md`. Use **exactly** this format:

### For APPROVED:

```markdown
## Review: task-{ID}

**Status:** APPROVED

## Checks Passed
- Tests: X passing, properly validate behavior
- DoD: All items met
- Quality: No obvious issues

## Verification
- `npm test` - PASS
- `npm run lint` - PASS
```

### For REJECTED:

```markdown
## Review: task-{ID}

**Status:** REJECTED

## Reason
[Specific issue that caused rejection]

## Action Required
[What the role agent must fix - be specific]

## Checks
- Tests: [status]
- DoD: [which items not met]
- Quality: [issues found]
```

## Required Elements

| Element | Description |
|---------|-------------|
| `## Review: task-{ID}` | Header with task ID |
| `**Status:** APPROVED` or `**Status:** REJECTED` | Decision on exact line |
| `## Checks` or `## Checks Passed` | What was verified |

## For REJECTED - Additional Required

| Element | Description |
|---------|-------------|
| `## Reason` | Why rejected |
| `## Action Required` | What to fix |

## Rules

1. **Status must be exact** - `APPROVED` or `REJECTED` (all caps)
2. **Be specific in rejections** - Vague feedback wastes time
3. **File path derives from task** - `task-001` → `task-001-review.md`
4. **Don't approve weak tests** - Tests must validate real behavior

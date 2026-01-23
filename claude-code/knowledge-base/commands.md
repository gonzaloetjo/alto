# Claude Code > Commands

> Custom slash commands in `.claude/commands/`.

## Directory Locations

| Location | Scope | Visibility in `/help` |
|----------|-------|----------------------|
| `.claude/commands/` | Project (team-shared) | `(project)` |
| `~/.claude/commands/` | User (personal) | `(user)` |

**Precedence**: Project commands override user commands with the same name.

---

## Creating a Command

### Basic Command

```bash
# Creates /optimize command
mkdir -p .claude/commands
echo "Analyze this code for performance issues:" > .claude/commands/optimize.md
```

### Command File Structure

```markdown
---
description: Brief description shown in /help
allowed-tools: Bash(git status:*), Bash(git diff:*)
argument-hint: [file-path] [options]
model: claude-3-5-haiku-20241022
---

Your prompt text goes here.
This is what Claude receives when you invoke the command.
```

---

## Frontmatter Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `description` | Shown in `/help` output | `"Fix GitHub issues"` |
| `argument-hint` | Hint for expected args | `[issue-number] [priority]` |
| `allowed-tools` | Tools the command can use | `Bash(git:*), Read` |
| `model` | Override model for this command | `claude-3-5-haiku-20241022` |
| `context: fork` | Run in isolated subagent context | `fork` |
| `agent` | Subagent type when `context: fork` | `code-simplifier` |
| `disable-model-invocation` | Prevent auto-invocation | `true` |
| `hooks` | Define PreToolUse/PostToolUse hooks | See hooks section |

---

## Arguments

### Capture All Arguments: `$ARGUMENTS`

```markdown
---
description: Fix a GitHub issue
---

Fix issue #$ARGUMENTS following our coding standards.
```

Usage:
```
> /fix-issue 123
# $ARGUMENTS = "123"

> /fix-issue 123 with high priority
# $ARGUMENTS = "123 with high priority"
```

### Positional Arguments: `$1`, `$2`, `$3`

```markdown
---
argument-hint: [issue-number] [priority] [assignee]
description: Assign and fix issue
---

Fix issue #$1 with $2 priority. Assign to $3.
```

---

## Dynamic Content

### Bash Execution: `!`backticks

Execute shell commands and include output:

```markdown
---
allowed-tools: Bash(git:*)
description: Create a commit from current changes
---

## Current State

Branch: !`git branch --show-current`
Status: !`git status --short`
Diff: !`git diff --stat`

## Task

Create a meaningful commit message based on the above changes.
```

### File References: `@`

Include file contents inline:

```markdown
Review the implementation in @src/utils/helpers.js

Compare these two files:
- Old: @src/v1/handler.js
- New: @src/v2/handler.js
```

---

## Tool Permissions

### Granting Bash Access

```markdown
---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(npm run build:*)
---
```

Pattern syntax:
- `Bash(git:*)` - any git command
- `Bash(git status:*)` - only git status
- `Bash(npm run:*)` - any npm run script

### Multiple Tools

```markdown
---
allowed-tools: Bash(git:*), Bash(npm:*), Read, Glob, Grep
---
```

---

## Examples

### Git Commit with Context

```markdown
# .claude/commands/commit.md

---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*)
description: Create a conventional commit
---

## Current Changes

Branch: !`git branch --show-current`
Status: !`git status`
Staged: !`git diff --cached`
Unstaged: !`git diff`

## Task

Create a commit following conventional commits format:
- feat: new feature
- fix: bug fix
- docs: documentation
- refactor: code refactoring
- test: adding tests
- chore: maintenance

Stage appropriate files and create the commit.
```

### Issue Fixer

```markdown
# .claude/commands/fix-issue.md

---
argument-hint: [issue-number]
allowed-tools: Bash(gh issue view:*), Bash(git:*), Bash(npm test:*)
description: Fix a GitHub issue end-to-end
---

## Issue Details

!`gh issue view $1 --json title,body,labels`

## Task

1. Analyze the issue
2. Find relevant code
3. Implement a fix
4. Write/update tests
5. Create a PR description

Follow our contributing guidelines in @CONTRIBUTING.md
```

### PR Review

```markdown
# .claude/commands/pr-review.md

---
argument-hint: [pr-number]
allowed-tools: Bash(gh pr:*), Bash(git:*)
description: Review a pull request
---

## PR Information

!`gh pr view $1 --json title,body,files,additions,deletions`

## Full Diff

!`gh pr diff $1`

## Task

Review this PR for:
1. Correctness and logic
2. Security concerns
3. Performance implications
4. Test coverage
5. Documentation needs
```

### Isolated Context Command

```markdown
# .claude/commands/isolated-task.md

---
description: Run task in isolated context
context: fork
agent: code-simplifier
---

Simplify and refactor the code in $ARGUMENTS.
Focus on readability and maintainability.
```

---

## Organizing Commands

### Subdirectories (Namespacing)

```
.claude/commands/
├── optimize.md              # /optimize
├── review.md                # /review
├── backend/
│   ├── deploy.md            # /deploy (project:backend)
│   └── migrate.md           # /migrate (project:backend)
└── frontend/
    └── build.md             # /build (project:frontend)
```

Commands in subdirectories show their folder as a label in `/help`.

---

## Commands vs Skills

| Aspect | Commands | Skills |
|--------|----------|--------|
| Complexity | Simple prompts | Complex multi-step workflows |
| Structure | Single `.md` file | Directory with `SKILL.md` + files |
| Discovery | Explicit (`/name`) | Can be automatic |
| Best for | Quick, reusable prompts | Complex automation |

---

## Related

- [skills.md](skills.md) - Complex capabilities
- [agents.md](agents.md) - Custom subagents

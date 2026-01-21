# Claude Code Custom Commands

Custom commands are reusable prompts stored as Markdown files that you can invoke with `/command-name` during Claude Code sessions.

## Directory Locations

| Location | Scope | Visibility in `/help` |
|----------|-------|----------------------|
| `.claude/commands/` | Project (team-shared, committed to repo) | `(project)` |
| `~/.claude/commands/` | User (personal, all projects) | `(user)` |

**Precedence**: Project commands override user commands with the same name.

## Creating a Command

### Basic Command

1. Create the directory:
   ```bash
   mkdir -p .claude/commands
   ```

2. Create a Markdown file (filename = command name):
   ```bash
   # Creates /optimize command
   echo "Analyze this code for performance issues:" > .claude/commands/optimize.md
   ```

3. Use it:
   ```
   > /optimize
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

The YAML frontmatter (between `---`) is optional but enables advanced features.

## Frontmatter Options

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

### Positional Arguments: `$1`, `$2`, `$3`, etc.

```markdown
---
argument-hint: [issue-number] [priority] [assignee]
description: Assign and fix issue
---

Fix issue #$1 with $2 priority. Assign to $3.
```

Usage:
```
> /assign-issue 123 high alice
# $1 = "123", $2 = "high", $3 = "alice"
```

### Default Values

Arguments without values are empty strings. Handle gracefully:

```markdown
Review $1 with focus on ${2:-general} concerns.
```

## Dynamic Content

### Bash Execution: `!`backticks

Execute shell commands and include their output:

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

The bash output is inserted into the prompt before Claude sees it.

### File References: `@`

Include file contents inline:

```markdown
Review the implementation in @src/utils/helpers.js

Compare these two files:
- Old: @src/v1/handler.js
- New: @src/v2/handler.js
```

### Combining Features

```markdown
---
allowed-tools: Bash(git:*), Bash(npm test:*)
argument-hint: [component-name]
description: Review and test a component
---

## Component: $1

Source: @src/components/$1.jsx
Tests: @src/components/$1.test.jsx

## Recent Changes

!`git diff HEAD~5 -- src/components/$1.jsx`

## Task

1. Review the component for issues
2. Run tests: `npm test -- $1`
3. Suggest improvements
```

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
- `Bash(docker compose up:*)` - specific docker command

### Multiple Tools

```markdown
---
allowed-tools: Bash(git:*), Bash(npm:*), Read, Glob, Grep
---
```

## Organizing Commands

### Subdirectories (Namespacing)

```
.claude/commands/
├── optimize.md              # /optimize
├── review.md                # /review
├── backend/
│   ├── deploy.md            # /deploy (project:backend)
│   ├── migrate.md           # /migrate (project:backend)
│   └── seed.md              # /seed (project:backend)
├── frontend/
│   ├── deploy.md            # /deploy (project:frontend)
│   └── build.md             # /build (project:frontend)
└── devops/
    └── deploy.md            # /deploy (project:devops)
```

Commands in subdirectories show their folder as a label in `/help`. Same-named commands in different subdirectories are distinguished by their label.

## Complete Examples

### Example 1: Simple Code Review

```markdown
# .claude/commands/review.md

---
description: Review code for quality issues
---

Review this code for:
1. Bugs and logic errors
2. Security vulnerabilities
3. Performance issues
4. Code style and readability

Provide specific suggestions with code examples.
```

### Example 2: Git Commit with Context

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

### Example 3: Issue Fixer with Arguments

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

### Example 4: PR Review

```markdown
# .claude/commands/pr-review.md

---
argument-hint: [pr-number]
allowed-tools: Bash(gh pr:*), Bash(git:*)
description: Review a pull request
---

## PR Information

!`gh pr view $1 --json title,body,files,additions,deletions`

## Changed Files

!`gh pr diff $1 --name-only`

## Full Diff

!`gh pr diff $1`

## Task

Review this PR for:
1. Correctness and logic
2. Security concerns
3. Performance implications
4. Test coverage
5. Documentation needs

Provide actionable feedback.
```

### Example 5: Database Migration

```markdown
# .claude/commands/backend/migrate.md

---
allowed-tools: Bash(npm run migrate:*), Bash(psql:*), Read
description: Create and run database migrations
argument-hint: [migration-name]
---

## Existing Migrations

!`ls -la migrations/`

## Current Schema

@prisma/schema.prisma

## Task

Create a new migration named "$1":
1. Generate migration file
2. Write up/down migrations
3. Test migration locally
4. Update schema documentation
```

### Example 6: Security Audit

```markdown
# .claude/commands/security-audit.md

---
allowed-tools: Bash(npm audit:*), Bash(git log:*), Grep, Glob
description: Run security audit on codebase
---

## Dependency Audit

!`npm audit --json 2>/dev/null | head -100`

## Task

1. Analyze npm audit results
2. Search for common vulnerabilities:
   - SQL injection patterns
   - XSS vulnerabilities
   - Hardcoded secrets
   - Insecure dependencies
3. Check authentication/authorization code
4. Review input validation
5. Provide remediation steps
```

### Example 7: Forked Context Command

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

This runs in a separate subagent context, keeping the main conversation clean.

## Viewing Commands

```
> /help
```

Shows all available commands grouped by:
- Built-in commands
- Project commands (from `.claude/commands/`)
- User commands (from `~/.claude/commands/`)

## Commands vs Skills

| Aspect | Commands | Skills |
|--------|----------|--------|
| Complexity | Simple prompts | Complex multi-step workflows |
| Structure | Single `.md` file | Directory with `SKILL.md` + supporting files |
| Discovery | Explicit (`/name`) | Can be automatic |
| Best for | Quick, reusable prompts | Complex automation, multi-tool workflows |

## Tips

1. **Start simple**: Begin with basic prompts, add features as needed
2. **Use descriptions**: Always add `description` for discoverability
3. **Be specific with tools**: Grant minimum required permissions
4. **Test incrementally**: Test commands after each change
5. **Document arguments**: Use `argument-hint` to show expected inputs
6. **Organize early**: Use subdirectories before commands proliferate
7. **Share with team**: Commit `.claude/commands/` to version control

## Troubleshooting

**Command not showing in `/help`**:
- Check file is in correct location
- Ensure `.md` extension
- Verify no YAML syntax errors in frontmatter

**Bash commands not executing**:
- Add required tools to `allowed-tools`
- Check command syntax in backticks

**Arguments not substituting**:
- Use `$ARGUMENTS` for all args, `$1`/`$2` for positional
- Ensure no spaces around `$` in variable names

**File references not working**:
- Use `@` prefix directly before path
- Ensure file exists and is readable

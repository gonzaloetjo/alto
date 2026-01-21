# Claude Code Skills (`.claude/skills/`)

Skills are reusable capabilities that Claude can automatically invoke when relevant. They're more powerful than commands - supporting multiple files, progressive disclosure, and automatic discovery.

## Directory Structure

```
.claude/skills/
├── code-review/
│   ├── SKILL.md              # Required: main skill definition
│   ├── CHECKLIST.md          # Supporting documentation
│   └── examples.md           # Usage examples
├── pdf-processing/
│   ├── SKILL.md
│   └── scripts/
│       ├── fill_form.py
│       └── validate.py
└── commit-helper/
    └── SKILL.md              # Simple skill (single file)
```

## Scope Locations

| Location | Scope | Shared |
|----------|-------|--------|
| `.claude/skills/` | Project (team) | Yes (committed to git) |
| `~/.claude/skills/` | User (personal) | No |

## SKILL.md Format

### Basic Skill

```markdown
---
name: code-review
description: Reviews code for quality, security, and maintainability issues
---

# Code Review

When reviewing code, analyze:
1. Logic errors and bugs
2. Security vulnerabilities
3. Performance issues
4. Code style and readability
5. Test coverage gaps

Provide specific, actionable feedback with code examples.
```

### Full-Featured Skill

```yaml
---
name: security-audit
description: Performs security audits on codebases. Checks for OWASP vulnerabilities, secrets exposure, and insecure patterns.
allowed-tools: Read, Grep, Glob, Bash
model: opus
context: fork
agent: general-purpose
user-invocable: true
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly.sh"
---

# Security Audit Skill

## Scope

This skill performs comprehensive security audits including:
- OWASP Top 10 vulnerability scanning
- Secrets and credential detection
- Dependency vulnerability analysis
- Authentication/authorization review

## Process

1. Scan for hardcoded secrets
2. Check dependency vulnerabilities
3. Review authentication flows
4. Analyze input validation
5. Check for injection vulnerabilities

## Output Format

Provide findings in this format:
- **CRITICAL**: Immediate action required
- **HIGH**: Fix before next release
- **MEDIUM**: Plan remediation
- **LOW**: Consider improving

## Resources

For detailed checklists, see [CHECKLIST.md](CHECKLIST.md)
```

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase, hyphens, max 64 chars) |
| `description` | Yes | When to use (keyword-rich for auto-discovery, max 1024 chars) |
| `allowed-tools` | No | Comma-separated tools: `Read, Grep, Glob, Bash` |
| `model` | No | Model override: `sonnet`, `opus`, `haiku` |
| `context` | No | `fork` for isolated subagent context |
| `agent` | No | Agent type when `context: fork` |
| `user-invocable` | No | Show in `/help` (default: true) |
| `hooks` | No | PreToolUse/PostToolUse hooks |

## String Substitutions

Use these variables in your skill content:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed to the skill |
| `$1`, `$2`, etc. | Positional arguments |
| `${CLAUDE_SESSION_ID}` | Current session ID |

```markdown
---
name: log-activity
description: Logs activity to session-specific file
---

Log the following to logs/${CLAUDE_SESSION_ID}.log:

Activity: $ARGUMENTS
Timestamp: $(date)
```

## Progressive Disclosure Pattern

For complex skills, keep `SKILL.md` concise and link to supporting files:

```
my-skill/
├── SKILL.md              # Overview (<500 lines)
├── reference.md          # Detailed API/reference docs
├── examples.md           # Usage examples
├── templates/
│   ├── template1.md
│   └── template2.md
└── scripts/
    ├── helper.py
    └── validate.sh
```

**In SKILL.md:**

```markdown
---
name: api-generator
description: Generates REST API endpoints with tests and documentation
---

# API Generator

Generates complete API endpoints including:
- Route handlers
- Input validation
- Database queries
- Unit tests
- OpenAPI documentation

## Quick Start

Specify the resource name and fields:
```
/api-generator users name:string email:string:unique
```

## Resources

- **Full Reference**: See [reference.md](reference.md) for all options
- **Examples**: See [examples.md](examples.md) for common patterns
- **Templates**: Available in `templates/` directory

## Validation

Run `scripts/validate.sh` to verify generated code.
```

## Examples

### Simple Skill: Commit Message Helper

```markdown
# .claude/skills/commit-helper/SKILL.md

---
name: commit-helper
description: Generates conventional commit messages from staged changes
allowed-tools: Bash
---

# Commit Message Helper

Generate a commit message following conventional commits format.

## Process

1. Run `git diff --cached` to see staged changes
2. Analyze the changes
3. Generate a commit message:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for refactoring
   - `test:` for tests
   - `chore:` for maintenance

## Format

```
type(scope): short description

- Bullet point details
- Another detail

Closes #issue-number
```
```

### Complex Skill: Database Migration

```markdown
# .claude/skills/db-migrate/SKILL.md

---
name: db-migrate
description: Creates and manages database migrations. Use for schema changes, data migrations, and rollbacks.
allowed-tools: Bash, Read, Write, Glob
model: sonnet
---

# Database Migration Skill

## Capabilities

- Generate migration files
- Apply migrations
- Rollback migrations
- Validate migration safety

## Commands

### Create Migration
```
/db-migrate create add_users_table
```

### Apply Migrations
```
/db-migrate up
/db-migrate up --step 1
```

### Rollback
```
/db-migrate down
/db-migrate down --step 2
```

## Safety Checks

Before applying migrations:
1. Verify no data loss in down migration
2. Check for long-running operations
3. Validate foreign key constraints

See [safety-checklist.md](safety-checklist.md) for details.
```

### Isolated Skill with Subagent

```markdown
# .claude/skills/parallel-research/SKILL.md

---
name: parallel-research
description: Researches multiple topics in parallel using subagents
context: fork
agent: general-purpose
allowed-tools: WebSearch, WebFetch, Read
---

# Parallel Research

This skill spawns isolated subagents to research topics concurrently.

## Usage

```
/parallel-research "topic1" "topic2" "topic3"
```

## Process

1. Parse input topics
2. Spawn research agent for each topic
3. Gather and synthesize results
4. Return consolidated findings

## Output Format

For each topic:
- **Summary**: 2-3 sentence overview
- **Key Findings**: Bullet points
- **Sources**: Links to references
```

### Skill with Scripts

```markdown
# .claude/skills/pdf-processor/SKILL.md

---
name: pdf-processor
description: Extracts, fills, and validates PDF forms
allowed-tools: Bash, Read, Write
---

# PDF Processor

## Capabilities

- Extract form fields from PDFs
- Fill PDF forms with data
- Validate filled forms

## Scripts

### Extract Fields
```bash
python scripts/extract_fields.py input.pdf
```

### Fill Form
```bash
python scripts/fill_form.py template.pdf data.json output.pdf
```

### Validate
```bash
python scripts/validate.py filled.pdf
```

## Supported Formats

- PDF 1.4+ with AcroForms
- XFA forms (limited)
- Flattened forms (read-only)
```

## Skills vs Commands vs Agents

| Aspect | Commands | Skills | Agents |
|--------|----------|--------|--------|
| **Structure** | Single `.md` | Directory with `SKILL.md` | Single `.md` |
| **Discovery** | Explicit (`/name`) | Automatic + explicit | Task delegation |
| **Complexity** | Simple prompts | Multi-file capabilities | Specialized personas |
| **Context** | Main conversation | Optional fork | Always forked |
| **Best for** | Quick prompts | Complex workflows | Isolated tasks |

## Auto-Discovery

Claude automatically suggests skills when:
- User request matches skill description keywords
- Task aligns with skill capabilities
- Context indicates skill would help

**Tips for better discovery:**
- Use keyword-rich descriptions
- Include common synonyms
- Mention specific use cases

```markdown
---
description: Reviews pull requests for code quality, security issues, performance problems, and test coverage. Use for PR review, code review, merge requests.
---
```

## Hooks in Skills

```yaml
---
name: safe-executor
description: Executes code with safety validations
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "./scripts/lint-file.sh"
---
```

## Best Practices

1. **Keep SKILL.md focused**: Overview and quick reference only
2. **Use progressive disclosure**: Link to detailed docs
3. **Restrict tools**: Only grant necessary permissions
4. **Make descriptions searchable**: Include keywords and use cases
5. **Bundle scripts**: Include utility scripts in skill directory
6. **Test thoroughly**: Verify skill works with real requests
7. **Document clearly**: Include examples and expected output

## Troubleshooting

**Skill not auto-discovered:**
- Check description keywords match user requests
- Verify `user-invocable: true` (or omit for default)
- Ensure SKILL.md has valid frontmatter

**Scripts not found:**
- Use relative paths from skill directory
- Ensure scripts are executable (`chmod +x`)
- Check working directory context

**Skill too verbose:**
- Use `context: fork` to isolate output
- Move details to supporting files
- Summarize rather than show everything

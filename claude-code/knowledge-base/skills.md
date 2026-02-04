# Claude Code > Skills

> Reusable capabilities in `.claude/skills/`.

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
| `.claude/skills/` | Project (team) | Yes (committed) |
| `~/.claude/skills/` | User (personal) | No |

---

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
disable-model-invocation: false
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
```

---

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase, hyphens, max 64 chars) |
| `description` | Yes | When to use (keyword-rich for discovery, max 1024 chars) |
| `allowed-tools` | No | Comma-separated tools: `Read, Grep, Glob, Bash` |
| `model` | No | Model override: `sonnet`, `opus`, `haiku` |
| `context` | No | `fork` for isolated subagent context |
| `agent` | No | Agent type when `context: fork` |
| `user-invocable` | No | Show in `/help` (default: true) |
| `disable-model-invocation` | No | Prevent auto-invocation (default: false) |
| `hooks` | No | PreToolUse/PostToolUse hooks |

---

## Activation Model

### Soft vs Strong Activation

| Type | Description | When to Use |
|------|-------------|-------------|
| **Soft** | Claude *could* auto-invoke via description matching | Context-dependent procedures |
| **Strong** | Explicitly called (`/skill`) or referenced in agent .md | Predictable workflows |

```
┌─────────────────────────────────────────────────────────────────┐
│                     SKILL ACTIVATION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SOFT (probabilistic)              STRONG (deterministic)        │
│  ┌─────────────────────┐          ┌─────────────────────┐       │
│  │ User says "deploy"  │          │ User types /deploy  │       │
│  │         ↓           │          │         ↓           │       │
│  │ Claude checks       │          │ Skill loads         │       │
│  │ skill descriptions  │          │ immediately         │       │
│  │         ↓           │          │                     │       │
│  │ Maybe suggests      │          │                     │       │
│  │ deploy skill        │          │                     │       │
│  └─────────────────────┘          └─────────────────────┘       │
│                                                                  │
│  • May not trigger                 • Always triggers             │
│  • Depends on description          • Explicit invocation         │
│  • Context-dependent               • User-controlled             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### When to Use Each

| Scenario | Activation | Settings |
|----------|------------|----------|
| Common workflow user remembers | Strong (`/skill`) | Default |
| Context-dependent procedure | Soft (auto) | Default |
| Background reference | Soft | `user-invocable: false` |
| Dangerous operations | Strong only | `disable-model-invocation: true` |

---

## String Substitutions

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

---

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
## Quick Start

Specify the resource name and fields:
/api-generator users name:string email:string:unique

## Resources

- **Full Reference**: See [reference.md](reference.md) for all options
- **Examples**: See [examples.md](examples.md) for common patterns
```

---

## Examples

### Simple Commit Helper

```markdown
# .claude/skills/commit-helper/SKILL.md

---
name: commit-helper
description: Generates conventional commit messages from staged changes
allowed-tools: Bash
---

# Commit Message Helper

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

/parallel-research "topic1" "topic2" "topic3"

## Output Format

For each topic:
- **Summary**: 2-3 sentence overview
- **Key Findings**: Bullet points
- **Sources**: Links to references
```

---

## Skills vs Commands vs Agents

| Aspect | Commands | Skills | Agents |
|--------|----------|--------|--------|
| **Structure** | Single `.md` | Directory with `SKILL.md` | Single `.md` |
| **Discovery** | Explicit (`/name`) | Automatic + explicit | Task delegation |
| **Complexity** | Simple prompts | Multi-file capabilities | Specialized personas |
| **Context** | Main conversation | Optional fork | Always forked |
| **Best for** | Quick prompts | Complex workflows | Isolated tasks |

---

## Skills vs Rules

| Aspect | Skills | Rules |
|--------|--------|-------|
| **Loading** | On-demand (lazy) | Always in context |
| **Activation** | Probabilistic or explicit | Deterministic |
| **Context cost** | Only paid when invoked | Always paid |
| **Best for** | Task-specific procedures | Universal conventions |

---

## Best Practices

1. **Keep SKILL.md focused**: Overview and quick reference only
2. **Use progressive disclosure**: Link to detailed docs
3. **Restrict tools**: Only grant necessary permissions
4. **Make descriptions searchable**: Include keywords and use cases
5. **Bundle scripts**: Include utility scripts in skill directory
6. **Disable auto-invocation for dangerous ops**: `disable-model-invocation: true`

---

## Related

- [commands.md](commands.md) - Simple slash commands
- [agents.md](agents.md) - Isolated specialists
- [rules.md](rules.md) - Always-on conventions

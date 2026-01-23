# Claude Code > Rules

> Modular instruction files in `.claude/rules/`.

## Directory Structure

```
.claude/rules/
├── code-style.md           # General coding standards
├── testing.md              # Testing conventions
├── security.md             # Security requirements
├── api-design.md           # API guidelines
└── frontend/
    ├── react.md            # React-specific rules
    └── styling.md          # CSS/styling rules
```

## Scope Locations

| Location | Scope | Shared |
|----------|-------|--------|
| `.claude/rules/` | Project (team) | Yes (committed) |
| `~/.claude/rules/` | User (personal) | No |

---

## Rule File Format

### Basic Rule (applies to all files)

```markdown
# Security Requirements

- Never commit secrets or API keys
- Always validate user input
- Use parameterized queries for database operations
- Implement proper error handling without exposing internals
```

### Path-Specific Rule

Use YAML frontmatter to restrict rules to specific file patterns:

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/middleware/**/*.ts"
---

# API Development Rules

- All endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments
- Follow REST conventions for HTTP methods
```

---

## Path Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under src/ |
| `*.md` | Markdown files in project root only |
| `{src,lib}/**/*.ts` | TypeScript in src/ or lib/ |
| `test/**/*.test.ts` | Test files in test directory |
| `!**/node_modules/**` | Exclude node_modules |

---

## Examples

### Code Style Rules

```markdown
# .claude/rules/code-style.md

---
paths:
  - "src/**/*.{ts,tsx}"
---

# TypeScript Style Guide

## Naming Conventions
- Use PascalCase for types, interfaces, and classes
- Use camelCase for variables, functions, and methods
- Use UPPER_SNAKE_CASE for constants

## Code Organization
- One component per file
- Group imports: external, internal, relative
- Export types separately from implementations

## Best Practices
- Prefer `const` over `let`
- Use strict TypeScript settings
- Avoid `any` type - use `unknown` when type is truly unknown
```

### Testing Rules

```markdown
# .claude/rules/testing.md

---
paths:
  - "test/**/*.test.ts"
  - "src/**/*.spec.ts"
  - "**/__tests__/**"
---

# Testing Guidelines

## File Naming
- Test files: `{name}.test.ts` or `{name}.spec.ts`
- One test file per source file

## Test Structure
- Use descriptive test names that explain the scenario
- Follow Arrange-Act-Assert pattern
- One assertion per test when possible

## Coverage Requirements
- Minimum 80% code coverage
- 100% coverage for critical paths
```

### Security Rules

```markdown
# .claude/rules/security.md

# Security Requirements

These rules apply to ALL files in the project.

## Secrets Management
- NEVER hardcode secrets, API keys, or credentials
- Use environment variables for all sensitive values
- Never log sensitive information

## Input Validation
- Validate all user input at system boundaries
- Use allowlists over denylists
- Sanitize data before database operations
```

---

## Rules vs CLAUDE.md

| Aspect | `CLAUDE.md` | `.claude/rules/` |
|--------|-------------|------------------|
| Structure | Single file | Multiple files |
| Organization | Sections | Separate files |
| Path targeting | No | Yes (frontmatter) |
| Best for | Project overview | Detailed guidelines |
| Maintenance | Can get unwieldy | Modular and focused |

**Recommendation**: Use `CLAUDE.md` for high-level project context and `.claude/rules/` for detailed coding standards.

---

## Rules vs Skills: Activation Model

| Aspect | Rules | Skills |
|--------|-------|--------|
| **Loading** | Always in context | On-demand (lazy) |
| **Activation** | Deterministic | Probabilistic or explicit |
| **Context cost** | Always paid | Only when invoked |
| **Best for** | Universal conventions | Task-specific procedures |

---

## Key Insight

> **Rules are suggestions that the LLM weighs against other context. Hooks are enforcement.**
>
> A rule saying "don't edit .env" is parsed by Claude and *maybe* followed.
> A PreToolUse hook blocking .env edits *always* runs and blocks the operation.

---

## Loading Behavior

- All rules in `.claude/rules/` are loaded at session start
- Path-specific rules are filtered based on current context
- User rules (`~/.claude/rules/`) load after project rules
- No explicit ordering - keep rules non-conflicting

---

## Best Practices

1. **Keep rules focused**: Each file covers ONE topic
2. **Be specific**: Vague rules get ignored; specific rules get followed
3. **Include examples**: Show code examples of good/bad patterns
4. **Use path patterns sparingly**: Rules without `paths` apply globally
5. **Review regularly**: Update rules as project conventions evolve

---

## Related

- [memory.md](memory.md) - CLAUDE.md memory files
- [skills.md](skills.md) - On-demand capabilities
- [hooks.md](hooks.md) - Enforcement via hooks

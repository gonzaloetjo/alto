# Claude Code Rules (`.claude/rules/`)

Rules are modular instruction files that provide context-specific guidance to Claude. They replace or supplement a monolithic `CLAUDE.md` with focused, organized files.

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
| `.claude/rules/` | Project (team) | Yes (committed to git) |
| `~/.claude/rules/` | User (personal) | No |

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

## Path Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under src/ |
| `*.md` | Markdown files in project root only |
| `{src,lib}/**/*.ts` | TypeScript in src/ or lib/ |
| `test/**/*.test.ts` | Test files in test directory |
| `!**/node_modules/**` | Exclude node_modules |

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
- Prefix interfaces with `I` only when necessary for clarity

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
- Place tests adjacent to source or in `__tests__/`

## Test Structure
- Use descriptive test names that explain the scenario
- Follow Arrange-Act-Assert pattern
- One assertion per test when possible

## Coverage Requirements
- Minimum 80% code coverage
- 100% coverage for critical paths
- All edge cases must have tests
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

## Authentication
- Use secure session management
- Implement proper CSRF protection
- Use secure password hashing (bcrypt, argon2)

## Dependencies
- Keep dependencies updated
- Review security advisories regularly
- Use `npm audit` before deployments
```

### Solidity/Smart Contract Rules

```markdown
# .claude/rules/solidity.md

---
paths:
  - "src/contracts/**/*.sol"
  - "contracts/**/*.sol"
---

# Solidity Development Rules

## Security
- Use OpenZeppelin contracts when available
- Follow checks-effects-interactions pattern
- Use reentrancy guards on external calls
- Validate all external inputs

## Gas Optimization
- Use `calldata` for read-only function parameters
- Cache storage variables in memory for loops
- Use `unchecked` blocks where overflow is impossible
- Prefer `++i` over `i++`

## Code Style
- Use NatSpec comments for all public functions
- Order: receive/fallback, external, public, internal, private
- Use custom errors over require strings
```

### API Design Rules

```markdown
# .claude/rules/api-design.md

---
paths:
  - "src/api/**/*"
  - "src/routes/**/*"
  - "src/controllers/**/*"
---

# API Design Guidelines

## REST Conventions
- Use nouns for resources, verbs for actions
- Use plural nouns: `/users`, `/orders`
- Use HTTP methods correctly: GET (read), POST (create), PUT (replace), PATCH (update), DELETE (remove)

## Response Format
```json
{
  "success": true,
  "data": { ... },
  "meta": { "page": 1, "total": 100 }
}
```

## Error Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [ ... ]
  }
}
```

## Versioning
- Use URL versioning: `/api/v1/users`
- Maintain backward compatibility within major versions
```

### Frontend/React Rules

```markdown
# .claude/rules/frontend/react.md

---
paths:
  - "src/components/**/*.tsx"
  - "src/pages/**/*.tsx"
  - "src/hooks/**/*.ts"
---

# React Development Rules

## Component Structure
- Functional components only (no class components)
- Use hooks for state and side effects
- Keep components under 200 lines

## State Management
- Use local state for component-specific data
- Use context for cross-cutting concerns
- Consider Zustand/Redux for complex global state

## Performance
- Memoize expensive computations with `useMemo`
- Memoize callbacks passed to children with `useCallback`
- Use `React.memo` for pure presentational components

## Hooks
- Custom hooks must start with `use`
- Extract reusable logic into custom hooks
- Keep hooks focused on single responsibility
```

## Organization Best Practices

### Use Subdirectories for Large Projects

```
.claude/rules/
├── general/
│   ├── code-style.md
│   ├── git-workflow.md
│   └── documentation.md
├── backend/
│   ├── api.md
│   ├── database.md
│   └── security.md
├── frontend/
│   ├── react.md
│   ├── styling.md
│   └── accessibility.md
└── testing/
    ├── unit.md
    ├── integration.md
    └── e2e.md
```

### Keep Rules Focused

Each rule file should cover ONE topic. This makes them:
- Easier to maintain
- Easier to enable/disable
- More discoverable
- Less likely to conflict

### Use Path-Specific Rules Sparingly

- Rules without `paths` apply globally (usually what you want)
- Use `paths` only when rules are truly specific to certain files
- Avoid overly complex path patterns

## Rules vs CLAUDE.md

| Aspect | `CLAUDE.md` | `.claude/rules/` |
|--------|-------------|------------------|
| Structure | Single file | Multiple files |
| Organization | Sections | Separate files |
| Path targeting | No | Yes (frontmatter) |
| Best for | Project overview | Detailed guidelines |
| Maintenance | Can get unwieldy | Modular and focused |

**Recommendation**: Use `CLAUDE.md` for high-level project context and `.claude/rules/` for detailed coding standards.

## Loading Behavior

- All rules in `.claude/rules/` are loaded at session start
- Path-specific rules are filtered based on current context
- User rules (`~/.claude/rules/`) load after project rules
- No explicit ordering - keep rules non-conflicting

## Tips

1. **Start simple**: Begin with 2-3 rule files, expand as needed
2. **Be specific**: Vague rules get ignored; specific rules get followed
3. **Include examples**: Show code examples of good/bad patterns
4. **Review regularly**: Update rules as project conventions evolve
5. **Test rules**: Verify Claude follows them in practice

# Claude Code > Memory Files

> CLAUDE.md and memory file configuration.

## File Locations

| File | Scope | Shared |
|------|-------|--------|
| `./CLAUDE.md` | Project root | Yes (committed) |
| `./.claude/CLAUDE.md` | Project (alternative) | Yes (committed) |
| `./CLAUDE.local.md` | Personal project | No (gitignored) |
| `~/.claude/CLAUDE.md` | User global | No |

---

## Loading Order

Memory files load in this order (later supplements earlier):

1. `~/.claude/CLAUDE.md` (user global)
2. `~/.claude/rules/*` (user rules)
3. `./CLAUDE.md` or `./.claude/CLAUDE.md` (project)
4. `./.claude/rules/*` (project rules)
5. `./CLAUDE.local.md` (personal project)

---

## Basic Structure

```markdown
# Project Name

Brief description of the project.

## Tech Stack

- Language: TypeScript
- Framework: Next.js
- Database: PostgreSQL
- Testing: Jest

## Architecture

Describe the overall architecture here.

## Coding Standards

- Use functional components
- Prefer composition over inheritance
- Write tests for all new features

## Common Commands

- `npm run dev` - Start development server
- `npm test` - Run tests
- `npm run build` - Production build

## Important Files

- `src/config/` - Configuration files
- `src/lib/` - Shared utilities
- `src/components/` - React components
```

---

## File References with `@`

Import content from other files:

```markdown
# Project Overview

See the main documentation:
@README.md

## API Reference

@docs/api.md

## Contributing Guidelines

@CONTRIBUTING.md
```

File references:
- Are relative to the markdown file's location
- Support up to 5 levels of recursive imports
- Are expanded at load time

---

## Recommended Sections

### Project Overview

```markdown
# MyProject

A real-time collaboration platform for document editing.

## Purpose

Enable teams to edit documents simultaneously with conflict resolution.

## Key Features

- Real-time sync via WebSockets
- Operational transformation for conflict resolution
- Version history and rollback
```

### Architecture

```markdown
## Architecture

### Frontend
- Next.js 14 with App Router
- React Query for server state
- Tailwind CSS for styling

### Backend
- Node.js with Express
- PostgreSQL for persistence
- Redis for pub/sub
```

### Directory Structure

```markdown
## Directory Structure

src/
├── app/              # Next.js app router pages
├── components/       # React components
│   ├── ui/           # Primitive UI components
│   └── features/     # Feature-specific components
├── lib/              # Shared utilities
├── hooks/            # Custom React hooks
├── services/         # API service clients
├── types/            # TypeScript types
└── config/           # Configuration
```

### Coding Standards

```markdown
## Coding Standards

### Naming Conventions
- Components: PascalCase (`UserProfile.tsx`)
- Utilities: camelCase (`formatDate.ts`)
- Constants: UPPER_SNAKE_CASE

### Code Style
- Use TypeScript strict mode
- Prefer `const` over `let`
- Use async/await over raw promises

### Error Handling
- Use custom error classes
- Always log errors with context
- Return meaningful error messages
```

### Development Workflow

```markdown
## Development Workflow

### Setup
npm install
cp .env.example .env.local
npm run db:migrate
npm run dev

### Testing
npm test              # Run all tests
npm test -- --watch   # Watch mode
npm run test:e2e      # End-to-end tests
```

### Things to Avoid

```markdown
## Things to Avoid

- DON'T commit `.env` files
- DON'T use `any` type - use `unknown` if truly unknown
- DON'T add dependencies without team discussion
- DON'T modify database schema without migration
- DON'T push directly to main branch
```

### Claude Instructions

```markdown
## Claude Instructions

When working on this project:

1. Always run tests after making changes
2. Follow the existing code style
3. Update documentation for API changes
4. Use conventional commits for messages
5. Check for TypeScript errors before committing

### Preferred Libraries
- Dates: date-fns (not moment)
- HTTP: fetch API (not axios)
- Validation: zod
- Testing: Vitest
```

---

## CLAUDE.local.md

Personal overrides that won't be committed:

```markdown
# Personal Settings

## My Sandbox
- Test URL: http://localhost:3001
- Test user: dev@test.com / password123

## My Preferences
- I prefer verbose explanations
- Always show me the diff before committing
- Run tests in watch mode

## Notes
- Working on feature/user-profile branch
- TODO: Fix the caching issue in user service
```

---

## User Global (~/.claude/CLAUDE.md)

Instructions that apply to all projects:

```markdown
# Global Preferences

## Coding Style
- I prefer functional programming patterns
- Use early returns over nested conditionals
- Keep functions under 30 lines

## Communication
- Be concise in explanations
- Show code examples when explaining concepts
- Ask before making large changes

## Git
- Use conventional commits
- Always sign commits with GPG
- Rebase before merging
```

---

## Best Practices

1. **Keep it focused**: Include only what Claude needs to know
2. **Update regularly**: Keep information current
3. **Use file references**: Link to detailed docs with `@`
4. **Organize with headers**: Make it scannable
5. **Include examples**: Show don't just tell
6. **Document patterns**: Explain project-specific patterns
7. **List common commands**: Quick reference for workflows

---

## CLAUDE.md vs Rules

| Aspect | CLAUDE.md | .claude/rules/ |
|--------|-----------|----------------|
| Structure | Single file | Multiple files |
| Purpose | Project overview | Specific guidelines |
| Organization | Sections | Separate files |
| Path targeting | No | Yes (frontmatter) |
| Best for | Context & overview | Detailed rules |

**Recommendation**: Use `CLAUDE.md` for project overview and `.claude/rules/` for detailed coding standards.

---

## Related

- [rules.md](rules.md) - Modular rule files
- [settings.md](settings.md) - Configuration options

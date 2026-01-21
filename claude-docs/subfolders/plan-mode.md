# Claude Code Plan Mode

Plan Mode is a specialized permission mode for safe code analysis and planning. Claude operates in read-only mode, exploring the codebase and creating detailed implementation plans before any code changes.

## Purpose

Plan Mode enables:
- **Safe exploration**: Analyze codebases without risk of changes
- **Thorough planning**: Create detailed plans before implementation
- **Interactive clarification**: Ask questions to gather requirements
- **Architecture decisions**: Think through complex problems step-by-step

## When to Use Plan Mode

| Scenario | Why Plan Mode Helps |
|----------|---------------------|
| Multi-file features | Plan the approach before touching many files |
| Complex refactoring | Understand dependencies and plan migration |
| Code exploration | Research without accidentally modifying |
| Architecture decisions | Evaluate options before committing |
| Onboarding to codebase | Learn structure safely |

## Plans Directory

### Default Location

```
~/.claude/plans/
```

Plans are stored at user level by default.

### Custom Location

Configure in `.claude/settings.json`:

```json
{
  "plansDirectory": "./plans"
}
```

This stores plans in the project directory instead.

## Entering Plan Mode

### Method 1: Keyboard Toggle

While in an interactive session:

```
Shift+Tab    # Cycles through permission modes
```

Mode cycle:
1. **Normal** → asks for permission on each action
2. **Auto-Accept** (`⏵⏵ accept edits on`) → auto-approves changes
3. **Plan Mode** (`⏸ plan mode on`) → read-only analysis

### Method 2: Start in Plan Mode

```bash
claude --permission-mode plan
```

### Method 3: Headless Plan Mode

```bash
claude --permission-mode plan -p "Analyze the auth system and suggest improvements"
```

## Tools Available in Plan Mode

### Allowed (Read-Only)

| Tool | Purpose |
|------|---------|
| `Read` | Examine file contents |
| `Glob` | Find files by pattern |
| `Grep` | Search for patterns |
| `AskUserQuestion` | Ask clarifying questions |
| `ExitPlanMode` | Signal ready to implement |

### Blocked (Modifications)

| Tool | Why Blocked |
|------|-------------|
| `Edit` | Modifies files |
| `Write` | Creates/overwrites files |
| `Bash` | Can execute arbitrary commands |
| `WebFetch` | External requests |
| `WebSearch` | External requests |

## Plan Mode Workflow

### 1. Enter Plan Mode

```bash
claude --permission-mode plan
```

### 2. Describe the Task

```
> I need to refactor our authentication system to use OAuth2.
  Create a detailed migration plan.
```

### 3. Claude Analyzes

Claude will:
- Read relevant files
- Search for patterns
- Map dependencies
- Ask clarifying questions

### 4. Answer Clarifying Questions

Claude uses `AskUserQuestion` to gather requirements:

```
Claude: What OAuth2 providers should we support?
  [ ] Google
  [ ] GitHub
  [ ] Microsoft
  [ ] Custom OIDC

Claude: Should we maintain backward compatibility with existing sessions?
  [ ] Yes, migrate gradually
  [ ] No, clean cutover
```

### 5. Receive the Plan

Claude provides a detailed implementation plan with:
- Step-by-step approach
- Files to modify
- Potential risks
- Testing strategy

### 6. Exit Plan Mode

When ready to implement:
- Press `Shift+Tab` to switch to Normal or Auto-Accept mode
- Or start a new session without `--permission-mode plan`

## Configuration

### Set Plan Mode as Default

```json
{
  "permissions": {
    "defaultMode": "plan"
  }
}
```

### Use OpusPlan Model

The `opusplan` model alias provides hybrid planning:
- **Plan Mode**: Uses Claude Opus (superior reasoning)
- **Execution Mode**: Switches to Claude Sonnet (efficient coding)

```bash
claude --model opusplan
```

Or in settings:

```json
{
  "model": "opusplan"
}
```

### Limit Thinking Budget

Control analysis depth:

```bash
export MAX_THINKING_TOKENS=15000
claude --permission-mode plan
```

## Example Session

```bash
$ claude --permission-mode plan

> Analyze the codebase and create a plan to add real-time notifications

Claude: I'll analyze the codebase to understand the current architecture
and create a comprehensive plan for adding real-time notifications.

[Reads package.json, src/config/, src/services/]

Claude: I have a few questions to clarify the requirements:

1. What notification channels do you need?
   [ ] In-app only
   [ ] In-app + Email
   [ ] In-app + Email + Push

2. What's the expected scale?
   [ ] < 1,000 concurrent users
   [ ] 1,000 - 10,000 concurrent users
   [ ] > 10,000 concurrent users

> In-app + Email, 1,000 - 10,000 users

Claude: Based on my analysis, here's the implementation plan:

## Phase 1: Infrastructure Setup
1. Add Redis for pub/sub messaging
2. Create WebSocket server module
3. Set up notification queue

## Phase 2: Core Implementation
1. Create notification service (src/services/notification.ts)
2. Add WebSocket connection handler
3. Implement notification types and templates

## Phase 3: Integration
1. Add notification triggers to existing events
2. Create email notification worker
3. Add user notification preferences

## Phase 4: Testing & Deployment
1. Unit tests for notification service
2. Integration tests for WebSocket
3. Load testing for scale requirements

Ready to proceed with implementation?

> Yes, let's start with Phase 1

[Press Shift+Tab to exit Plan Mode and begin implementation]
```

## Encouraging Questions in CLAUDE.md

Add to your project's `CLAUDE.md`:

```markdown
## Planning Guidelines

Always ask clarifying questions when:
- Multiple valid approaches exist
- Requirements are ambiguous
- Trade-offs need consideration
- Scale/performance requirements are unclear
```

## Plan Mode vs Other Features

| Feature | Purpose | Modifies Code |
|---------|---------|---------------|
| **Plan Mode** | Safe analysis and planning | No |
| **Normal Mode** | Interactive development | With permission |
| **Auto-Accept** | Fast execution | Automatically |
| **Agents** | Delegated tasks | Configurable |

## Best Practices

1. **Start complex tasks in Plan Mode**: Get alignment before coding
2. **Use OpusPlan for architecture**: Better reasoning for planning
3. **Answer questions thoughtfully**: Better input = better plans
4. **Iterate on plans**: Refine before switching to execution
5. **Save plans for reference**: Configure `plansDirectory` for persistence

## Troubleshooting

**Can't modify files in Plan Mode:**
- This is expected behavior
- Exit Plan Mode with `Shift+Tab` to enable modifications

**Claude not asking enough questions:**
- Add guidance to `CLAUDE.md`
- Be explicit: "Ask clarifying questions before planning"

**Plan too vague:**
- Provide more context in your initial request
- Answer clarifying questions with specifics
- Ask for more detail on specific sections

# Claude Code `.claude/` Folder Documentation

Comprehensive analysis of all configurable components in the Claude Code `.claude/` directory.

## Directory Structure

```
.claude/
├── settings.json          # Configuration
├── CLAUDE.md              # Project memory file
├── commands/              # Custom slash commands
├── rules/                 # Modular instruction files
├── skills/                # Reusable capabilities
├── agents/                # Custom subagents
├── hooks/                 # Hook scripts
├── output-styles/         # Custom output style definitions
├── .mcp.json              # MCP server configuration
└── (plansDirectory)       # Plan Mode storage (configurable)
```

---

## Feature Analysis

### 1. Settings (`settings.json`)

| Aspect | Details |
|--------|---------|
| **Objective** | Control Claude Code's behavior, permissions, tool access, and integrations at a foundational level |
| **Context Management** | Does not add to conversation context. Configures what Claude *can do*, not what it *knows* |
| **Lifecycle Stage** | **Pre-session** - loaded before Claude starts, configures the environment |
| **Activation** | Automatic on session start |

**Key Insight**: Settings are the "permissions layer" - they define boundaries and capabilities but don't influence Claude's knowledge or reasoning directly.

**Documentation**: [settings.md](settings.md)

---

### 2. Memory Files (`CLAUDE.md`)

| Aspect | Details |
|--------|---------|
| **Objective** | Provide persistent project context, architecture knowledge, and instructions that Claude remembers across sessions |
| **Context Management** | Injected as **user context** at conversation start. Adds to Claude's knowledge but doesn't modify system prompt |
| **Lifecycle Stage** | **Session start** - loaded once when session begins, persists throughout |
| **Activation** | Automatic. Discovered in project root or `.claude/` directory |

**Key Insight**: CLAUDE.md is "what Claude knows about this project" - it's additive context that informs decisions without changing Claude's fundamental behavior.

**Documentation**: [claude-md.md](claude-md.md)

---

### 3. Rules (`.claude/rules/`)

| Aspect | Details |
|--------|---------|
| **Objective** | Provide modular, file-type-specific coding standards and guidelines. Organize instructions by topic instead of one monolithic file |
| **Context Management** | Loaded as **user context** like CLAUDE.md, but can be **path-filtered** via frontmatter globs. Only relevant rules load for current file context |
| **Lifecycle Stage** | **Session start + context-aware** - all rules load at start, path-specific rules filter based on active files |
| **Activation** | **Deterministic** — always present when session starts (unlike skills which are probabilistic) |

**Key Insight**: Rules are "conditional CLAUDE.md" - they let you say "when working on `*.sol` files, follow these Solidity conventions" without cluttering context for other file types.

**Important**: Rules are suggestions the LLM weighs against other context. For enforcement, use hooks.

**Documentation**: [rules.md](rules.md)

---

### 4. Commands (`.claude/commands/`)

| Aspect | Details |
|--------|---------|
| **Objective** | Create reusable prompt templates that users invoke explicitly. Standardize common workflows |
| **Context Management** | Command content becomes the **user prompt** when invoked. Supports dynamic injection via `$ARGUMENTS`, `!`backticks (bash), and `@` file references |
| **Lifecycle Stage** | **On-demand** - only executes when user explicitly invokes `/command-name` |
| **Activation** | Explicit via `/command-name` or selecting from `/help` menu |

**Key Insight**: Commands are "stored prompts with superpowers" - they're user-triggered shortcuts that can pull in dynamic context (git status, file contents) at invocation time.

**Documentation**: [commands.md](commands.md)

---

### 5. Skills (`.claude/skills/`)

| Aspect | Details |
|--------|---------|
| **Objective** | Define complex, multi-file capabilities that Claude can auto-discover and invoke when relevant. More powerful than commands |
| **Context Management** | Skill instructions load into context when invoked. Can run in **forked context** (`context: fork`) to isolate from main conversation. Supports progressive disclosure via linked files |
| **Lifecycle Stage** | **Auto-discovery + on-demand** - Claude can suggest skills based on task matching, or user invokes explicitly |
| **Activation** | **Soft** (probabilistic via description matching) OR **Strong** (explicit `/skill-name`). See activation model below |

**Key Insight**: Skills are "intelligent capabilities" - unlike commands which are just prompt templates, skills can be auto-suggested, run isolated, and contain supporting files for complex workflows.

**Activation Types**:
- **Soft**: Claude *could* auto-invoke via description matching (probabilistic)
- **Strong**: Explicitly referenced in agent .md or called by user (deterministic)

**Documentation**: [skills.md](skills.md)

---

### 6. Agents (`.claude/agents/`)

| Aspect | Details |
|--------|---------|
| **Objective** | Create specialized AI personas with restricted tools, custom models, and focused expertise. Delegate specific task types to purpose-built assistants |
| **Context Management** | Agents run in **isolated context** - they don't see prior conversation and their output is summarized back. Each agent has its own system prompt (the file content) |
| **Lifecycle Stage** | **On-demand delegation** - Claude spawns agents when task matches their description, or user requests explicitly |
| **Activation** | Automatic (Claude delegates matching tasks) OR explicit ("use the code-reviewer agent"). Description drives auto-delegation |

**Key Insight**: Agents are "isolated specialists" - they run in separate contexts with their own tool restrictions, preventing context pollution and enabling parallel execution of independent tasks.

**Documentation**: [agents.md](agents.md)

---

### 7. Hooks (`settings.json` → `hooks`)

| Aspect | Details |
|--------|---------|
| **Objective** | Execute scripts at specific lifecycle events. Enable validation, automation, logging, and custom integrations |
| **Context Management** | Hooks don't modify Claude's context directly. They intercept tool calls and can **block, modify, or log** operations. PostToolUse hooks can trigger side effects (formatting, notifications) |
| **Lifecycle Stage** | **Per-tool-call** - fires before (PreToolUse) or after (PostToolUse) each tool invocation, plus session events |
| **Activation** | Automatic based on matcher patterns. Fires on every matching tool call |

**Key Insight**: Hooks are "middleware for tool calls" - they sit between Claude's intent and execution, enabling validation ("block dangerous commands") and automation ("format after every edit").

**Hook Events**:
| Event | When | Use Case |
|-------|------|----------|
| `SessionStart` | Session begins | Environment setup |
| `PreToolUse` | Before tool executes | Validation, blocking |
| `PostToolUse` | After tool executes | Formatting, logging |
| `Notification` | Claude needs attention | Custom alerts |
| `Stop` | Response complete | Cleanup, reporting |
| `SessionEnd` | Session ends | Final cleanup |

**Documentation**: [hooks.md](hooks.md)

---

### 8. MCP Servers (`.mcp.json`)

| Aspect | Details |
|--------|---------|
| **Objective** | Connect Claude to external services (databases, APIs, tools) via Model Context Protocol. Extend Claude's capabilities beyond local files |
| **Context Management** | MCP servers provide **additional tools** Claude can use. They don't add to conversation context but expand what actions are available |
| **Lifecycle Stage** | **Session start** - servers connect when session begins, remain available throughout |
| **Activation** | Automatic connection on session start. Claude uses MCP tools when relevant to task |

**Key Insight**: MCP is "Claude's plugin system for external world" - it's how Claude talks to databases, APIs, and services that aren't local files.

**Documentation**: [mcp.md](mcp.md)

---

### 9. Output Styles (`.claude/output-styles/`)

| Aspect | Details |
|--------|---------|
| **Objective** | Fundamentally change Claude's behavior by replacing its system prompt. Adapt Claude for non-engineering tasks (technical writing, research, tutoring) |
| **Context Management** | **Replaces system prompt** - this is the most invasive context change. By default removes all coding instructions (`keep-coding-instructions: false`) |
| **Lifecycle Stage** | **Session-wide after activation** - once activated, affects all subsequent interactions |
| **Activation** | Explicit via `/output-style name` or setting `outputStyle` in settings |

**Key Insight**: Output styles are "personality replacement" - unlike everything else which adds context, output styles *replace* Claude's core instructions. Use when you need Claude to be fundamentally different (researcher, teacher, auditor).

**Documentation**: [output-styles.md](output-styles.md)

---

### 10. Plan Mode (`plansDirectory`)

| Aspect | Details |
|--------|---------|
| **Objective** | Enable safe, read-only code analysis and planning before making changes. Think through complex problems without risk |
| **Context Management** | Restricts Claude to **read-only tools** (Read, Glob, Grep). Blocks all modification tools (Edit, Write, Bash). Encourages `AskUserQuestion` for clarification |
| **Lifecycle Stage** | **Permission mode** - can be active for entire session or toggled mid-session |
| **Activation** | `--permission-mode plan` flag, `Shift+Tab` toggle, or `defaultMode: "plan"` in settings |

**Key Insight**: Plan Mode is "analysis sandbox" - it's not about adding context but about *restricting actions*. Claude can explore freely knowing it can't accidentally break anything.

**Documentation**: [plan-mode.md](plan-mode.md)

---

## Context Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SESSION START                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │  settings   │    │   Output    │    │    MCP      │              │
│  │   .json     │    │   Style     │    │  Servers    │              │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘              │
│         │                  │                  │                      │
│         ▼                  ▼                  ▼                      │
│  ┌─────────────────────────────────────────────────────┐            │
│  │              SYSTEM PROMPT LAYER                     │            │
│  │  • Permissions (what Claude can do)                  │            │
│  │  • Output style (how Claude behaves)                 │            │
│  │  • Available tools (MCP + built-in)                  │            │
│  └─────────────────────────────────────────────────────┘            │
│                           │                                          │
│         ┌─────────────────┼─────────────────┐                       │
│         ▼                 ▼                 ▼                        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │
│  │  CLAUDE.md  │   │   Rules     │   │   Skills    │               │
│  │  (memory)   │   │  (filtered) │   │ (discovered)│               │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘               │
│         │                 │                 │                        │
│         ▼                 ▼                 ▼                        │
│  ┌─────────────────────────────────────────────────────┐            │
│  │              USER CONTEXT LAYER                      │            │
│  │  • Project knowledge (CLAUDE.md)                     │            │
│  │  • Coding standards (rules, path-filtered)           │            │
│  │  • Available capabilities (skills)                   │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CONVERSATION RUNTIME                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Prompt ──► [Commands expand] ──► Claude Processing            │
│                                              │                       │
│                                              ▼                       │
│                                    ┌─────────────────┐              │
│                                    │   Tool Call     │              │
│                                    └────────┬────────┘              │
│                                             │                        │
│                    ┌────────────────────────┼────────────────────┐  │
│                    ▼                        ▼                    ▼  │
│             ┌───────────┐           ┌───────────┐         ┌────────┐│
│             │ PreToolUse│           │  Execute  │         │ Agents ││
│             │   Hooks   │──block?──►│   Tool    │──spawn─►│(isolated)│
│             └───────────┘           └─────┬─────┘         └────────┘│
│                                           │                         │
│                                           ▼                         │
│                                    ┌───────────┐                    │
│                                    │PostToolUse│                    │
│                                    │   Hooks   │                    │
│                                    └───────────┘                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Master Comparison Chart

| Feature | What It Does | Context Impact | When It Loads | How It Activates | Can Auto-Trigger? |
|---------|--------------|----------------|---------------|------------------|-------------------|
| **Settings** | Permissions, tool access, environment config | None (config only) | Pre-session | Automatic | Always on |
| **CLAUDE.md** | Project knowledge, architecture, instructions | Adds to conversation | Session start | Automatic | Always on |
| **Rules** | Coding standards, can scope by file path via `paths:` frontmatter | Adds to conversation | Session start | Automatic | Always on |
| **Commands** | Reusable prompt templates with dynamic injection | Becomes your prompt | On invoke | `/command-name` | No |
| **Skills** | Complex multi-file capabilities | Adds to conversation (unless run isolated - see below) | On invoke/suggest | `/skill` or auto-suggested | Yes (by description match) |
| **Agents** | Isolated specialist personas with tool restrictions | **Isolated**: fresh conversation, doesn't see your chat, returns summary | On delegation | Auto-delegated or explicit | Yes (by description match) |
| **Hooks** | Scripts that intercept tool calls | None (side effects only) | Per tool call | Automatic (matcher-based) | Always on |
| **MCP** | External service connections (DBs, APIs) | Adds tools (no knowledge) | Session start | Automatic | Always on |
| **Output Styles** | Replace system prompt entirely | 🔴 Replaces system prompt | After activation | `/output-style name` | No |
| **Plan Mode** | Read-only analysis, blocks modifications | Restricts tools | On toggle | `Shift+Tab` or `--permission-mode plan` | No |

### What "Isolated" Means (Agents & Skills)

**Isolated = runs in a separate subprocess with fresh empty context**

- Doesn't see your conversation history
- Has its own private conversation
- Does its work, then returns only the final summary to you
- Like saying: "go figure this out in another room, come back with the answer"

**Skills can optionally run isolated** by setting `context: fork` in frontmatter. When they do, you also specify which agent type runs it (`agent: code-reviewer`).

### Skills ↔ Agents Relationship

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   SKILLS                              AGENTS                │
│   ┌─────────┐                         ┌─────────┐           │
│   │         │                         │         │           │
│   │  Skill  │──"run me isolated"────► │  Agent  │           │
│   │         │   (context: fork)       │  runs   │           │
│   │         │   (agent: X)            │  skill  │           │
│   │         │                         │         │           │
│   │         │ ◄──"load these skills"──│         │           │
│   │         │    (skills: X, Y)       │         │           │
│   └─────────┘                         └─────────┘           │
│                                                             │
│   • Skills CANNOT spawn agents                              │
│   • Skills CAN request to run inside an agent (isolated)    │
│   • Agents CAN load skills into their own context           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Skills vs Agents - Actual Differences

| | Skills | Agents |
|---|--------|--------|
| **Default behavior** | Runs in your conversation | Runs isolated |
| **Can run isolated?** | Only if you set `context: fork` | Always isolated |
| **Has tool restrictions?** | No (uses main Claude's tools) | Yes (`tools:` / `disallowedTools:`) |
| **Has model override?** | Yes | Yes |
| **File structure** | Directory with `SKILL.md` + supporting files | Single `.md` file |
| **Mental model** | "Instructions on how to do X" | "A specialist persona to delegate to" |

**The confusing part:** When a Skill sets `context: fork` + `agent: X`, it's basically just running in an agent. The Skill becomes instructions loaded into that agent.

**The real distinction:**
- **Skill (no fork)** = instructions added to YOUR conversation. Claude learns how to do something.
- **Skill (with fork)** = instructions sent to a separate agent. Basically becomes an agent task.
- **Agent** = always a separate specialist that doesn't pollute your main context.

**When to use which:**
- Want isolation + tool restrictions → **Agent**
- Want instructions in your conversation → **Skill** (no fork)
- Want complex multi-file capability that runs isolated → **Skill** (with fork) + **Agent**


### Agents vs Rules vs Skills

#### Purpose & Propagation

| Concept | Purpose | Propagation |
|---------|---------|-------------|
| **Rules** | Shared conventions, style guides, format requirements | Can propagate across agents |
| **Skills** | On-demand procedures, task-specific workflows | Shared across agents (loaded when needed) |
| **Agent Prompts** | Individual agent's specific role and capabilities | Agent-specific, don't propagate |

#### Activation Model

| Aspect | Rules | Skills | Agents |
|--------|-------|--------|--------|
| **Loading** | Always in context | On-demand (lazy) | On delegation |
| **Activation** | Deterministic | Probabilistic (soft) or Explicit (strong) | Task-matching or explicit |
| **Context cost** | Always paid | Only when invoked | Isolated (own context) |
| **Trigger** | Automatic | Description match OR `/skill` | Claude delegates OR user requests |

#### Activation Types for Skills

| Type | Description | Example |
|------|-------------|---------|
| **Soft** | Claude *could* auto-invoke via description matching | Task mentions "deploy" → deploy skill suggested |
| **Strong** | Explicitly referenced in agent .md or called by user | `/deploy` or agent prompt says "use deploy skill" |
| **Where** | Location where the skill is defined | `skills/deploy/SKILL.md` |

#### Key Insight

> **Rules are suggestions. Hooks are enforcement.**
>
> A rule saying "don't edit .env" is parsed by Claude and *maybe* followed.
> A PreToolUse hook blocking .env edits *always* runs and blocks the operation.

#### References

- [User-Level Agent Rules Feature Request](https://github.com/anthropics/claude-code/issues/8395) — Discusses rule propagation to subagents
- [Official Skill Creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) — SKILL.md format and activation
- [Bug: Claude ignores CLAUDE.md rules](https://github.com/anthropics/claude-code/issues/19635) — Rules are suggestions, not enforcement
- [Skills Activation Discussion](https://github.com/orgs/community/discussions/182117) — Deterministic vs probabilistic retrieval

---

## What Affects What

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    CLAUDE'S BRAIN                            │
                    ├─────────────────────────────────────────────────────────────┤
                    │                                                              │
  REPLACES ───────► │  ┌─────────────────────────────────────────────────────┐   │
  Output Styles     │  │            SYSTEM PROMPT                             │   │
                    │  │  (Claude's core personality & instructions)          │   │
                    │  └─────────────────────────────────────────────────────┘   │
                    │                          │                                  │
                    │                          ▼                                  │
  ADDS TO ────────► │  ┌─────────────────────────────────────────────────────┐   │
  CLAUDE.md         │  │            USER CONTEXT                              │   │
  Rules             │  │  (What Claude knows about your project)              │   │
  Skills (on invoke)│  └─────────────────────────────────────────────────────┘   │
  Commands (expand) │                          │                                  │
                    │                          ▼                                  │
  CONFIGURES ─────► │  ┌─────────────────────────────────────────────────────┐   │
  Settings          │  │            AVAILABLE TOOLS                           │   │
  MCP               │  │  (What Claude can do - Read, Edit, Bash, etc.)       │   │
  Plan Mode         │  └─────────────────────────────────────────────────────┘   │
                    │                          │                                  │
                    │                          ▼                                  │
  INTERCEPTS ─────► │  ┌─────────────────────────────────────────────────────┐   │
  Hooks             │  │            TOOL EXECUTION                            │   │
                    │  │  (Block, modify, or react to tool calls)             │   │
                    │  └─────────────────────────────────────────────────────┘   │
                    │                                                              │
                    └─────────────────────────────────────────────────────────────┘
                                               │
                                               │ Can delegate to
                                               ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                 ISOLATED AGENTS                              │
                    ├─────────────────────────────────────────────────────────────┤
                    │  • Fresh context (doesn't see main conversation)            │
                    │  • Own tool restrictions                                     │
                    │  • Can load Skills into their context                        │
                    │  • Returns summary to main conversation                      │
                    │  • Skills with context:fork run here                         │
                    └─────────────────────────────────────────────────────────────┘
```

---

## Lifecycle Timeline

```
SESSION START                    CONVERSATION                         SESSION END
     │                                │                                    │
     ▼                                ▼                                    ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│Settings │  │CLAUDE.md│  │  User   │  │ Claude  │  │  Tool   │  │ Session │
│ loaded  │─►│ Rules   │─►│ types   │─►│ thinks  │─►│executes │─►│  ends   │
│         │  │ MCP     │  │ prompt  │  │         │  │         │  │         │
│         │  │Out.Style│  │         │  │         │  │         │  │         │
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘
                              │              │            │
                              ▼              ▼            ▼
                         ┌─────────┐   ┌─────────┐  ┌─────────┐
                         │Commands │   │ Skills  │  │ Hooks   │
                         │ expand  │   │ suggest │  │ fire    │
                         │ here    │   │ Agents  │  │ Pre/Post│
                         └─────────┘   │ spawn   │  └─────────┘
                                       └─────────┘
```

---

## Quick Reference by Use Case

| I want to... | Use | Why |
|--------------|-----|-----|
| Give Claude project context | CLAUDE.md | Persistent knowledge across sessions |
| Enforce coding standards | Rules | Path-filtered, modular, organized |
| Make a quick prompt shortcut | Commands | Simple, explicit, supports `$ARGUMENTS` |
| Build complex reusable capability | Skills | Multi-file, auto-discoverable, can fork |
| Delegate to a specialist | Agents | Isolated context, restricted tools, parallel |
| Auto-format after edits | Hooks (PostToolUse) | Runs after every matching tool |
| Block dangerous commands | Hooks (PreToolUse) | Intercepts before execution |
| Connect to a database | MCP | Adds DB tools to Claude |
| Make Claude a technical writer | Output Styles | Replaces entire personality |
| Explore code safely | Plan Mode | Blocks all write operations |
| Restrict tool access | Settings → permissions | Foundational config |

---

## Documentation Files

| File | Description |
|------|-------------|
| [settings.md](settings.md) | Configuration options for `settings.json` |
| [claude-md.md](claude-md.md) | Memory files for project context |
| [rules.md](rules.md) | Modular instruction files |
| [commands.md](commands.md) | Custom slash commands |
| [skills.md](skills.md) | Reusable capabilities |
| [agents.md](agents.md) | Custom subagents |
| [hooks.md](hooks.md) | Event hooks for automation |
| [mcp.md](mcp.md) | MCP server configuration |
| [output-styles.md](output-styles.md) | Custom output styles |
| [plan-mode.md](plan-mode.md) | Plan Mode configuration |

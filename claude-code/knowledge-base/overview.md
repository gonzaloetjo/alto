# Claude Code > Overview

> Architecture, context flow, and lifecycle of Claude Code's extensibility system.

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

## Session Lifecycle

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

## Feature Loading Order

### Memory Files
1. `~/.claude/CLAUDE.md` (user global)
2. `~/.claude/rules/*` (user rules)
3. `./CLAUDE.md` or `./.claude/CLAUDE.md` (project)
4. `./.claude/rules/*` (project rules)
5. `./CLAUDE.local.md` (personal project)

### Settings Precedence
1. **Managed** (IT deployed) - highest priority
2. **CLI flags** (current session)
3. `.claude/settings.local.json` (personal project)
4. `.claude/settings.json` (team project)
5. `~/.claude/settings.json` (user global) - lowest priority

Arrays merge (combine), objects deep-merge, primitives use highest priority.

---

## Isolated Execution

### What "Isolated" Means

Isolated = runs in a separate subprocess with fresh empty context.

| Aspect | Main Context | Isolated Context |
|--------|--------------|------------------|
| Sees conversation history | Yes | No |
| Shares context pollution | Yes | No |
| Tool restrictions | From settings | From agent definition |
| Returns | N/A | Summary only |

### Skills ↔ Agents Relationship

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   SKILLS                              AGENTS                │
│   ┌─────────┐                         ┌─────────┐           │
│   │         │──"run me isolated"────► │  Agent  │           │
│   │  Skill  │   (context: fork)       │  runs   │           │
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

---

## Feature Comparison Summary

| Feature | Default Behavior | Can Run Isolated? | Has Tool Restrictions? |
|---------|-----------------|-------------------|------------------------|
| Rules | In your context | No | No |
| Commands | In your context | Only with `context: fork` | Yes (`allowed-tools`) |
| Skills | In your context | Yes (`context: fork`) | Yes (`allowed-tools`) |
| Agents | Always isolated | Always | Yes (`tools`/`disallowedTools`) |

---

## Related

- [index.md](index.md) - Feature matrix and navigation
- [quick-reference.md](quick-reference.md) - Single-page cheat sheet

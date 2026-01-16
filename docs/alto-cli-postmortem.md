# Alto-CLI SDK Wrapper: Postmortem

**Branch:** `alto-cli-abandoned`
**Date:** 2026-01-16
**Status:** Abandoned

## Goal

Build a TypeScript CLI wrapper using `@anthropic-ai/claude-agent-sdk` to enable instant mode switching without manual `/resume` commands or shell restarts.

**Desired UX:**
```
[SETUP] > /switch build
Switching to build mode...
[BUILD] >
```

## What Was Built

A full TypeScript package (`alto-cli/`) with:

- `src/index.ts` - CLI entry point using commander
- `src/alto.ts` - Main Alto class orchestrating SDK calls
- `src/config/agents.ts` - Agent .md file parser
- `src/config/loader.ts` - Config loading from runs/
- `src/config/hooks.ts` - Hook definitions (not spawning, just config)
- `src/session/manager.ts` - Per-mode session persistence
- `src/repl/input.ts` - AsyncIterable for user input with /switch handling
- `src/repl/output.ts` - ANSI colored output

## Why It Failed

### 1. System Prompt Append Doesn't Work

The SDK's `systemPrompt: { type: "preset", preset: "claude_code", append: content }` doesn't make Claude follow the appended instructions reliably.

**Evidence:**
- Switched to dev mode, header showed "ALTO DEV"
- Claude responded with setup mode content ("Welcome to ALTO!")
- Even after fixing mode loading, Claude ignored mode-specific instructions

**Root cause:** Claude Code's preset system prompt is strong. Appended content is treated as supplementary, not overriding.

### 2. AskUserQuestion Tool Not Invoked

Despite explicit instructions like "Invoke the `AskUserQuestion` tool (NOT plain text)", Claude outputted plain text options instead of using the tool.

**Evidence:**
```
Would you like to:
1. **Approve the command** so I can show open issues
2. **Tell me an issue number** you'd like to work on
```

This is plain text, not the interactive UI that AskUserQuestion provides.

### 3. Expensive

Simple interactions cost $0.17-$0.30 due to multiple turns. The SDK approach adds overhead compared to native `claude` command.

### 4. Session Architecture Mismatch

Claude Code sessions are stateful. You cannot change the system prompt mid-session. The goal of "instant switching without restart" is architecturally impossible with current SDK.

**Reality:** Mode switching will always require starting a new Claude session. The question is just how to make that transition smoother.

## Lessons Learned

1. **SDK preset+append is weak** - For mode-specific behavior, you'd need a fully custom system prompt, losing Claude Code features.

2. **AskUserQuestion invocation is probabilistic** - Even with explicit instructions, Claude may choose plain text. This isn't controllable via system prompt.

3. **The original shell approach was fine** - `alto-switch build` + `/exit` + `claude` is not that bad. The friction was overstated.

4. **Test early, test often** - Should have tested SDK behavior with a minimal example before building full infrastructure.

## Useful Artifacts to Keep

These changes from the attempt are worth preserving:

### 1. `alto-nuke` script
Full reset of ALTO state. Essential for testing and recovery.
```bash
rm -rf .claude/ runs/ CLAUDE.md objective.md
direnv reload
```

### 2. `scripts/alto-init-test.sh`
Standalone script to create test projects pointing to local ALTO.
```bash
./scripts/alto-init-test.sh ../my-test-project
```

### 3. `alto-init-test` devenv wrapper
Devenv script that calls the standalone script.

### 4. `alto-switch` orchestrator.json update
Make `alto-switch` also update `runs/orchestrator.json` so any future tooling can read the mode without parsing devenv.nix.

## Not Worth Keeping

- `alto` CLI script (references non-working alto-cli)
- `alto-cli/` directory (the whole SDK wrapper)
- Template changes about "NOT plain text" (doesn't help)
- nodejs_20 in packages (not needed without alto-cli)
- Changes to copy ALL templates/skills (was for runtime loading)

## Future Directions: Alternative Approaches

### Constraints (from research)

Before evaluating options, key constraints:

- **Skills/hooks cannot invoke /exit or /resume** - These are user-typed CLI commands
- **Session restart requires user action** - Architectural limit of Claude Code
- **Hooks can detect resumption** - `SessionStart` receives `{resume: true/false}`
- **Session naming works** - `/rename build` enables `/resume build`

---

### Option 1: Improved Skill + Named Sessions (Simplest)

**Concept:** Enhance the existing `/alto-switch` skill to be more seamless.

**Implementation:**
1. On first run per mode, skill tells user: "Run `/rename setup` to enable quick switching"
2. `alto-switch` updates config AND outputs exact command to type
3. User types `/resume build` (2 keystrokes after `/res` tab-complete)

**Flow:**
```
[SETUP] > /alto-switch build
Switching to build mode...
Type: /resume build

[SETUP] > /resume build
Resuming session 'build'...

[BUILD] >
```

**Pros:**
- Zero new infrastructure
- Works today with current Claude Code
- Named sessions persist conversation history
- Fast after initial setup (tab-complete)

**Cons:**
- Still requires user to type /resume (can't automate)
- User must remember to /rename each mode initially
- Two commands instead of one

**Effort:** Low (enhance existing skill)

**Verdict:** ⭐ Best option for minimal friction with zero infrastructure.

---

### Option 2: Folder-Based Isolation

**Concept:** Three sibling directories, each a complete environment.

**Structure:**
```
project/
├── setup/          # Human-interactive mode
│   ├── devenv.nix  # alto.orchestrator = "setup"
│   ├── .claude/
│   └── (symlinks to shared code)
├── build/          # Autonomous execution mode
│   ├── devenv.nix  # alto.orchestrator = "build"
│   ├── .claude/
│   └── (symlinks to shared code)
├── dev/            # ALTO development mode
│   ├── devenv.nix  # alto.orchestrator = "dev"
│   ├── .claude/
│   └── (symlinks to shared code)
└── src/            # Actual source code (shared)
```

**Flow:**
```bash
cd ../build && claude   # Switch to build mode
cd ../setup && claude   # Switch to setup mode
```

**Pros:**
- Complete isolation (no state confusion)
- Each mode has its own session history
- Can run multiple modes simultaneously (different terminals)
- Clear mental model

**Cons:**
- File duplication or symlink management
- `cd` disrupts workflow
- Three separate devenv shells to manage
- Harder to keep configs in sync
- Git messier (what's the "main" directory?)

**Effort:** Medium (create structure, manage symlinks, modify ALTO deployment)

**Verdict:** Viable for users who want complete isolation, but adds complexity.

---

### Option 3: Docker Containers

**Concept:** Each mode runs in its own container with isolated Claude instance.

**Implementation:**
```yaml
# docker-compose.yml
services:
  setup:
    image: alto-claude
    volumes:
      - ./src:/workspace/src
    environment:
      - ALTO_MODE=setup

  build:
    image: alto-claude
    volumes:
      - ./src:/workspace/src
    environment:
      - ALTO_MODE=build
```

**Flow:**
```bash
docker compose exec setup claude   # Run in setup container
docker compose exec build claude   # Run in build container
```

**Pros:**
- Complete isolation
- Reproducible environments
- Can snapshot/restore states
- Could run headless for CI

**Cons:**
- **Streaming/interaction is problematic** - Claude's interactive REPL doesn't work well through docker exec
- Container overhead (startup time, resources)
- Volume mounting complexity
- API key management in containers
- devenv in Docker is complex

**Effort:** High (Dockerfile, compose config, streaming workarounds)

**Verdict:** Not recommended. Docker's TTY handling makes interactive Claude painful.

---

### Option 4: Tmux Multi-Session

**Concept:** Pre-create tmux windows/panes for each mode, switch with keybindings.

**Implementation:**
```bash
# alto-tmux-setup (run once)
tmux new-session -d -s alto -n setup
tmux new-window -t alto -n build
tmux new-window -t alto -n dev

# In each window, start devenv shell with appropriate mode
tmux send-keys -t alto:setup 'cd project && devenv shell' Enter
tmux send-keys -t alto:build 'cd project && ALTO_MODE=build devenv shell' Enter
# etc.
```

**Switching:**
```
Ctrl-b 1   # Switch to setup (window 1)
Ctrl-b 2   # Switch to build (window 2)
Ctrl-b 3   # Switch to dev (window 3)
```

**Pros:**
- Instant switching (single keystroke after Ctrl-b)
- All sessions persist
- Can see output from multiple modes
- Standard tmux workflow many devs know

**Cons:**
- Requires tmux knowledge
- Three concurrent Claude sessions = 3x API usage if all active
- Setup script needed
- Each window needs its own devenv shell initialization
- Still need mechanism to set mode per window

**Effort:** Medium (tmux setup script, mode-per-window config)

**Verdict:** Good for tmux users. The instant switching is genuinely fast, but requires buying into tmux workflow.

---

### Option 5: Shell Wrapper Function (Recommended)

**Concept:** A shell function `c` or `alto` that reads mode and handles session management.

**Implementation:**
```bash
# In .zshrc or devenv shell
alto() {
  local mode=$(cat runs/orchestrator.json 2>/dev/null | jq -r '.orchestrator // "setup"')
  local session_file="runs/sessions/${mode}.json"

  if [[ -f "$session_file" ]]; then
    local session_id=$(jq -r '.id' "$session_file")
    echo "Resuming $mode session..."
    claude --resume "$session_id" "$@"
  else
    echo "Starting new $mode session..."
    claude "$@"
  fi
}

# Mode switch
switch() {
  alto-switch "$1"
  echo "Now run: alto"
}
```

**Flow:**
```bash
switch build    # Updates config
alto            # Auto-resumes correct session

switch setup    # Updates config
alto            # Auto-resumes setup session
```

**Pros:**
- Single command after switch
- Auto-resumes correct session per mode
- Works with existing Claude Code
- No new dependencies
- Can add features incrementally

**Cons:**
- Requires session ID capture (hook modification)
- Still two commands (switch + alto)
- Shell function needs to be in user's shell config

**Effort:** Low-Medium (modify SessionStart hook to save ID, add shell function)

**Verdict:** ⭐⭐ Best balance of UX improvement vs complexity. Builds on existing infrastructure.

---

## Recommendation

**Start with Option 1** (improved skill + named sessions):
- Zero new code
- Works today
- Just needs better messaging in `/alto-switch` skill

**Then consider Option 5** (shell wrapper) if:
- Users find `/resume mode` too friction-y
- We want single-command mode switch
- Worth the hook modification effort

**Skip Options 2-4** unless:
- Option 2: User specifically wants folder isolation
- Option 3: Need CI/headless (but streaming issues)
- Option 4: User is already a tmux power user

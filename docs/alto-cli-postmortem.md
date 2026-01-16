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

## Future Directions

If we want better mode switching UX in the future:

1. **Accept the restart** - Mode switch = new session. Make the restart fast and seamless.

2. **Named sessions** - Each mode gets its own named session. `/resume setup` vs `/resume build`.

3. **Session state file** - On mode switch, save session ID to a file. New claude invocation auto-resumes.

4. **Wrapper shell function** - A shell function `alto` that handles mode detection and calls `claude` with right args.

None of these require the SDK wrapper approach.

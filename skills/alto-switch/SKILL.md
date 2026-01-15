---
name: alto-switch
type: technique
triggers:
  - when switching orchestrator modes
  - when user requests dev/build/setup mode
---

# Mode Switching

ALTO has three orchestrator modes: `setup`, `build`, `dev`.

## Process

1. `Edit(devenv.nix)` - find `alto.orchestrator = "X"` and change `"X"` to desired mode
2. `Bash(alto-restart)` to apply

If `alto-restart` not found, tell user to run `devenv shell` to reload.

## Quick Reference

| From | To | When |
|------|----|------|
| setup | build | objective.md ready, start autonomous execution |
| build | setup | Feature complete, define next feature |
| any | dev | Developing ALTO itself |

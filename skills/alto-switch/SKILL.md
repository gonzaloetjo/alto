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
2. Tell user: "Mode updated. Please exit and run `devenv shell` then `claude` to apply."

Claude cannot restart itself. User must exit and re-enter.

## Quick Reference

| From | To | When |
|------|----|------|
| setup | build | objective.md ready, start autonomous execution |
| build | setup | Feature complete, define next feature |
| any | dev | Developing ALTO itself |

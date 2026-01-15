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

Run `Bash(alto-switch <mode>)` where `<mode>` is `setup`, `build`, or `dev`.

This command:
1. Updates `alto.orchestrator` in devenv.nix
2. Runs `alto-restart` to apply

## Quick Reference

| From | To | When |
|------|----|------|
| setup | build | objective.md ready, start autonomous execution |
| build | setup | Feature complete, define next feature |
| any | dev | Developing ALTO itself |

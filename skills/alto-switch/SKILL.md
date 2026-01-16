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

Run the switch command:

```bash
alto-switch <mode>
```

Where `<mode>` is one of: `setup`, `build`, `dev`

The script updates devenv.nix and triggers a restart automatically.

## Quick Reference

| From | To | When |
|------|------|------|
| setup | build | objective.md ready, start autonomous execution |
| build | setup | Feature complete, define next feature |
| any | dev | Developing ALTO itself |

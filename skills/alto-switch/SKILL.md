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

1. `Edit(devenv.nix)` - add or update `alto.orchestrator = "X";` (where X is `setup`, `build`, or `dev`). Do NOT use `lib.mkDefault`.

2. Run this to trigger restart:
```bash
touch /tmp/alto-restart-requested
echo "Switching mode. Restarting Claude..."
kill -TERM $(ps -o ppid= -p $$ | tr -d ' ')
```

This kills Claude. The wrapper function detects the restart file and restarts Claude with fresh config.

## Quick Reference

| From | To | When |
|------|------|------|
| setup | build | objective.md ready, start autonomous execution |
| build | setup | Feature complete, define next feature |
| any | dev | Developing ALTO itself |

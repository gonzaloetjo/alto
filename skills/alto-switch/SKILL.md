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

2. Run this restart command:
```bash
CLAUDE_PID=$(ps -o ppid= -p $$ | tr -d ' ')
nohup sh -c "
  sleep 0.5
  kill $CLAUDE_PID 2>/dev/null
  sleep 0.2
  cd '$PWD'
  exec devenv shell claude -- --continue
" > /tmp/alto-restart.log 2>&1 &
sleep 0.1
echo "Restarting..."
```

This kills the current Claude and restarts with new config.

## Quick Reference

| From | To | When |
|------|------|------|
| setup | build | objective.md ready, start autonomous execution |
| build | setup | Feature complete, define next feature |
| any | dev | Developing ALTO itself |

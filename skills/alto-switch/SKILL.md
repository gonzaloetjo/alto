---
name: alto-switch
type: technique
triggers:
  - when switching orchestrator modes
  - when user requests dev/build/setup mode
---

# Mode Switching

## Steps

1. Run `alto-switch <mode>` to update devenv.nix
2. Tell user exactly what to type next:
   - If they have a named session: `/resume <mode>`
   - Otherwise: `/exit` then `claude`

## Example Response

After running `alto-switch dev`:
```
Switched to dev mode. Type one of:
  /resume dev     (if you have a session named "dev")
  /exit           (then run `claude` to start fresh)
```

## Naming Sessions (optional)

Users can name sessions with `/rename <mode>` to enable quick switching via `/resume`.

## Modes

| Mode | Purpose |
|------|---------|
| setup | Feature definition, configuration |
| build | Autonomous execution |
| dev | ALTO development |

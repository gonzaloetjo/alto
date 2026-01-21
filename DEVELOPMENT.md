# ALTO Development Guide

Guide for developing ALTO itself.

---

## Dev Mode

Dev mode provides a streamlined environment for ALTO development:

- Single `alto-dev` agent with full access
- `alto-dev-guide` skill with documentation URLs and patterns
- `writing-alto-skills` skill for skill authoring
- Minimal hooks (just `changelog-check`)

### Switching to Dev Mode

```bash
alto dev
```

If inside Claude: type `/exit` first, then run `alto dev`.

### What Dev Mode Provides

| Feature | Description |
|---------|-------------|
| `alto-dev` agent | Full tool access (Read, Write, Edit, Grep, Glob, Bash, WebFetch) |
| `alto-dev-guide` skill | Documentation URLs, patterns, architecture |
| `writing-alto-skills` skill | Skill authoring methodology |
| `changelog-check` hook | Ensures CHANGELOG.md updates |
| devenv MCP | Package search and config generation |

---

## Testing

### Test Layers

| Layer | Command | Purpose | Speed |
|-------|---------|---------|-------|
| Syntax | `alto-validate` | Nix/Python/Bash syntax, frontmatter | <5s |
| Unit | `pytest tests/` | Hook utilities, validators | ~10s |
| Protocol | `alto-test-multi --scenario X` | Multi-turn orchestrator flows | ~$0.08/turn |

### Quick Syntax Checks

```bash
devenv shell -- alto-validate

# Or manually:
nix-instantiate --parse devenv.nix > /dev/null && echo "OK"
python3 -m py_compile hooks/*.py && echo "OK"
```

### Unit Tests

```bash
pytest tests/ -v
```

### Protocol Testing (Multi-Turn)

```bash
# Run ALL scenarios
devenv shell -- alto-test-multi --all --verbose

# Single scenario
devenv shell -- alto-test-multi --scenario build-blocked-recovery --verbose

# Keep test directory for debugging
devenv shell -- alto-test-multi --scenario setup-new-project --keep --verbose
```

**Available Scenarios:** `setup-new-project`, `build-simple-feature`, `build-phase-transitions`, `build-handoff-structure`, `setup-configure-flow`, `build-blocked-recovery`

### Local Integration Test

Create a **separate directory** to test local changes:

```bash
mkdir -p /tmp/alto-test && cd /tmp/alto-test
git init

cat > devenv.yaml << 'EOF'
inputs:
  nixpkgs:
    url: github:cachix/devenv-nixpkgs/rolling
  alto:
    url: path:/path/to/your/alto
    flake: false
EOF

cat > devenv.nix << 'EOF'
{ pkgs, lib, inputs, ... }:
{
  imports = [ "${inputs.alto}/devenv.nix" ];
}
EOF

devenv shell -- alto-status
```

---

## Adding Agents

Agents live in `agents/<name>.md` with YAML frontmatter:

```yaml
---
name: alto-myagent
model: sonnet
tools:
  - Read
  - Grep
  - Glob
  - LS
  - Edit
permissionMode: acceptEdits
---

# Agent Name

## Purpose
What this agent does.

## Skills
- Read `skills/scope-discipline/SKILL.md` — only do what task asks

## Constraints
- Constraint 1
```

### Required Fields

| Field | Values | Description |
|-------|--------|-------------|
| `name` | string | Agent identifier |
| `model` | `opus`, `sonnet`, `haiku` | LLM model |
| `tools` | array | Available tools |
| `permissionMode` | `plan`, `acceptEdits`, `default` | Permission behavior |

---

## Adding Skills

Skills live in `skills/<name>/SKILL.md`:

```yaml
---
name: my-skill
description: Use when [conditions]. [What it does].
---

# Skill Name

## Process
1. Step one
2. Step two
```

### Skill Types

| Type | Purpose | Word Limit |
|------|---------|------------|
| `discipline` | Behavioral rules (Hard Rule, Warning Signs) | 300 |
| `technique` | How-to procedures | 500 |
| `reference` | Lookup information | 800 |

---

## Adding Hooks

Hooks live in `hooks/<name>.py`:

```python
#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import safe_hook, get_runs_dir

@safe_hook("my-hook")
def main():
    # Hook logic - errors logged to runs/errors.jsonl
    pass

if __name__ == "__main__":
    main()
```

### The safe_hook Decorator

- Errors logged to `runs/errors.jsonl`
- Exit 0 on error (doesn't crash Claude)
- User-friendly stderr message

### Hook Events

| Event | When | Use |
|-------|------|-----|
| `PostToolUse` | After tool completes | Validation, logging |
| `Stop` | Session ends | Usage tracking |
| `SubagentStop` | Agent completes | Handoff validation |
| `PreToolUse` | Before tool runs | Blocking |
| `SessionStart` | Session begins | Health checks |

---

## Changelog Requirements

Key files requiring CHANGELOG.md updates:

| File Pattern | Reason |
|--------------|--------|
| `agents/*.md` | Agent behavior |
| `hooks/*.py` | Hook logic |
| `skills/*/SKILL.md` | Skill updates |
| `templates/CLAUDE.md.*` | Orchestrator changes |

The `changelog-check` hook blocks commits without CHANGELOG updates.

---

## Debug Mode

Enable verbose event logging:

```nix
alto.debug = true;
```

Events logged to `runs/logs/events.jsonl`. Query with:

```bash
alto-logs              # Last 20 events
alto-logs --metrics    # Aggregated stats
```

---

## Architecture Reference

- **ARCHITECTURE.md** — High-level design model
- **AI-CONTEXT.md** — Full agent context (state machine, formats, flow)
- **OPERATIONS.md** — Commands, configuration, troubleshooting

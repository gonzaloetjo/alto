---
name: alto-self-fix
type: technique
triggers:
  - running /alto-self-fix
  - "solve issue through ALTO"
  - "use ALTO self-fix"
---

# ALTO Self-Fix Procedure

Procedural workflow for ALTO to fix itself via GitHub issues.

## Workflow

### 1. Get Issue

```bash
gh issue view <number> --repo gonzaloetjo/alto
```

Read and understand the issue requirements.

### 2. Create Branch

```bash
git checkout -b issue-<number>-<short-description>
```

### 3. Implement

Modify ALTO source files as needed:
- `devenv.nix` - Options, scripts, hooks config
- `agents/*.md` - Agent prompts
- `hooks/*.py` - Hook logic
- `skills/*/SKILL.md` - Skills
- `templates/CLAUDE.md.*` - Protocols

### 4. Validate

```bash
nix-instantiate --parse devenv.nix > /dev/null && echo "Nix OK"
python3 -m py_compile hooks/*.py && echo "Python OK"
```

### 5. Test (if behavior change)

```bash
alto-test-run --scenario <relevant> --keep --json
```

Skip for string/doc-only changes.

### 6. Update CHANGELOG

Add entry under `## [Unreleased]` with issue reference.

### 7. Commit

```bash
git add <files>
git commit -m "feat: description (#<issue>)"
```

### 8. Push & PR

```bash
git push -u origin issue-<number>-<description>
gh pr create --title "feat: description (#<number>)" --body "Closes #<number>"
```

## Notes

- Never commit to main directly
- `changelog-check` hook enforces CHANGELOG updates
- `alto-restart` is blocked in dev mode
- Changes apply next session

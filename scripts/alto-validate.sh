#!/usr/bin/env bash
# Quick validation script for ALTO development
# Runs fast static checks before committing
set -e

ALTO_SRC="${ALTO_SRC:-$(dirname "$(dirname "$0")")}"

# Colors (if terminal supports it)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

ERRORS=0
WARNINGS=0

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warn() {
    echo -e "  ${YELLOW}!${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

echo "ALTO Validation"
echo "==============="
echo ""

# 1. Nix syntax check
echo "Checking Nix syntax..."
if nix-instantiate --parse "$ALTO_SRC/devenv.nix" >/dev/null 2>&1; then
    check_pass "devenv.nix"
else
    check_fail "devenv.nix has syntax errors"
    nix-instantiate --parse "$ALTO_SRC/devenv.nix" 2>&1 | head -5
fi

# 2. Python syntax check
# Use -B to prevent writing .pyc files (fails on read-only Nix store)
echo ""
echo "Checking Python syntax..."
for pyfile in "$ALTO_SRC"/hooks/*.py; do
    if [ -f "$pyfile" ]; then
        basename=$(basename "$pyfile")
        if python3 -B -m py_compile "$pyfile" 2>/dev/null; then
            check_pass "$basename"
        else
            check_fail "$basename has syntax errors"
            python3 -B -m py_compile "$pyfile" 2>&1 | head -3
        fi
    fi
done

# Also check scripts/*.py if any exist
for pyfile in "$ALTO_SRC"/scripts/*.py; do
    if [ -f "$pyfile" ]; then
        basename=$(basename "$pyfile")
        if python3 -B -m py_compile "$pyfile" 2>/dev/null; then
            check_pass "$basename"
        else
            check_fail "$basename has syntax errors"
            python3 -B -m py_compile "$pyfile" 2>&1 | head -3
        fi
    fi
done

# 3. Bash syntax check
echo ""
echo "Checking Bash syntax..."
for shfile in "$ALTO_SRC"/scripts/*.sh; do
    if [ -f "$shfile" ]; then
        basename=$(basename "$shfile")
        if bash -n "$shfile" 2>/dev/null; then
            check_pass "$basename"
        else
            check_fail "$basename has syntax errors"
            bash -n "$shfile" 2>&1 | head -3
        fi
    fi
done

# 4. Agent frontmatter validation
echo ""
echo "Checking agent frontmatter..."
for agentfile in "$ALTO_SRC"/agents/*.md; do
    if [ -f "$agentfile" ]; then
        basename=$(basename "$agentfile")
        # Check for YAML frontmatter
        if head -1 "$agentfile" | grep -q "^---"; then
            # Check required fields (tools, model)
            frontmatter=$(sed -n '2,/^---$/p' "$agentfile" | head -n -1)
            has_tools=false
            has_model=false

            if echo "$frontmatter" | grep -q "^tools:"; then
                has_tools=true
            fi
            if echo "$frontmatter" | grep -q "^model:"; then
                has_model=true
            fi

            if $has_tools && $has_model; then
                check_pass "$basename"
            else
                missing=""
                $has_tools || missing="tools"
                $has_model || missing="${missing:+$missing, }model"
                check_fail "$basename missing: $missing"
            fi
        else
            check_fail "$basename missing YAML frontmatter"
        fi
    fi
done

# 5. Skill frontmatter validation
echo ""
echo "Checking skill frontmatter..."
if [ -x "$ALTO_SRC/scripts/validate-frontmatter.py" ]; then
    if python3 "$ALTO_SRC/scripts/validate-frontmatter.py" 2>&1; then
        check_pass "All skills validated"
    else
        check_fail "Skill validation failed"
    fi
else
    # Basic check if validate-frontmatter.py doesn't exist yet
    for skillfile in "$ALTO_SRC"/.claude/skills/*/SKILL.md "$ALTO_SRC"/skills/*/SKILL.md; do
        if [ -f "$skillfile" ]; then
            skillname=$(dirname "$skillfile" | xargs basename)
            if head -1 "$skillfile" | grep -q "^---"; then
                frontmatter=$(sed -n '2,/^---$/p' "$skillfile" | head -n -1)
                has_name=false
                has_type=false
                has_triggers=false

                if echo "$frontmatter" | grep -q "^name:"; then
                    has_name=true
                fi
                if echo "$frontmatter" | grep -q "^type:"; then
                    has_type=true
                fi
                if echo "$frontmatter" | grep -q "^triggers:"; then
                    has_triggers=true
                fi

                if $has_name && $has_type && $has_triggers; then
                    check_pass "$skillname"
                else
                    missing=""
                    $has_name || missing="name"
                    $has_type || missing="${missing:+$missing, }type"
                    $has_triggers || missing="${missing:+$missing, }triggers"
                    check_fail "$skillname missing: $missing"
                fi
            else
                check_fail "$skillname missing YAML frontmatter"
            fi
        fi
    done
fi

# Summary
echo ""
echo "==============="
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}FAILED${NC}: $ERRORS error(s), $WARNINGS warning(s)"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}PASSED${NC} with $WARNINGS warning(s)"
    exit 0
else
    echo -e "${GREEN}PASSED${NC}: All checks passed"
    exit 0
fi

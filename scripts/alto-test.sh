#!/usr/bin/env bash
# Run ALTO test suite
# Layer 1: Quick validation (alto-validate)
# Layer 2: pytest unit tests
set -e

ALTO_SRC="${ALTO_SRC:-$(dirname "$(dirname "$0")")}"

# Parse arguments
SKIP_VALIDATE=false
PYTEST_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-validate)
            SKIP_VALIDATE=true
            shift
            ;;
        --help|-h)
            echo "Usage: alto-test [OPTIONS] [PYTEST_ARGS...]"
            echo ""
            echo "Run ALTO test suite."
            echo ""
            echo "Options:"
            echo "  --skip-validate    Skip quick validation step"
            echo "  -h, --help         Show this help"
            echo ""
            echo "All other arguments are passed to pytest."
            echo ""
            echo "Examples:"
            echo "  alto-test                    # Run all tests"
            echo "  alto-test -v                 # Run with verbose output"
            echo "  alto-test -k hook_utils      # Run only hook_utils tests"
            echo "  alto-test --skip-validate    # Skip validation, run pytest only"
            exit 0
            ;;
        *)
            PYTEST_ARGS+=("$1")
            shift
            ;;
    esac
done

# Colors
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

echo -e "${BLUE}ALTO Test Suite${NC}"
echo "================"
echo ""

# Layer 1: Quick validation
if [ "$SKIP_VALIDATE" = false ]; then
    echo -e "${BLUE}[1/2] Running validation...${NC}"
    if "$ALTO_SRC/scripts/alto-validate.sh"; then
        echo -e "${GREEN}Validation passed${NC}"
    else
        echo -e "${RED}Validation failed${NC}"
        exit 1
    fi
    echo ""
else
    echo -e "${YELLOW}[1/2] Skipping validation${NC}"
    echo ""
fi

# Layer 2: pytest unit tests
echo -e "${BLUE}[2/2] Running pytest...${NC}"
echo ""

# Set PYTHONPATH to include hooks directory
export PYTHONPATH="$ALTO_SRC/hooks:${PYTHONPATH:-}"

# Run pytest
if [ ${#PYTEST_ARGS[@]} -eq 0 ]; then
    # Default: run with verbose output
    python3 -m pytest "$ALTO_SRC/tests/" -v --ignore="$ALTO_SRC/tests/scenarios"
else
    python3 -m pytest "$ALTO_SRC/tests/" --ignore="$ALTO_SRC/tests/scenarios" "${PYTEST_ARGS[@]}"
fi

echo ""
echo -e "${GREEN}All tests passed!${NC}"

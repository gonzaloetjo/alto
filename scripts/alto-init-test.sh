#!/usr/bin/env bash
# Initialize a test project that imports local ALTO
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALTO_SRC="$(dirname "$SCRIPT_DIR")"
TARGET="${1:-alto-test}"

if [ "$TARGET" = "--help" ] || [ "$TARGET" = "-h" ]; then
  echo "Usage: alto-init-test.sh [TARGET_DIR]"
  echo ""
  echo "Creates/updates a test project that imports local ALTO."
  echo "Default target: ./alto-test"
  echo ""
  echo "Run from anywhere. Safe to run multiple times."
  exit 0
fi

# Handle relative paths
if [[ "$TARGET" != /* ]]; then
  TARGET="$(pwd)/$TARGET"
fi

echo "Setting up test project at: $TARGET"
echo "Using ALTO from: $ALTO_SRC"

mkdir -p "$TARGET"
cd "$TARGET"

# Init git if needed
[ -d .git ] || git init -q

# Copy template files
cp "$ALTO_SRC"/templates/default/.envrc .
cp "$ALTO_SRC"/templates/default/.gitignore .
cp "$ALTO_SRC"/templates/default/devenv.nix .

# Calculate relative path from target to alto-2
ALTO_REL=$(realpath --relative-to="$TARGET" "$ALTO_SRC")

# Create devenv.yaml pointing to local alto
cat > devenv.yaml << EOF
# yaml-language-server: \$schema=https://devenv.sh/devenv.schema.json
inputs:
  nixpkgs:
    url: github:cachix/devenv-nixpkgs/rolling
  alto:
    url: path:$ALTO_REL
    flake: false

imports:
  - alto
EOF

echo ""
echo "Done. Now:"
echo "  cd $TARGET"
echo "  devenv shell"
echo "  claude"
echo ""
echo "To reset after changes to ALTO:"
echo "  alto-nuke"
echo "  (wait for direnv reload)"

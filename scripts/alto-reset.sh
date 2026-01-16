#!/usr/bin/env bash
# ALTO Reset - Bootstrap script that works even when ALTO is broken
# Usage: bash <(curl -fsSL https://raw.githubusercontent.com/gonzaloetjo/alto/main/scripts/alto-reset.sh)

set -e

echo "=== ALTO Reset ==="

# Check we're in an ALTO project (devenv.yaml must exist, even if empty)
if [ ! -e "devenv.yaml" ]; then
  echo "Error: devenv.yaml not found. Run this from an ALTO project directory."
  exit 1
fi

# Fix .envrc if empty
if [ ! -s ".envrc" ]; then
  echo "[0/5] Fixing empty .envrc..."
  cat > .envrc << 'ENVRC_EOF'
if ! has devenv; then
  echo "Installing devenv..."
  nix profile install --accept-flake-config github:cachix/devenv/latest
fi

eval "$(devenv print-dev-env)"
ENVRC_EOF
fi

# Step 1: Fix devenv.yaml if needed
echo "[1/5] Checking devenv.yaml..."
if [ ! -s "devenv.yaml" ] || ! grep -q 'alto' devenv.yaml 2>/dev/null; then
  echo "      devenv.yaml is empty or missing alto, resetting..."
  cat > devenv.yaml << 'YAML_EOF'
inputs:
  nixpkgs:
    url: github:cachix/devenv-nixpkgs/rolling
  alto:
    url: github:gonzaloetjo/alto?ref=main
    flake: false

imports:
  - alto
YAML_EOF
elif grep -q 'github:gonzaloetjo/alto$' devenv.yaml 2>/dev/null; then
  echo "      Adding ?ref=main to alto input..."
  sed -i 's|github:gonzaloetjo/alto$|github:gonzaloetjo/alto?ref=main|' devenv.yaml
else
  echo "      OK"
fi

# Step 2: Reset devenv.nix if corrupted or fix issues
echo "[2/5] Checking devenv.nix..."
if [ ! -s "devenv.nix" ] || ! grep -q '^{' devenv.nix 2>/dev/null; then
  echo "      devenv.nix is empty or corrupted, resetting..."
  cat > devenv.nix << 'DEVENV_EOF'
{ pkgs, ... }:
{
  # Switch modes with: alto-switch <mode>
}
DEVENV_EOF
elif grep -q 'lib.mkDefault' devenv.nix 2>/dev/null; then
  echo "      Fixing lib.mkDefault issue..."
  sed -i 's/lib\.mkDefault "\([^"]*\)"/"\1"/' devenv.nix
  # Remove lib from function args if not used elsewhere
  if ! grep -q 'lib\.' devenv.nix; then
    sed -i 's/{ pkgs, lib, \.\.\. }:/{ pkgs, ... }:/' devenv.nix
  fi
else
  echo "      OK"
fi

# Step 3: Clean caches
echo "[3/5] Removing .devenv and devenv.lock..."
rm -rf .devenv devenv.lock

# Step 4: Force fetch latest from GitHub
echo "[4/5] Fetching latest ALTO from GitHub..."
nix flake prefetch github:gonzaloetjo/alto?ref=main --refresh 2>/dev/null || echo "      (prefetch skipped)"

# Step 5: Rebuild
echo "[5/5] Running devenv update..."
devenv update

echo ""
echo "=== Done! ==="
echo "Run 'direnv reload' or 'devenv shell' to activate."

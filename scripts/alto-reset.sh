#!/usr/bin/env bash
# ALTO Reset - Bootstrap script that works even when ALTO is broken
# Usage: bash <(curl -fsSL https://raw.githubusercontent.com/gonzaloetjo/alto/main/scripts/alto-reset.sh)

set -e

echo "=== ALTO Reset ==="

# Check we're in an ALTO project
if [ ! -f "devenv.yaml" ]; then
  echo "Error: devenv.yaml not found. Run this from an ALTO project directory."
  exit 1
fi

# Step 1: Fix devenv.yaml if needed
echo "[1/5] Checking devenv.yaml..."
if grep -q 'github:gonzaloetjo/alto$' devenv.yaml 2>/dev/null; then
  echo "      Adding ?ref=main to alto input..."
  sed -i 's|github:gonzaloetjo/alto$|github:gonzaloetjo/alto?ref=main|' devenv.yaml
else
  echo "      OK"
fi

# Step 2: Reset devenv.nix to clean state (preserve custom config)
echo "[2/5] Checking devenv.nix..."
if grep -q 'lib.mkDefault' devenv.nix 2>/dev/null; then
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

#!/bin/bash
# Install git hooks for the Code Standards Auditor project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_DIR="$SCRIPT_DIR/.git"
HOOKS_DIR="$GIT_DIR/hooks"
SOURCE_HOOKS="$SCRIPT_DIR/.githooks"

echo "Installing git hooks..."

# Check if .git directory exists
if [ ! -d "$GIT_DIR" ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Install pre-commit hook
if [ -f "$SOURCE_HOOKS/pre-commit" ]; then
    echo "Installing pre-commit hook..."
    ln -sf "../../.githooks/pre-commit" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo "✅ Pre-commit hook installed"
else
    echo "❌ Error: pre-commit hook not found in $SOURCE_HOOKS"
    exit 1
fi

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "The pre-commit hook will:"
echo "  - Prevent committing .env files"
echo "  - Check for hardcoded credentials"
echo "  - Scan for API keys and passwords"
echo ""
echo "To bypass in emergencies (NOT RECOMMENDED):"
echo "  git commit --no-verify"
echo ""

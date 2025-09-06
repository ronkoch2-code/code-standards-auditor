#!/bin/zsh

# Git commit and push script for MCP Server validation fix
# Following Avatar-Engine project feature branch strategy

set -e
cd /Volumes/FS001/pythonscripts/code-standards-auditor

echo "=== Code Standards Auditor - MCP Server Validation Fix ==="
echo "Starting git operations..."

# Check current status
echo -e "\n=== Current Git Status ==="
git status --porcelain
git branch --show-current
git remote -v

# Create feature branch for this fix
BRANCH_NAME="fix/mcp-server-validation-error"
echo -e "\n=== Creating Feature Branch: $BRANCH_NAME ==="

# Check if branch exists, if so delete it
if git branch --list | grep -q "$BRANCH_NAME"; then
    echo "Branch $BRANCH_NAME already exists, switching to it..."
    git checkout "$BRANCH_NAME"
else
    echo "Creating new branch $BRANCH_NAME..."
    git checkout -b "$BRANCH_NAME"
fi

# Add modified files
echo -e "\n=== Adding Modified Files ==="
git add mcp/server.py
git add DEVELOPMENT_STATE.md
git add README.md

# Check what's staged
echo -e "\n=== Staged Changes ==="
git diff --cached --name-only

# Create commit message
COMMIT_MSG="fix: resolve MCP server Pydantic validation error

🚨 CRITICAL FIX: Claude Desktop Integration

**Problem:**
- MCP server tool validation failing with Pydantic error
- Missing 'type' field in check_status tool inputSchema
- Claude Desktop unable to load server tools

**Solution:**
- Added missing 'type': 'object' to check_status inputSchema
- All MCP tools now comply with JSON Schema requirements
- Server validates properly with Claude Desktop

**Files Modified:**
- mcp/server.py: Fixed tool schema validation error
- README.md: Added troubleshooting section and version history  
- DEVELOPMENT_STATE.md: Added session tracking and completion status

**Testing:**
- MCP server should now start without validation errors
- Claude Desktop integration should work correctly
- All tool definitions comply with Pydantic requirements

Closes: MCP server validation issue
Version: v2.0.2"

# Commit the changes
echo -e "\n=== Committing Changes ==="
git commit -m "$COMMIT_MSG"

# Push to origin
echo -e "\n=== Pushing to Origin ==="
git push -u origin "$BRANCH_NAME"

echo -e "\n=== ✅ SUCCESS: Git operations completed ==="
echo "Branch: $BRANCH_NAME"
echo "Ready for merge to main when tested"
echo "GitHub: https://github.com/ronkoch2-code/code-standards-auditor"

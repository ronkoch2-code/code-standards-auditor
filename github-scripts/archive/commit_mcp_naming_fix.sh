#!/bin/bash

# Git commit script for MCP naming conflict fix
# Date: 2025-09-04

echo "=========================================="
echo "Code Standards Auditor - MCP Naming Conflict Fix"
echo "=========================================="

# Navigate to project directory
cd /Volumes/FS001/pythonscripts/code-standards-auditor

# Check current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Create feature branch if not already on one
if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
    feature_branch="fix/mcp-import-naming-conflict"
    echo "Creating feature branch: $feature_branch"
    git checkout -b $feature_branch
else
    feature_branch=$current_branch
fi

# Add files
echo -e "\nAdding files to commit..."

# Core fix files
git add fix_mcp_naming_conflict.sh
git add test_mcp_import.py
git add mcp_config_updated.json
git add MCP_IMPORT_CONFLICT_FIX.md

# Updated documentation
git add DEVELOPMENT_STATE.md

# Add renamed directory if it exists
if [ -d "mcp_server" ]; then
    git add mcp_server/
    echo "Added mcp_server/ directory"
fi

# Remove old mcp directory from git if needed
if [ -d "mcp" ]; then
    git rm -r mcp/
    echo "Removed old mcp/ directory from git"
fi

# Show status
echo -e "\nFiles staged for commit:"
git status --short

# Commit with detailed message
echo -e "\nCreating commit..."
git commit -m "fix: Resolve MCP package import naming conflict

## Root Cause
Local 'mcp' directory was shadowing the installed mcp Python package,
causing circular import error when trying to import mcp.server.Server

## Solution
- Renamed local directory from 'mcp/' to 'mcp_server/'
- Updated all configuration files with new path
- Fixed import statements in server.py
- Created automated fix script

## Files Added
- fix_mcp_naming_conflict.sh: Automated fix script
- test_mcp_import.py: Verification test
- mcp_config_updated.json: Updated config for Claude Desktop
- MCP_IMPORT_CONFLICT_FIX.md: Documentation of issue and fix

## Breaking Changes
- Directory rename: mcp/ → mcp_server/
- Config path update required for Claude Desktop

## Testing
After applying fix:
1. Run: ./fix_mcp_naming_conflict.sh
2. Test: python3 test_mcp_import.py
3. Update Claude Desktop config
4. Restart Claude Desktop

Resolves: Circular import error in MCP server
Fixes: 'cannot import name Server from partially initialized module'
Type: fix
Scope: mcp-server
Breaking: yes (directory rename)"

# Push to remote
echo -e "\nPushing to GitHub..."
git push origin $feature_branch

echo -e "\n✅ Commit complete!"
echo "Branch: $feature_branch"
echo ""
echo "IMPORTANT - After merging, users must:"
echo "1. Pull the changes"
echo "2. Run: ./fix_mcp_naming_conflict.sh"
echo "3. Update Claude Desktop config"
echo "4. Restart Claude Desktop"
echo ""
echo "GitHub PR: https://github.com/ronkoch2-code/code-standards-auditor/pulls"

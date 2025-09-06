#!/bin/bash

# Git commit script for MCP debugging suite
# Date: 2025-09-04

echo "=========================================="
echo "Code Standards Auditor - MCP Debug Suite Commit"
echo "=========================================="

# Navigate to project directory
cd /Volumes/FS001/pythonscripts/code-standards-auditor

# Check current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Create feature branch if not already on one
if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
    feature_branch="feature/mcp-debugging-suite"
    echo "Creating feature branch: $feature_branch"
    git checkout -b $feature_branch
else
    feature_branch=$current_branch
fi

# Add files
echo -e "\nAdding files to commit..."

# Core debugging files
git add diagnose_mcp_failure.py
git add test_mcp_minimal.py
git add fix_mcp_server.sh
git add make_scripts_executable.py
git add MCP_DEBUG_GUIDE.md

# Updated documentation
git add DEVELOPMENT_STATE.md
git add README.md

# Show status
echo -e "\nFiles staged for commit:"
git status --short

# Commit with detailed message
echo -e "\nCreating commit..."
git commit -m "feat: Add comprehensive MCP server debugging suite

## What's New
- Created diagnostic tools for MCP server troubleshooting
- Added automated fix script for common issues
- Enhanced test coverage with minimal and full test scripts
- Added detailed debugging documentation

## Files Added
- diagnose_mcp_failure.py: Comprehensive diagnostic tool
- test_mcp_minimal.py: Quick minimal test script
- fix_mcp_server.sh: Automated fix script
- make_scripts_executable.py: Utility to set permissions
- MCP_DEBUG_GUIDE.md: Detailed troubleshooting guide

## Files Updated
- DEVELOPMENT_STATE.md: Current session progress
- README.md: Version 2.0.3 release notes

## Purpose
Addresses Claude Desktop MCP server failure reports by providing
a complete debugging and resolution toolkit. Users can now:
1. Run automated diagnostics
2. Apply fixes with single command
3. Follow detailed troubleshooting guide
4. Generate status reports

## Testing
- Test with: python3 test_mcp_minimal.py
- Fix with: ./fix_mcp_server.sh
- Full diagnostic: python3 diagnose_mcp_failure.py

Resolves: MCP server connection failures
Type: feat
Scope: debugging
Breaking: no"

# Push to remote
echo -e "\nPushing to GitHub..."
git push origin $feature_branch

echo -e "\n✅ Commit complete!"
echo "Branch: $feature_branch"
echo ""
echo "Next steps:"
echo "1. Create PR on GitHub: https://github.com/ronkoch2-code/code-standards-auditor/pulls"
echo "2. Review and merge to main"
echo "3. Test MCP server with: ./fix_mcp_server.sh"
echo ""
echo "To test locally:"
echo "  cd /Volumes/FS001/pythonscripts/code-standards-auditor"
echo "  python3 test_mcp_minimal.py"

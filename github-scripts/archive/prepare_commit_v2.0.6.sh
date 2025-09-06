#!/bin/bash

# GitHub preparation script for Code Standards Auditor
# Version: 2.0.6
# Date: 2025-09-05

echo "==========================================="
echo "Preparing for GitHub commit - v2.0.6"
echo "==========================================="
echo ""

# Set the project directory
PROJECT_DIR="/Volumes/FS001/pythonscripts/code-standards-auditor"
cd "$PROJECT_DIR"

# Create a feature branch for today's fixes
BRANCH_NAME="fix/mcp-server-startup-v2.0.6"
echo "Creating feature branch: $BRANCH_NAME"

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
echo "Current branch: $CURRENT_BRANCH"

# Ensure we're on main and up to date
git checkout main 2>/dev/null || git checkout -b main
git pull origin main 2>/dev/null || echo "No remote to pull from yet"

# Create and checkout feature branch
git checkout -b "$BRANCH_NAME"

# Stage the changes
echo ""
echo "Staging changes..."
git add mcp_server/server_impl/server.py
git add mcp_server/server_impl/server_backup_20250905.py
git add troubleshoot_neo4j.sh
git add DEVELOPMENT_STATE.md
git add README.md

# Remove the temporary fixed file
rm -f mcp_server/server_impl/server_fixed.py

# Show the status
echo ""
echo "Git status:"
git status

# Create commit message
COMMIT_MSG="fix(mcp): resolve server startup errors and improve Neo4j handling

- Fixed Tool registration: changed input_schema to inputSchema (MCP requirement)
- Added missing list_prompts() and list_resources() handlers
- Improved Neo4j authentication with database fallback
- Created troubleshooting script for Neo4j diagnostics
- Enhanced error messages with detailed troubleshooting steps
- Updated documentation and version to 2.0.6

Fixes: MCP server validation errors and Neo4j authentication issues"

echo ""
echo "Commit message:"
echo "$COMMIT_MSG"

echo ""
echo "Ready to commit! To complete the process, run:"
echo ""
echo "  git commit -m \"$COMMIT_MSG\""
echo "  git push origin $BRANCH_NAME"
echo ""
echo "Then create a pull request to merge into main."
echo ""
echo "==========================================="

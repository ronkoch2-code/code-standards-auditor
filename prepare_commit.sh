#!/bin/bash
# Git commit preparation script for Code Standards Auditor
# Version: 1.0.2
# Date: 2025-01-31

echo "========================================"
echo "Code Standards Auditor - Git Preparation"
echo "========================================"

# Check if we're in the correct directory
if [ ! -f "README.md" ]; then
    echo "Error: Not in the code-standards-auditor directory"
    exit 1
fi

# Initialize git if needed
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git branch -M main
    git remote add origin https://github.com/ronkoch2-code/code-standards-auditor.git
fi

# Add all files
echo "Adding files to git..."
git add .

# Show status
echo ""
echo "Git Status:"
git status --short

echo ""
echo "========================================"
echo "Ready to commit with:"
echo "git commit -m \"feat(mcp): add Claude Desktop integration via MCP server\""
echo "git push origin main"
echo "========================================"

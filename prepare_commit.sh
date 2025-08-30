#!/bin/bash
# Git commit preparation script for Code Standards Auditor
# Version: 1.0.1
# Date: 2025-01-27

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

# Prepare commit message
COMMIT_MSG="feat: implement core services and configuration

- Implemented configuration management with pydantic-settings
- Created cache manager with Redis backend for optimized performance
- Implemented Neo4j graph database service for standards relationships
- Enhanced Gemini service with prompt caching and batch processing
- Added comprehensive standards documentation (Python, Java, General)
- Set up project dependencies and requirements
- Created project structure following hexagonal architecture

BREAKING CHANGE: None
Refs: #1"

echo ""
echo "Prepared commit message:"
echo "------------------------"
echo "$COMMIT_MSG"
echo "------------------------"

echo ""
echo "To commit and push, run:"
echo "  git commit -m \"$COMMIT_MSG\""
echo "  git push -u origin main"

echo ""
echo "Or to commit with your own message:"
echo "  git commit -m \"your message here\""
echo "  git push -u origin main"

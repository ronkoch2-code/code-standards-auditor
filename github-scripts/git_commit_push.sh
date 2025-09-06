#!/bin/bash

# Git commit and push script for Code Standards Auditor
# Follows feature branch strategy similar to Avatar-Engine project

echo "================================================================"
echo "Code Standards Auditor - Git Commit & Push"
echo "================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Check if we're in the right directory
if [ ! -d "/Volumes/FS001/pythonscripts/code-standards-auditor/.git" ]; then
    echo -e "${RED}Error: Not in the code-standards-auditor git repository${NC}"
    exit 1
fi

cd /Volumes/FS001/pythonscripts/code-standards-auditor

# Check for uncommitted changes
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}No changes to commit${NC}"
    exit 0
fi

echo -e "${GREEN}Current branch: $CURRENT_BRANCH${NC}"
echo ""

# Show status
echo "Changed files:"
git status --short
echo ""

# Create or switch to feature branch if on main
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo -e "${YELLOW}You're on the main branch. Creating feature branch...${NC}"
    
    # Generate feature branch name based on the fix
    FEATURE_BRANCH="fix/mcp-dependencies-robust-server"
    
    # Check if branch already exists
    if git show-ref --verify --quiet refs/heads/$FEATURE_BRANCH; then
        echo "Switching to existing branch: $FEATURE_BRANCH"
        git checkout $FEATURE_BRANCH
    else
        echo "Creating new branch: $FEATURE_BRANCH"
        git checkout -b $FEATURE_BRANCH
    fi
    
    CURRENT_BRANCH=$FEATURE_BRANCH
fi

# Stage all changes
echo "Staging changes..."
git add -A

# Commit with the message from COMMIT_MESSAGE.md if it exists
if [ -f "COMMIT_MESSAGE.md" ]; then
    echo "Using commit message from COMMIT_MESSAGE.md"
    
    # Extract just the first line for the commit message
    COMMIT_MSG=$(head -n 1 COMMIT_MESSAGE.md)
    
    # Use the full file as the detailed message
    git commit -F COMMIT_MESSAGE.md
    
    echo -e "${GREEN}✓ Changes committed${NC}"
else
    # Fallback to a simple message
    echo "Enter commit message (or press Enter for default):"
    read -r USER_MSG
    
    if [ -z "$USER_MSG" ]; then
        COMMIT_MSG="fix: MCP server import error and dependencies update"
    else
        COMMIT_MSG="$USER_MSG"
    fi
    
    git commit -m "$COMMIT_MSG"
    echo -e "${GREEN}✓ Changes committed${NC}"
fi

# Push to remote
echo ""
echo "Pushing to remote repository..."

# Check if remote branch exists
if git ls-remote --heads origin $CURRENT_BRANCH | grep -q $CURRENT_BRANCH; then
    # Branch exists on remote, just push
    git push origin $CURRENT_BRANCH
else
    # New branch, set upstream
    git push -u origin $CURRENT_BRANCH
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully pushed to $CURRENT_BRANCH${NC}"
    echo ""
    echo "================================================================"
    echo "Next steps:"
    echo "1. Go to: https://github.com/ronkoch2-code/code-standards-auditor"
    echo "2. Create a Pull Request from '$CURRENT_BRANCH' to 'main'"
    echo "3. Review and merge the changes"
    echo "================================================================"
else
    echo -e "${RED}✗ Failed to push changes${NC}"
    exit 1
fi

# Clean up commit message file
if [ -f "COMMIT_MESSAGE.md" ]; then
    echo ""
    echo "Removing COMMIT_MESSAGE.md..."
    rm COMMIT_MESSAGE.md
fi

echo ""
echo -e "${GREEN}All done!${NC}"

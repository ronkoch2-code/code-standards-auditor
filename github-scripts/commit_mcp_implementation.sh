#!/bin/zsh

# Git commit script for Code Standards Auditor MCP Implementation
# Version: 3.0.1
# Date: 2025-09-06

echo "🚀 Code Standards Auditor - Git Commit Preparation"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Volumes/FS001/pythonscripts/code-standards-auditor"
BRANCH_NAME="feature/mcp-implementation-v3"
COMMIT_MESSAGE="feat: Complete MCP server implementation with stdout fix

- Implemented full MCP (Model Context Protocol) server
- Fixed stdout pollution issues by redirecting all output to stderr
- Resolved circular imports and namespace collisions
- Added comprehensive error handling and logging
- Cleaned up 70+ temporary debug and fix scripts
- Updated documentation for v3.0.1 release
- Tested and verified with Claude Desktop integration

BREAKING CHANGE: Architecture redesigned to separate Neo4j concerns
See ARCHITECTURE_V3.md for migration guide"

# Change to project directory
cd "$PROJECT_DIR"

echo "${BLUE}📁 Current directory: $(pwd)${NC}"
echo ""

# Check git status
echo "${YELLOW}📊 Current git status:${NC}"
git status --short
echo ""

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "${BLUE}🌿 Current branch: $CURRENT_BRANCH${NC}"
echo ""

# Function to create or switch to feature branch
setup_feature_branch() {
    if [ "$CURRENT_BRANCH" != "$BRANCH_NAME" ]; then
        echo "${YELLOW}Creating/switching to feature branch: $BRANCH_NAME${NC}"
        
        # Check if branch exists
        if git show-ref --quiet refs/heads/$BRANCH_NAME; then
            git checkout $BRANCH_NAME
        else
            git checkout -b $BRANCH_NAME
        fi
        echo "${GREEN}✅ Switched to $BRANCH_NAME${NC}"
    else
        echo "${GREEN}✅ Already on feature branch: $BRANCH_NAME${NC}"
    fi
}

# Function to run cleanup
run_cleanup() {
    echo ""
    echo "${YELLOW}🧹 Running cleanup script...${NC}"
    
    if [ -f "cleanup_temp_files.sh" ]; then
        chmod +x cleanup_temp_files.sh
        ./cleanup_temp_files.sh
        echo "${GREEN}✅ Cleanup completed${NC}"
    else
        echo "${YELLOW}⚠️  Cleanup script not found, skipping...${NC}"
    fi
}

# Function to add files to git
stage_changes() {
    echo ""
    echo "${YELLOW}📝 Staging changes...${NC}"
    
    # Add all changes except archived files
    git add -A
    
    # Unstage archived_temp_files directory if it exists
    if [ -d "archived_temp_files" ]; then
        git reset HEAD archived_temp_files/
        echo "${YELLOW}⚠️  Excluded archived_temp_files from commit${NC}"
    fi
    
    # Unstage .env file for security
    git reset HEAD .env 2>/dev/null
    
    # Remove the cleanup scripts from staging
    git reset HEAD cleanup_temp_files.sh 2>/dev/null
    git reset HEAD run_cleanup.py 2>/dev/null
    
    echo "${GREEN}✅ Changes staged${NC}"
}

# Function to show what will be committed
show_commit_preview() {
    echo ""
    echo "${BLUE}📋 Files to be committed:${NC}"
    git diff --cached --name-status | head -20
    
    TOTAL_FILES=$(git diff --cached --name-status | wc -l | tr -d ' ')
    if [ "$TOTAL_FILES" -gt 20 ]; then
        echo "... and $((TOTAL_FILES - 20)) more files"
    fi
    
    echo ""
    echo "${BLUE}📊 Change summary:${NC}"
    git diff --cached --stat
}

# Function to create commit
create_commit() {
    echo ""
    echo "${YELLOW}💾 Creating commit...${NC}"
    
    git commit -m "$COMMIT_MESSAGE"
    
    if [ $? -eq 0 ]; then
        echo "${GREEN}✅ Commit created successfully!${NC}"
        
        # Show commit info
        echo ""
        echo "${BLUE}📝 Commit details:${NC}"
        git log -1 --oneline
    else
        echo "${RED}❌ Commit failed${NC}"
        return 1
    fi
}

# Function to push to remote
push_to_remote() {
    echo ""
    echo "${YELLOW}🔄 Ready to push to remote?${NC}"
    echo "This will push branch: ${BLUE}$BRANCH_NAME${NC} to origin"
    echo ""
    read "PUSH_CONFIRM?Push to remote? (y/n): "
    
    if [[ "$PUSH_CONFIRM" == "y" || "$PUSH_CONFIRM" == "Y" ]]; then
        echo "${YELLOW}📤 Pushing to remote...${NC}"
        git push -u origin $BRANCH_NAME
        
        if [ $? -eq 0 ]; then
            echo "${GREEN}✅ Successfully pushed to remote!${NC}"
            echo ""
            echo "${BLUE}🔗 Next steps:${NC}"
            echo "  1. Create a Pull Request on GitHub"
            echo "  2. Review the changes"
            echo "  3. Merge to main branch"
            echo ""
            echo "${BLUE}GitHub URL:${NC} https://github.com/ronkoch2-code/code-standards-auditor"
        else
            echo "${RED}❌ Push failed${NC}"
        fi
    else
        echo "${YELLOW}⏸️  Push skipped. You can push later with:${NC}"
        echo "  git push -u origin $BRANCH_NAME"
    fi
}

# Main execution
main() {
    echo "${GREEN}Starting git operations...${NC}"
    echo ""
    
    # Step 1: Run cleanup
    read "CLEANUP_CONFIRM?Run cleanup script to archive temp files? (y/n): "
    if [[ "$CLEANUP_CONFIRM" == "y" || "$CLEANUP_CONFIRM" == "Y" ]]; then
        run_cleanup
    fi
    
    # Step 2: Setup feature branch
    setup_feature_branch
    
    # Step 3: Stage changes
    stage_changes
    
    # Step 4: Show preview
    show_commit_preview
    
    # Step 5: Confirm and commit
    echo ""
    read "COMMIT_CONFIRM?Proceed with commit? (y/n): "
    
    if [[ "$COMMIT_CONFIRM" == "y" || "$COMMIT_CONFIRM" == "Y" ]]; then
        create_commit
        
        if [ $? -eq 0 ]; then
            # Step 6: Push to remote
            push_to_remote
        fi
    else
        echo "${YELLOW}⏸️  Commit cancelled${NC}"
        echo "Changes remain staged. You can commit manually with:"
        echo "  git commit -m \"your message\""
    fi
    
    echo ""
    echo "${GREEN}✨ Git operations complete!${NC}"
}

# Run main function
main

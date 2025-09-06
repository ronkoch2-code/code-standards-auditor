#!/bin/zsh

# Quick execution script for MCP implementation GitHub commit
# This script runs all necessary steps in sequence

echo "🚀 Code Standards Auditor - GitHub Commit Quick Start"
echo "===================================================="
echo ""
echo "This script will:"
echo "  1. Run cleanup to archive temp files"
echo "  2. Archive old GitHub scripts"
echo "  3. Execute the main commit script"
echo ""

# Make all scripts executable
chmod +x cleanup_temp_files.sh
chmod +x cleanup_github_scripts.sh
chmod +x github-scripts/commit_mcp_implementation.sh

# Step 1: Cleanup temp files
echo "Step 1: Cleaning up temporary files..."
./cleanup_temp_files.sh

echo ""
echo "Step 2: Archiving old GitHub scripts..."
./cleanup_github_scripts.sh

echo ""
echo "Step 3: Running GitHub commit preparation..."
./github-scripts/commit_mcp_implementation.sh

echo ""
echo "✅ All steps completed!"

#!/bin/zsh

# Archive old GitHub scripts that are no longer needed
# Date: 2025-09-06

echo "📦 Archiving old GitHub scripts..."

cd /Volumes/FS001/pythonscripts/code-standards-auditor/github-scripts

# Create archive directory if it doesn't exist
mkdir -p archive

# Move old commit scripts to archive
mv commit_mcp_debugging_suite.sh archive/ 2>/dev/null
mv commit_mcp_fixes.sh archive/ 2>/dev/null
mv commit_mcp_naming_fix.sh archive/ 2>/dev/null
mv commit_mcp_validation_fix.sh archive/ 2>/dev/null
mv commit_monitoring_fix.sh archive/ 2>/dev/null
mv commit_python_path_fix.sh archive/ 2>/dev/null
mv commit_workflow_fixes.sh archive/ 2>/dev/null
mv deploy_complete_fix.sh archive/ 2>/dev/null
mv deploy_complete_workflow.sh archive/ 2>/dev/null
mv deploy_fix.sh archive/ 2>/dev/null
mv prepare_commit_v2.0.6.sh archive/ 2>/dev/null
mv session_commit_20250905.sh archive/ 2>/dev/null
mv quick_fix.sh archive/ 2>/dev/null
mv make_commit_executable.py archive/ 2>/dev/null
mv make_executable.py archive/ 2>/dev/null

echo "✅ Old scripts archived to github-scripts/archive/"
echo ""
echo "Active scripts retained:"
ls -la *.sh 2>/dev/null | grep -v archive

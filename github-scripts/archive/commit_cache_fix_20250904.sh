#!/bin/bash
# Git commit script for cache service method fixes
# Created: September 01, 2025
# Purpose: Commit the cache method fixes to resolve Phase 3 research execution error

set -e

echo "🔧 Code Standards Auditor - Cache Service Method Fix Commit"
echo "============================================================="

# Change to project directory
cd "$(dirname "$0")"

echo "📁 Current directory: $(pwd)"
echo "🌿 Current branch: $(git branch --show-current)"

# Add the modified files
echo "📦 Adding modified files..."
git add services/standards_research_service.py
git add DEVELOPMENT_STATUS.md
git add test_fix.py
git add README.md

# Show what we're committing
echo ""
echo "📝 Files to be committed:"
git status --porcelain

echo ""
echo "🔍 Changes summary:"
echo "- Fixed CacheService method calls in StandardsResearchService"
echo "- get_cached_audit() → get_audit_result()"
echo "- cache_audit_result() → set_audit_result()" 
echo "- Fixed cache manager access pattern"
echo "- Added test script to verify fixes"
echo "- Updated development status documentation"

# Commit the changes
echo ""
echo "💾 Committing changes..."
git commit -m "fix: resolve CacheService method name mismatch in StandardsResearchService

- Fix 'CacheService' object has no attribute 'get_cached_audit' error
- Replace get_cached_audit() with get_audit_result() using proper parameters
- Replace cache_audit_result() with set_audit_result() using proper parameters  
- Fix cache manager access pattern in _queue_pattern_for_research method
- Add test_fix.py to verify the fixes work correctly
- Update DEVELOPMENT_STATUS.md with fix documentation

Resolves: Phase 3 AI Research Execution failure
Component: services/standards_research_service.py
Impact: Critical - enables research functionality to work"

echo ""
echo "🚀 Preparing to push changes..."

# Check if we need to set upstream
current_branch=$(git branch --show-current)
if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} &>/dev/null; then
    echo "🔗 Setting upstream for branch $current_branch..."
    git push -u origin "$current_branch"
else
    echo "📤 Pushing to existing upstream..."
    git push
fi

echo ""
echo "✅ Commit completed successfully!"
echo ""
echo "🎯 Next Steps:"
echo "1. Test the fix: python3 test_fix.py"
echo "2. Run enhanced CLI: python3 cli/enhanced_cli.py interactive" 
echo "3. Test Phase 3 research functionality"
echo ""
echo "🔗 Repository: https://github.com/ronkoch2-code/code-standards-auditor"

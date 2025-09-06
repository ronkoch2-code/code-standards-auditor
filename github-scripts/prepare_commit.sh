#!/bin/bash
# Git preparation script for Code Standards Auditor
# Date: September 06, 2025

echo "==================================================="
echo "Git Preparation for Code Standards Auditor"
echo "==================================================="

cd /Volumes/FS001/pythonscripts/code-standards-auditor

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    git remote add origin https://github.com/ronkoch2-code/code-standards-auditor.git
fi

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    echo "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
.env.*.local

# Cache
.cache/
*.cache

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# Testing
.coverage
htmlcov/
.pytest_cache/

# Backups
*.backup
*.bak
*_backup_*

# MCP
mcp.log
EOF
fi

# Add all files
echo ""
echo "Adding files to staging..."
git add -A

# Show status
echo ""
echo "Current git status:"
git status

echo ""
echo "==================================================="
echo "Ready for commit!"
echo "==================================================="
echo ""
echo "To commit and push, run:"
echo "  git commit -m 'Fix MCP StdoutProtector buffer attribute error'"
echo "  git push origin main"
echo ""
echo "Or use the feature branch strategy:"
echo "  git checkout -b fix/mcp-stdout-buffer"
echo "  git commit -m 'Fix MCP StdoutProtector buffer attribute error'"
echo "  git push origin fix/mcp-stdout-buffer"

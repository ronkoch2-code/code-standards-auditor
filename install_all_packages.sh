#!/bin/bash

# Install all required Python packages for Code Standards Auditor
# This fixes the confusion between Neo4j server (database) and neo4j Python package (client)
# Date: 2025-09-05

echo "=========================================="
echo "Installing Required Python Packages"
echo "=========================================="
echo ""
echo "CLARIFICATION:"
echo "- Neo4j SERVER (database): You have this running ✅"
echo "- neo4j PYTHON package (client): This might be missing ⚠️"
echo ""

# Use python3 -m pip to ensure correct installation
echo "Installing packages using: python3 -m pip"
echo ""

# Core required packages
PACKAGES=(
    "neo4j"                  # Python client for Neo4j database
    "google-generativeai"    # Gemini AI integration
    "redis"                  # Redis cache client
    "python-dotenv"          # Environment variable management
    "mcp"                    # Model Context Protocol for Claude
    "pydantic-settings"      # Settings management
    "fastapi"               # Web framework
    "uvicorn"               # ASGI server
    "structlog"             # Structured logging
)

echo "Installing ${#PACKAGES[@]} packages..."
echo "=========================================="

# Install each package
for package in "${PACKAGES[@]}"
do
    echo ""
    echo "Installing $package..."
    python3 -m pip install "$package"
    
    if [ $? -eq 0 ]; then
        echo "✅ $package installed successfully"
    else
        echo "❌ Failed to install $package"
    fi
done

echo ""
echo "=========================================="
echo "Verifying installations..."
echo "=========================================="

# Run the Python diagnostic
python3 fix_neo4j_python.py

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart Claude Desktop"
echo "2. Test with: 'Check the code standards auditor status'"
echo ""

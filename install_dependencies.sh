#!/bin/bash

# Code Standards Auditor - Dependency Installation Script
# Created: September 01, 2025
# Purpose: Install all required Python dependencies

set -e  # Exit on any error

echo "🚀 Installing Code Standards Auditor Dependencies..."
echo "=============================================="

# Change to project directory
cd "$(dirname "$0")"

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Install/upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install main dependencies
echo "📚 Installing dependencies from requirements.txt..."
python3 -m pip install -r requirements.txt

# Install MCP dependencies (if separate file exists)
if [ -f "requirements-mcp.txt" ]; then
    echo "🔌 Installing MCP dependencies..."
    python3 -m pip install -r requirements-mcp.txt
fi

# Verify key imports
echo "🔍 Verifying key module imports..."
python3 -c "
import structlog
import google.generativeai as genai
import neo4j
import redis
import fastapi
import mcp

print('✅ All critical modules imported successfully!')
print('📝 structlog version:', structlog.__version__)
print('🤖 google-generativeai version:', genai.__version__)
print('🔗 neo4j version:', neo4j.__version__)
print('⚡ fastapi version:', fastapi.__version__)
"

echo ""
echo "✅ Dependencies installed successfully!"
echo "🎯 You can now run: python3 cli/enhanced_cli.py interactive"

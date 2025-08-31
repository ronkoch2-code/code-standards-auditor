#!/bin/bash

# Setup script for Code Standards Auditor MCP Server
# This script installs/updates the necessary dependencies and prepares the environment

echo "================================================================"
echo "Code Standards Auditor - MCP Server Setup"
echo "================================================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check for environment variables
echo ""
echo "Checking environment variables..."

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠ Warning: GEMINI_API_KEY is not set"
    echo "  Please set it with: export GEMINI_API_KEY='your_api_key'"
else
    echo "✓ GEMINI_API_KEY is set"
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    echo "⚠ Warning: NEO4J_PASSWORD is not set"
    echo "  Please set it with: export NEO4J_PASSWORD='your_password'"
else
    echo "✓ NEO4J_PASSWORD is set"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠ Warning: ANTHROPIC_API_KEY is not set (optional)"
else
    echo "✓ ANTHROPIC_API_KEY is set"
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install/update MCP package
echo ""
echo "Installing MCP (Model Context Protocol) package..."
python3 -m pip install --upgrade mcp

# Install requirements
echo ""
echo "Installing project requirements..."
cd /Volumes/FS001/pythonscripts/code-standards-auditor
python3 -m pip install -r requirements.txt

# Run the test script
echo ""
echo "Running MCP server tests..."
python3 mcp/test_server.py

echo ""
echo "================================================================"
echo "Setup complete!"
echo ""
echo "To configure Claude Desktop to use this MCP server:"
echo "1. Copy the MCP configuration to Claude Desktop:"
echo "   cp mcp/mcp_config.json ~/Library/Application\\ Support/Claude/claude_desktop_config.json"
echo ""
echo "2. Restart Claude Desktop"
echo ""
echo "To test the server manually:"
echo "   python3 mcp/server.py"
echo "================================================================"

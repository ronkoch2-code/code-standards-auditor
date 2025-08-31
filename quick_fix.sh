#!/bin/bash

# Quick fix script for immediate MCP server functionality
# This installs just the missing critical packages

echo "Installing missing packages for MCP server..."

# Install Google Generative AI (the main missing package)
echo "Installing google-generativeai..."
pip install google-generativeai

# Fix the tree-sitter-javascript version
echo "Fixing tree-sitter-javascript version..."
pip install tree-sitter-javascript==0.23.1

# Install other critical packages if missing
echo "Ensuring other critical packages..."
pip install mcp neo4j redis pydantic-settings

echo ""
echo "Done! You can now run:"
echo "  python3 mcp/server.py"
echo ""
echo "Or test with:"
echo "  python3 mcp/test_server.py"

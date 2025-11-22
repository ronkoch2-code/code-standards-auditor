#!/bin/bash
# MCP Server initialization script
# Ensures all dependencies are installed for MCP server

echo "Installing MCP dependencies..."

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Not in a virtual environment. Consider activating one first."
    echo "Run: source venv/bin/activate"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install MCP SDK
pip install mcp

# Check if services are running
echo ""
echo "Checking required services..."

# Check Neo4j
if command -v neo4j &> /dev/null; then
    neo4j status
else
    echo "⚠️  Neo4j not found. Please install Neo4j."
fi

# Check Redis
if command -v redis-cli &> /dev/null; then
    redis-cli ping && echo "✅ Redis is running"
else
    echo "⚠️  Redis not found. Please install Redis."
fi

# Check environment variables
echo ""
echo "Checking environment variables..."

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY not set"
else
    echo "✅ GEMINI_API_KEY is set"
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    echo "⚠️  NEO4J_PASSWORD not set"
else
    echo "✅ NEO4J_PASSWORD is set"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ℹ️  ANTHROPIC_API_KEY not set (optional)"
else
    echo "✅ ANTHROPIC_API_KEY is set"
fi

echo ""
echo "MCP Server setup check complete!"
echo "To configure Claude Desktop, see: mcp/README.md"

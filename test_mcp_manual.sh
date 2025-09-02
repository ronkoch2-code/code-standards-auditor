#!/bin/bash

# MCP Server Manual Test Script
# This script provides instructions for manually testing the MCP server

echo "=================================================="
echo "  Code Standards Auditor - MCP Server Test Guide"
echo "=================================================="
echo

# Check if we're in the right directory
if [ ! -f "mcp/server.py" ]; then
    echo "❌ Error: Please run this script from the code-standards-auditor directory"
    echo "   cd /Volumes/FS001/pythonscripts/code-standards-auditor"
    exit 1
fi

echo "🔍 Step 1: Quick Dependency Check"
echo "=================================="

# Run our quick test
echo "Running quick MCP test..."
python3 quick_mcp_test.py

echo
echo "🚀 Step 2: Manual Server Test (Optional)"
echo "======================================="
echo "You can manually test the MCP server (it won't connect to Claude, but will show if it starts):"
echo
echo "Command to run:"
echo "   python3 mcp/server.py"
echo
echo "Expected behavior:"
echo "   - Server should start without critical errors"
echo "   - You'll see initialization messages"
echo "   - Press Ctrl+C to stop"
echo
echo "⚠️  Note: The server will wait for MCP protocol input (which only Claude Desktop provides)"
echo

echo "🖥️  Step 3: Claude Desktop Integration"
echo "====================================="
echo
echo "Option A - Copy our config (recommended):"
echo "   cp mcp/mcp_config.json ~/Library/Application\\ Support/Claude/claude_desktop_config.json"
echo
echo "Option B - Merge with existing config:"
echo "   # Edit: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "   # Add the contents from mcp/mcp_config.json"
echo
echo "Step 3.1: Restart Claude Desktop completely"
echo "Step 3.2: Open Claude Desktop"
echo "Step 3.3: Look for MCP indicator (usually shown in interface)"
echo "Step 3.4: Try commands like:"
echo "           'Check the status of the code standards auditor'"
echo "           'Audit this Python code: print(\"hello world\")'"
echo

echo "🔧 Step 4: Troubleshooting"
echo "========================="
echo
echo "If MCP doesn't work in Claude Desktop:"
echo "1. Check Claude Desktop logs:"
echo "   - macOS: ~/Library/Logs/Claude/"
echo "   - Look for MCP-related errors"
echo
echo "2. Verify environment variables are available to Claude Desktop"
echo "   (You may need to start Claude Desktop from terminal with env vars set)"
echo
echo "3. Test our server manually first:"
echo "   python3 mcp/server.py"
echo
echo "4. Check Claude Desktop config file syntax:"
echo "   cat ~/Library/Application\\ Support/Claude/claude_desktop_config.json"
echo

echo "🎯 Success Indicators"
echo "===================="
echo "✅ In Claude Desktop, you should see:"
echo "   - MCP indicator in the interface" 
echo "   - Ability to use commands like 'check status' or 'audit code'"
echo "   - Server responds with structured information about code standards"
echo

echo "💡 Pro Tips"
echo "==========="
echo "- Start with simple commands like 'check status'"
echo "- The server gracefully handles missing dependencies"
echo "- Neo4j and Redis are optional - basic functionality works without them"
echo "- Gemini API key is required for AI features"
echo

echo "📝 Quick Commands to Test in Claude Desktop:"
echo "==========================================="
echo "1. 'Check the status of the code standards auditor'"
echo "2. 'What coding standards do you have for Python?'"
echo "3. 'Audit this code: def foo(): pass'"
echo
echo "=================================================="
echo "Manual test complete! Follow the steps above to test with Claude Desktop."
echo "=================================================="

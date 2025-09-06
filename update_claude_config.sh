#!/bin/bash
# Script to update claude_desktop_config.json

CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Backup existing config
if [ -f "$CONFIG_PATH" ]; then
    cp "$CONFIG_PATH" "$CONFIG_PATH.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Backed up existing config"
fi

# Write new config with code-standards-auditor MCP server
cat > "$CONFIG_PATH" << 'EOF'
{
  "mcpServers": {
    "code-standards-auditor": {
      "command": "/usr/local/bin/python3",
      "args": [
        "/Volumes/FS001/pythonscripts/code-standards-auditor/mcp_server/server_hardcoded.py"
      ],
      "env": {
        "NEO4J_PASSWORD": "M@ry1and2",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_DATABASE": "neo4j",
        "GEMINI_API_KEY": "AIzaSyBlKf19Wl6PDRkcXXD22vmsg8En_lfixGM"
      }
    }
  }
}
EOF

echo "Updated claude_desktop_config.json"
echo "Please restart Claude Desktop to apply changes"

# Code Standards Auditor - v3.0 Architecture

## Clean Separation of Concerns

### Why This Architecture?

The previous attempts to embed Neo4j within our MCP server caused stdout pollution issues that broke the MCP protocol. The solution: **separation of concerns**.

## 🏗️ New Architecture

```
Claude Desktop
    │
    ├─→ Code Standards Auditor MCP (Simplified)
    │   • Gemini AI code analysis
    │   • File-based standards management
    │   • Save/retrieve standards
    │   • Clean, no stdout issues
    │
    └─→ Neo4j MCP Server (Native)
        • Graph database operations
        • Relationship management  
        • Complex queries
        • Official Neo4j implementation
```

## 🚀 Quick Setup

### 1. Set Up Simplified Code Standards Server

```bash
# Update claude_desktop_config.json
cat >> ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "code-standards-simple": {
      "command": "/usr/local/bin/python3",
      "args": [
        "/Volumes/FS001/pythonscripts/code-standards-auditor/mcp_server/server_simple.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key"
      }
    },
    "neo4j-dev": {
      "command": "python3",
      "args": ["-m", "neo4j_mcp"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-password"
      }
    }
  }
}
EOF
```

### 2. Test the Simplified Server

```bash
# Quick test
python3 /Volumes/FS001/pythonscripts/code-standards-auditor/mcp_server/server_simple.py

# Should start cleanly with no stdout pollution!
```

### 3. Install Neo4j MCP Server (if needed)

```bash
# Install Neo4j's official MCP server
pip install neo4j-mcp

# Make sure Neo4j is running
brew services start neo4j
```

## 📋 Usage Examples

### In Claude Desktop (after restart):

**Check Code Standards Status:**
```
Use the code-standards-simple server to check its status
```

**Analyze Code:**
```
Use code-standards-simple to analyze this Python code for security issues:
[paste code]
```

**Graph Database Operations:**
```
Use neo4j-dev to create a node for a new coding standard with name "API Security"
```

**Coordinated Workflow:**
```
1. Use code-standards-simple to analyze my code
2. Use neo4j-dev to store the violations found
3. Use code-standards-simple to get the relevant standards
4. Use neo4j-dev to create relationships between violations and standards
```

## ✅ Benefits of This Approach

1. **No stdout pollution** - Each server manages its own I/O
2. **Clean separation** - Neo4j issues don't affect code analysis
3. **Use official implementations** - Neo4j's MCP is maintained by them
4. **Easier debugging** - Issues are isolated
5. **Better scaling** - Services can run on different machines if needed
6. **Simpler code** - Each server does one thing well

## 🔧 Available Tools

### Code Standards Simple Server:
- `check_status` - Service health check
- `get_standards` - Retrieve standards from files
- `analyze_code` - Gemini AI analysis (if configured)
- `save_standard` - Save new standards to filesystem

### Neo4j Server (native):
- All standard Neo4j Cypher operations
- Node and relationship management
- Graph queries and analysis

## 🎯 Migration Path

1. Start using the simplified server immediately
2. Keep Neo4j operations separate using its native MCP
3. Use Claude to coordinate between the two servers
4. Gradually migrate any Neo4j-dependent features

## 📝 Environment Variables

### For Code Standards Server:
- `GEMINI_API_KEY` - Your Google Gemini API key

### For Neo4j Server:
- `NEO4J_URI` - Connection string (default: bolt://localhost:7687)
- `NEO4J_USERNAME` - Neo4j username (default: neo4j)
- `NEO4J_PASSWORD` - Neo4j password

## 🚨 Troubleshooting

If you see JSON parsing errors:
- The simplified server shouldn't have these issues
- Check that you're using `server_simple.py` not the old complex one

If Neo4j connection fails:
- That's isolated to the Neo4j MCP server
- Check Neo4j is running: `brew services list`
- Verify credentials in the config

## 🎉 Success!

This architecture solves the stdout pollution problem completely by:
- Removing Neo4j from our custom server
- Using Neo4j's official MCP implementation
- Keeping concerns separated
- Making the system more maintainable

No more fighting with stdout redirection!

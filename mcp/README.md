# MCP Server Setup for Code Standards Auditor

## Overview
The MCP (Model Context Protocol) server enables Claude Desktop to directly interact with the Code Standards Auditor system, providing seamless code auditing capabilities within Claude conversations.

## Installation

### 1. Install MCP SDK
```bash
pip install mcp
```

### 2. Configure Claude Desktop

Add the following to your Claude Desktop configuration file:

**On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "code-standards-auditor": {
      "command": "python3",
      "args": [
        "/Volumes/FS001/pythonscripts/code-standards-auditor/mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key",
        "NEO4J_PASSWORD": "your-neo4j-password",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key"
      }
    }
  }
}
```

### 3. Environment Variables

Ensure the following environment variables are set:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `NEO4J_PASSWORD`: Neo4j database password
- `ANTHROPIC_API_KEY`: (Optional) Anthropic API key for fallback

### 4. Start Services

Before using the MCP server, ensure the following services are running:

```bash
# Start Neo4j
neo4j start

# Start Redis (for caching)
redis-server

# Test MCP server
python3 /Volumes/FS001/pythonscripts/code-standards-auditor/mcp/server.py
```

## Available Tools

Once configured, Claude Desktop will have access to the following tools:

### 1. `audit_code`
Audit source code against coding standards.

**Parameters:**
- `code` (required): Source code to audit
- `language` (required): Programming language (python/java/javascript/general)
- `project_id`: Optional project identifier
- `severity_threshold`: Minimum severity level (info/warning/error/critical)

**Example usage in Claude:**
"Can you audit this Python function for coding standards?"

### 2. `get_standards`
Retrieve coding standards documentation.

**Parameters:**
- `language` (required): Programming language
- `category`: Optional category filter

**Example usage in Claude:**
"What are the Python coding standards for error handling?"

### 3. `update_standards`
Add or update coding standards.

**Parameters:**
- `language` (required): Programming language
- `rule` (required): Rule object with name, description, and severity

**Example usage in Claude:**
"Add a new Python standard for type hints"

### 4. `analyze_project`
Analyze an entire project directory.

**Parameters:**
- `project_path` (required): Path to project directory
- `recursive`: Scan subdirectories (default: true)
- `file_patterns`: File patterns to include

**Example usage in Claude:**
"Analyze all Python files in /path/to/my/project"

### 5. `get_audit_history`
Retrieve audit history for a project.

**Parameters:**
- `project_id` (required): Project identifier
- `limit`: Number of records to retrieve (default: 10)

**Example usage in Claude:**
"Show me the audit history for project 'my-app'"

## Troubleshooting

### Common Issues

1. **MCP server not found by Claude Desktop**
   - Verify the path in `claude_desktop_config.json` is correct
   - Ensure Python 3 is installed and accessible as `python3`
   - Check Claude Desktop logs for error messages

2. **Connection to services failed**
   - Ensure Neo4j is running: `neo4j status`
   - Ensure Redis is running: `redis-cli ping`
   - Verify environment variables are set correctly

3. **Permission denied errors**
   - Ensure the MCP server script is executable: `chmod +x server.py`
   - Check file permissions for the project directory

### Logging

Enable debug logging by setting the environment variable:
```bash
export MCP_LOG_LEVEL=DEBUG
```

Logs will be written to:
- macOS: `~/Library/Logs/Claude/mcp-server.log`
- Windows: `%APPDATA%\Claude\Logs\mcp-server.log`

## Testing

Test the MCP server independently:

```python
# test_mcp.py
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server

async def test():
    # Import and test your server
    from server import CodeAuditorMCPServer
    server = CodeAuditorMCPServer()
    
    # Test tool listing
    tools = await server.server.list_tools()
    print(f"Available tools: {[t.name for t in tools]}")
    
    # Test a simple audit
    result = await server._audit_code({
        "code": "def hello_world():\n    print('Hello')",
        "language": "python"
    })
    print(f"Audit result: {result}")

if __name__ == "__main__":
    asyncio.run(test())
```

## Architecture

```
Claude Desktop
     |
     v
MCP Protocol (stdio)
     |
     v
Code Auditor MCP Server
     |
     +---> Gemini Service (AI Analysis)
     |
     +---> Neo4j Service (Graph Database)
     |
     +---> Cache Service (Redis)
     |
     +---> File System (Standards Docs)
```

## Security Considerations

1. **API Key Management**: Store API keys in environment variables, never in code
2. **File Access**: The MCP server only accesses allowed directories
3. **Input Validation**: All inputs are validated before processing
4. **Rate Limiting**: Consider implementing rate limiting for API calls
5. **Audit Trail**: All operations are logged for security auditing

## Performance Optimization

1. **Caching**: Results are cached in Redis to reduce API calls
2. **Batch Processing**: Multiple files can be analyzed in batches
3. **Prompt Caching**: Gemini prompts are cached for efficiency
4. **Async Operations**: All I/O operations are asynchronous

## Development

### Adding New Tools

To add a new tool:

1. Define the tool schema in `list_tools()`
2. Add handler in `call_tool()`
3. Implement the tool method (e.g., `_your_new_tool()`)
4. Update this documentation

### Testing New Features

```bash
# Run tests
pytest mcp/tests/

# Run with coverage
pytest --cov=mcp mcp/tests/
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Consult the main project documentation
4. Open an issue on GitHub: https://github.com/ronkoch2-code/code-standards-auditor

---

**Version**: 1.0.0  
**Last Updated**: January 2025

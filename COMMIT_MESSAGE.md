fix: Resolve missing dependencies and make MCP server robust

## Problems Fixed
1. **ModuleNotFoundError**: google.generativeai package was not installed
2. **Version Error**: tree-sitter-javascript==0.23.2 doesn't exist (latest is 0.23.1)
3. **Server Fragility**: Server would crash if any dependency was missing

## Solution
Made the MCP server resilient with graceful degradation:
- Server now starts even with missing services
- Provides stub implementations when services unavailable
- Reports service status clearly to users
- Continues operating with limited functionality

## Changes

### mcp/server.py
- Added comprehensive dependency checking at startup
- Implemented service stubs (GeminiServiceStub, Neo4jServiceStub, CacheServiceStub)
- Added detailed status reporting via 'check_status' tool
- Server runs with graceful degradation when services unavailable
- Better error messages with installation instructions

### requirements.txt
- Fixed tree-sitter-javascript version: 0.23.2 → 0.23.1

### New Files
- **install_mcp.sh**: Enhanced installation script with:
  - Package-by-package installation with error handling
  - Environment variable checking
  - Colored output for better UX
  - Automatic testing after installation
  
- **mcp/requirements_mcp.txt**: Minimal requirements for MCP server only

### mcp/test_server.py (Updated)
- Added colored terminal output for better readability
- Enhanced diagnostics for each component
- Generates specific installation commands for missing packages
- Tests service initialization
- Python version checking (3.8+ required)

### README.md
- Updated to version 1.0.3
- Added graceful degradation documentation
- Enhanced setup instructions
- Added troubleshooting notes

## Impact
- **Robustness**: Server no longer crashes on missing dependencies
- **User Experience**: Clear feedback about what's working/missing
- **Developer Experience**: Easy installation with helpful diagnostics
- **Flexibility**: Can run with partial functionality for testing

## Testing
Run the test script to see detailed diagnostics:
```bash
python3 mcp/test_server.py
```

The server will now start and report its status even if some services are unavailable. Use the 'check_status' tool in Claude to see which services are active.

Fixes: #2 - Google Generative AI import error, tree-sitter version mismatch
Type: bugfix, enhancement
Scope: mcp-integration, dependencies

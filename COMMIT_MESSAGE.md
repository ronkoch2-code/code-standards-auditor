fix: Resolve MCP server import error and update dependencies

## Problem
The MCP server was failing to start due to an import error:
- `ImportError: cannot import name 'LogLevel' from 'mcp.types'`
- The LogLevel class doesn't exist in the current MCP package version

## Solution
- Removed deprecated LogLevel import from mcp/server.py
- Updated MCP package version requirement from 0.1.0 to >=1.0.0
- Added comprehensive testing and setup scripts

## Changes
- **mcp/server.py**: Removed LogLevel from imports (not used in code)
- **requirements.txt**: Updated MCP package version to >=1.0.0
- **mcp/test_server.py**: Added test script to validate MCP server setup
- **setup_mcp.sh**: Created installation script for easy setup
- **README.md**: 
  - Added troubleshooting section for MCP server
  - Updated version history to v1.0.2
  - Enhanced MCP setup documentation

## Testing
- Created test_server.py to validate all imports and initialization
- Setup script checks for required environment variables
- Instructions added for manual testing

## Impact
- MCP server can now start successfully
- Claude Desktop integration is functional
- Better developer experience with setup automation

Fixes: MCP server startup failure
Type: bugfix
Scope: mcp-integration

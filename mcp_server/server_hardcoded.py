#!/usr/bin/env python3
"""
MCP Server Launcher - HARDCODED VERSION
This version doesn't rely on .env file at all - credentials are hardcoded
Use this if .env loading continues to fail
"""

import sys
import os
import asyncio
from pathlib import Path

# ALL OUTPUT MUST GO TO STDERR FOR MCP PROTOCOL!
def log_to_stderr(message):
    sys.stderr.write(f"[Launcher-Hardcoded] {message}\n")
    sys.stderr.flush()

log_to_stderr("Starting MCP Server...")

# HARDCODE THE CREDENTIALS HERE - no .env needed!
os.environ['NEO4J_PASSWORD'] = 'M@ry1and2'
os.environ['NEO4J_URI'] = 'bolt://localhost:7687'
os.environ['NEO4J_USER'] = 'neo4j'
os.environ['NEO4J_DATABASE'] = 'neo4j'  # Use default database for simplicity
os.environ['GEMINI_API_KEY'] = 'AIzaSyBlKf19Wl6PDRkcXXD22vmsg8En_lfixGM'

log_to_stderr("Environment variables set directly (no .env needed)")
log_to_stderr(f"NEO4J_PASSWORD is set ({len(os.environ['NEO4J_PASSWORD'])} chars)")

# Add paths for imports
launcher_file = Path(__file__).resolve()
mcp_server_dir = launcher_file.parent
project_root = mcp_server_dir.parent
server_dir = mcp_server_dir / 'server_impl'

sys.path.insert(0, str(server_dir))
sys.path.insert(0, str(project_root))

# Import and run the actual server
if __name__ == "__main__":
    try:
        from server import main
        log_to_stderr("Starting server with hardcoded credentials...")
        asyncio.run(main())
    except Exception as e:
        log_to_stderr(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)  # Send traceback to stderr too
        sys.exit(1)

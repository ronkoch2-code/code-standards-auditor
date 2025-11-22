#!/usr/bin/env python3
"""
MCP Server Launcher - FIXED VERSION
This version properly handles stdout/stderr to avoid breaking MCP protocol
"""

import sys
import os
import asyncio
from pathlib import Path
import logging

# Configure logging to go to stderr, not stdout (critical for MCP!)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Important: log to stderr, not stdout
)
logger = logging.getLogger(__name__)

# Suppress Neo4j debug output by setting log level
logging.getLogger('neo4j').setLevel(logging.WARNING)
logging.getLogger('neo4j.bolt').setLevel(logging.WARNING)
logging.getLogger('neo4j.pool').setLevel(logging.WARNING)
logging.getLogger('neo4j.io').setLevel(logging.WARNING)

# Set environment variables for credentials
os.environ['NEO4J_PASSWORD'] = 'M@ry1and2'
os.environ['NEO4J_URI'] = 'bolt://localhost:7687'
os.environ['NEO4J_USER'] = 'neo4j'
os.environ['NEO4J_DATABASE'] = 'code-standards'
os.environ['GEMINI_API_KEY'] = 'AIzaSyBlKf19Wl6PDRkcXXD22vmsg8En_lfixGM'

logger.debug("Environment variables set")

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
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)

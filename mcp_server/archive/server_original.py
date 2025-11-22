#!/usr/bin/env python3
"""
MCP Server Launcher for Code Standards Auditor
This file serves as the entry point for the MCP server.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the server_impl subdirectory to the path
server_dir = Path(__file__).parent / 'server_impl'
sys.path.insert(0, str(server_dir))

# Import and run the actual server
if __name__ == "__main__":
    from server import main
    asyncio.run(main())

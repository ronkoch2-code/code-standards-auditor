#!/usr/bin/env python3
"""
MCP Server Launcher for Code Standards Auditor
This file serves as the entry point for the MCP server.
FIXED: Explicitly loads .env file before starting server
"""

import sys
import os
import asyncio
from pathlib import Path

# CRITICAL: Load environment variables BEFORE importing anything else
# This ensures Neo4j credentials are available
project_root = Path(__file__).parent.parent
env_file = project_root / '.env'

if env_file.exists():
    # Load .env file manually to ensure it's loaded
    from dotenv import load_dotenv
    load_dotenv(env_file, override=True)
    print(f"[Launcher] Loaded .env from: {env_file}")
    
    # Debug: Print what we loaded (without showing password)
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    if neo4j_password:
        print(f"[Launcher] NEO4J_PASSWORD is set ({len(neo4j_password)} chars)")
    else:
        print("[Launcher] WARNING: NEO4J_PASSWORD not found in environment!")
else:
    print(f"[Launcher] No .env file found at: {env_file}")

# Add the server_impl subdirectory to the path
server_dir = Path(__file__).parent / 'server_impl'
sys.path.insert(0, str(server_dir))

# Add project root to path for imports
sys.path.insert(0, str(project_root))

# Import and run the actual server
if __name__ == "__main__":
    try:
        from server import main
        print("[Launcher] Starting MCP server...")
        asyncio.run(main())
    except Exception as e:
        print(f"[Launcher] Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

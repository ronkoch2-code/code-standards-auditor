#!/usr/bin/env python3
"""
MCP Server Launcher for Code Standards Auditor
ROBUST VERSION - with better error handling and debugging
"""

import sys
import os
import asyncio
from pathlib import Path

print("[Launcher] Starting MCP Server Launcher...")

# Get paths
launcher_file = Path(__file__).resolve()
mcp_server_dir = launcher_file.parent
project_root = mcp_server_dir.parent
env_file = project_root / '.env'

print(f"[Launcher] Project root: {project_root}")
print(f"[Launcher] Looking for .env at: {env_file}")

# Try to load .env file with better error handling
env_loaded = False
neo4j_password = None

if env_file.exists():
    print(f"[Launcher] .env file exists")
    
    # Try to import and use dotenv
    try:
        from dotenv import load_dotenv, dotenv_values
        print("[Launcher] python-dotenv imported successfully")
        
        # Method 1: load_dotenv
        result = load_dotenv(env_file, override=True)
        print(f"[Launcher] load_dotenv result: {result}")
        
        # Method 2: Also try dotenv_values to debug
        values = dotenv_values(env_file)
        print(f"[Launcher] Found {len(values)} variables in .env")
        
        # Check if password is loaded
        neo4j_password = os.getenv('NEO4J_PASSWORD')
        if neo4j_password:
            print(f"[Launcher] NEO4J_PASSWORD is set ({len(neo4j_password)} chars)")
            env_loaded = True
        else:
            print("[Launcher] NEO4J_PASSWORD not in environment")
            
            # Try from dotenv_values
            if 'NEO4J_PASSWORD' in values:
                neo4j_password = values['NEO4J_PASSWORD']
                os.environ['NEO4J_PASSWORD'] = neo4j_password
                print(f"[Launcher] Set NEO4J_PASSWORD from dotenv_values ({len(neo4j_password)} chars)")
                env_loaded = True
                
    except ImportError as e:
        print(f"[Launcher] ERROR: Cannot import python-dotenv: {e}")
        print("[Launcher] Install with: python3 -m pip install python-dotenv")
    except Exception as e:
        print(f"[Launcher] ERROR loading .env: {e}")
else:
    print(f"[Launcher] ERROR: .env file not found at {env_file}")

# If .env didn't load, try to set from hardcoded values as fallback
if not env_loaded:
    print("[Launcher] WARNING: Using fallback credentials")
    # Set the credentials directly
    os.environ['NEO4J_PASSWORD'] = 'M@ry1and2'
    os.environ['NEO4J_URI'] = 'bolt://localhost:7687'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_DATABASE'] = 'neo4j'  # Use default database
    print("[Launcher] Set fallback environment variables")

# Add paths for imports
server_dir = mcp_server_dir / 'server_impl'
sys.path.insert(0, str(server_dir))
sys.path.insert(0, str(project_root))

print(f"[Launcher] Added to sys.path: {server_dir}")
print(f"[Launcher] Added to sys.path: {project_root}")

# Import and run the actual server
if __name__ == "__main__":
    try:
        print("[Launcher] Importing server module...")
        from server import main
        print("[Launcher] Starting MCP server with main()...")
        asyncio.run(main())
    except ImportError as e:
        print(f"[Launcher] ERROR: Cannot import server: {e}")
        print(f"[Launcher] Check if server.py exists in: {server_dir}")
        sys.exit(1)
    except Exception as e:
        print(f"[Launcher] ERROR: Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

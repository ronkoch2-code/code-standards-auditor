#!/usr/bin/env python3
"""
Quick MCP Test - Basic functionality check
"""
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def main():
    print("=" * 60)
    print("  MCP Server Quick Test")  
    print("=" * 60)
    
    # Test 1: Environment variables
    print("\n1. Environment Variables:")
    gemini_key = os.environ.get('GEMINI_API_KEY')
    neo4j_pass = os.environ.get('NEO4J_PASSWORD')
    
    if gemini_key:
        print(f"   ✓ GEMINI_API_KEY: ***{gemini_key[-4:]}")
    else:
        print("   ✗ GEMINI_API_KEY: NOT SET")
    
    if neo4j_pass:
        print(f"   ✓ NEO4J_PASSWORD: ***{neo4j_pass[-4:]}")
    else:
        print("   ✗ NEO4J_PASSWORD: NOT SET")
    
    # Test 2: Critical imports
    print("\n2. Critical Packages:")
    try:
        import mcp.server
        print("   ✓ mcp")
    except ImportError:
        print("   ✗ mcp - Run: pip install mcp")
        
    try:
        import google.generativeai
        print("   ✓ google-generativeai")
    except ImportError:
        print("   ✗ google-generativeai - Run: pip install google-generativeai")
    
    try:
        import neo4j
        print("   ✓ neo4j")
    except ImportError:
        print("   ✗ neo4j - Run: pip install neo4j")
    
    # Test 3: Config file
    print("\n3. Configuration:")
    config_file = Path("mcp/mcp_config.json")
    if config_file.exists():
        print("   ✓ mcp_config.json exists")
        try:
            with open(config_file) as f:
                config = json.load(f)
            if 'mcpServers' in config:
                print("   ✓ Valid JSON structure")
            else:
                print("   ⚠ JSON missing mcpServers")
        except:
            print("   ✗ Invalid JSON")
    else:
        print("   ✗ mcp_config.json missing")
    
    # Test 4: Server import
    print("\n4. MCP Server:")
    try:
        # Set dummy env vars for import test
        if not os.environ.get("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = "test"
        if not os.environ.get("NEO4J_PASSWORD"):
            os.environ["NEO4J_PASSWORD"] = "test"
            
        from mcp.server import CodeAuditorMCPServer
        print("   ✓ Server class importable")
        
        server = CodeAuditorMCPServer()
        print("   ✓ Server instantiates")
    except Exception as e:
        print(f"   ✗ Server error: {e}")
    
    print("\n" + "=" * 60)
    print("To test with Claude Desktop:")
    print("1. Fix any ✗ issues above")
    print("2. cp mcp/mcp_config.json ~/Library/Application\\ Support/Claude/claude_desktop_config.json")
    print("3. Restart Claude Desktop")
    print("4. Look for MCP indicator in Claude")
    print("=" * 60)

if __name__ == "__main__":
    main()

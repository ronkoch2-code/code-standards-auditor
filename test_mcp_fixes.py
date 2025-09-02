#!/usr/bin/env python3
"""
Quick test script to verify MCP server Neo4j fixes
"""

import sys
import os
from pathlib import Path

# Add project path
sys.path.insert(0, '/Volumes/FS001/pythonscripts/code-standards-auditor')

def test_env_loading():
    """Test that environment variables are loaded correctly"""
    print("=== Testing Environment Variable Loading ===")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        env_file = Path('/Volumes/FS001/pythonscripts/code-standards-auditor/.env')
        if env_file.exists():
            load_dotenv(env_file)
            print("✓ Environment variables loaded from .env")
        else:
            print("✗ .env file not found")
            return False
    except ImportError:
        print("✗ python-dotenv not available")
        return False
    
    # Check required variables
    required_vars = ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 'NEO4J_DATABASE']
    all_set = True
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✓ {var}: {masked_value}")
        else:
            print(f"✗ {var}: NOT SET")
            all_set = False
    
    return all_set

def test_neo4j_service_creation():
    """Test that Neo4j service can be created with parameters"""
    print("\n=== Testing Neo4j Service Creation ===")
    
    try:
        from services.neo4j_service import Neo4jService
        
        # Try to create with parameters
        service = Neo4jService(
            uri=os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
            user=os.environ.get('NEO4J_USER', 'neo4j'),
            password=os.environ.get('NEO4J_PASSWORD', 'password123'),
            database=os.environ.get('NEO4J_DATABASE', 'neo4j')
        )
        print("✓ Neo4jService created successfully with parameters")
        return True
        
    except Exception as e:
        print(f"✗ Neo4jService creation failed: {e}")
        return False

def test_mcp_server_initialization():
    """Test that MCP server can be initialized"""
    print("\n=== Testing MCP Server Initialization ===")
    
    try:
        # Set dummy env vars if needed
        if not os.environ.get('GEMINI_API_KEY'):
            os.environ['GEMINI_API_KEY'] = 'test_key'
        
        from mcp.server import CodeAuditorMCPServer
        server = CodeAuditorMCPServer()
        print("✓ MCP Server initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ MCP Server initialization failed: {e}")
        return False

def main():
    print("Testing MCP Server Neo4j Fixes")
    print("=" * 50)
    
    # Run tests
    env_ok = test_env_loading()
    neo4j_ok = test_neo4j_service_creation()
    mcp_ok = test_mcp_server_initialization()
    
    # Summary
    print("\n=== Test Summary ===")
    if env_ok and neo4j_ok and mcp_ok:
        print("🎉 ALL TESTS PASSED! The fixes should work.")
        print("\nNext steps:")
        print("1. Start Neo4j: neo4j start")
        print("2. Test the MCP server: python3 mcp/server.py")
        print("3. Should see ✓ Neo4j in initialization summary")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        
        if not env_ok:
            print("- Environment variables not loading properly")
        if not neo4j_ok:
            print("- Neo4j service creation issues")
        if not mcp_ok:
            print("- MCP server initialization issues")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to verify MCP server can start and initialize properly
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_imports():
    """Test that all imports work correctly"""
    try:
        logger.info("Testing MCP imports...")
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import (
            Tool, 
            TextContent, 
            ImageContent,
            EmbeddedResource
        )
        logger.info("✓ MCP imports successful")
        return True
    except ImportError as e:
        logger.error(f"✗ MCP import failed: {e}")
        return False


async def test_service_imports():
    """Test that service imports work"""
    try:
        logger.info("Testing service imports...")
        
        # Mock environment variables if not set
        if not os.environ.get("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = "test_key_for_import_check"
        if not os.environ.get("NEO4J_PASSWORD"):
            os.environ["NEO4J_PASSWORD"] = "test_password"
        
        from services.gemini_service import GeminiService
        from services.neo4j_service import Neo4jService
        from services.cache_service import CacheService
        from config.settings import settings
        
        logger.info("✓ Service imports successful")
        return True
    except ImportError as e:
        logger.error(f"✗ Service import failed: {e}")
        return False


async def test_server_initialization():
    """Test that the MCP server can be initialized"""
    try:
        logger.info("Testing server initialization...")
        
        # Import the server class
        from mcp.server import CodeAuditorMCPServer
        
        # Try to create an instance
        server = CodeAuditorMCPServer()
        
        logger.info("✓ Server initialization successful")
        return True
    except Exception as e:
        logger.error(f"✗ Server initialization failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("Starting MCP Server Tests")
    logger.info("=" * 50)
    
    results = []
    
    # Run tests
    results.append(await test_imports())
    results.append(await test_service_imports())
    results.append(await test_server_initialization())
    
    # Summary
    logger.info("=" * 50)
    if all(results):
        logger.info("✓ All tests passed! The MCP server should be ready to run.")
        logger.info("\nTo start the server, run:")
        logger.info("  python3 /Volumes/FS001/pythonscripts/code-standards-auditor/mcp/server.py")
        return 0
    else:
        logger.error("✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

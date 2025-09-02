#!/usr/bin/env python3
"""
MCP Server Connection Test
Test the MCP server without actually starting it, focusing on dependency checks and configuration
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Test colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.WHITE):
    """Print colored message to console"""
    print(f"{color}{message}{Colors.RESET}")

def print_section(title):
    """Print a section header"""
    print()
    print_colored("=" * 60, Colors.CYAN)
    print_colored(f"  {title}", Colors.CYAN)
    print_colored("=" * 60, Colors.CYAN)

async def test_environment_setup():
    """Test environment variables and configuration"""
    print_section("Environment Configuration Test")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
            print_colored("✓ Environment file loaded", Colors.GREEN)
        else:
            print_colored("⚠ No .env file found", Colors.YELLOW)
    except ImportError:
        print_colored("⚠ python-dotenv not installed", Colors.YELLOW)
    
    # Check key environment variables
    env_vars = {
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY'),
        'NEO4J_PASSWORD': os.environ.get('NEO4J_PASSWORD'),
        'NEO4J_URI': os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
        'NEO4J_USER': os.environ.get('NEO4J_USER', 'neo4j'),
        'NEO4J_DATABASE': os.environ.get('NEO4J_DATABASE', 'neo4j'),
    }
    
    for var, value in env_vars.items():
        if value:
            if 'KEY' in var or 'PASSWORD' in var:
                print_colored(f"✓ {var}: ***{value[-4:]}", Colors.GREEN)
            else:
                print_colored(f"✓ {var}: {value}", Colors.GREEN)
        else:
            if var in ['GEMINI_API_KEY', 'NEO4J_PASSWORD']:
                print_colored(f"✗ {var}: NOT SET (required)", Colors.RED)
            else:
                print_colored(f"ℹ {var}: Using default", Colors.BLUE)
    
    return env_vars

async def test_package_imports():
    """Test critical package imports"""
    print_section("Package Import Tests")
    
    packages = {
        'mcp.server': 'mcp',
        'google.generativeai': 'google-generativeai', 
        'neo4j': 'neo4j',
        'redis': 'redis',
        'pydantic_settings': 'pydantic-settings',
        'dotenv': 'python-dotenv',
        'aiofiles': 'aiofiles'
    }
    
    results = {}
    missing_packages = []
    
    for import_name, package_name in packages.items():
        try:
            __import__(import_name)
            print_colored(f"✓ {package_name}", Colors.GREEN)
            results[package_name] = True
        except ImportError:
            print_colored(f"✗ {package_name}", Colors.RED)
            results[package_name] = False
            missing_packages.append(package_name)
    
    if missing_packages:
        print()
        print_colored("Missing packages can be installed with:", Colors.YELLOW)
        print_colored(f"pip install {' '.join(missing_packages)}", Colors.YELLOW)
        print_colored("Or use the requirements file:", Colors.YELLOW)
        print_colored("pip install -r mcp/requirements_mcp.txt", Colors.YELLOW)
    
    return results

async def test_service_initialization():
    """Test if services can be imported and initialized"""
    print_section("Service Initialization Tests")
    
    # Test settings import
    try:
        from config.settings import settings
        print_colored("✓ Settings module imported", Colors.GREEN)
        
        # Test if Neo4j is configured
        neo4j_configured = bool(settings.NEO4J_PASSWORD)
        if neo4j_configured:
            print_colored("✓ Neo4j configuration complete", Colors.GREEN)
        else:
            print_colored("⚠ Neo4j password not configured", Colors.YELLOW)
            
    except Exception as e:
        print_colored(f"✗ Settings import failed: {e}", Colors.RED)
        return False
    
    # Test service imports
    services_status = {}
    
    try:
        from services.gemini_service import GeminiService
        print_colored("✓ GeminiService importable", Colors.GREEN)
        services_status['gemini'] = True
    except Exception as e:
        print_colored(f"✗ GeminiService import failed: {e}", Colors.RED)
        services_status['gemini'] = False
    
    try:
        from services.neo4j_service import Neo4jService
        print_colored("✓ Neo4jService importable", Colors.GREEN)
        services_status['neo4j'] = True
    except Exception as e:
        print_colored(f"✗ Neo4jService import failed: {e}", Colors.RED)
        services_status['neo4j'] = False
    
    try:
        from services.cache_service import CacheService
        print_colored("✓ CacheService importable", Colors.GREEN)
        services_status['cache'] = True
    except Exception as e:
        print_colored(f"✗ CacheService import failed: {e}", Colors.RED)
        services_status['cache'] = False
    
    return services_status

async def test_mcp_server_class():
    """Test if the MCP server class can be instantiated"""
    print_section("MCP Server Class Test")
    
    try:
        # Set dummy environment variables if not set for testing
        if not os.environ.get("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = "test_key_dummy_for_import"
        if not os.environ.get("NEO4J_PASSWORD"):
            os.environ["NEO4J_PASSWORD"] = "test_password_dummy"
        
        from mcp.server import CodeAuditorMCPServer
        print_colored("✓ CodeAuditorMCPServer class importable", Colors.GREEN)
        
        # Try to instantiate (but don't run)
        server = CodeAuditorMCPServer()
        print_colored("✓ CodeAuditorMCPServer instantiated successfully", Colors.GREEN)
        
        # Test service initialization
        print_colored("Testing service initialization...", Colors.BLUE)
        status = await server.initialize_services()
        
        print()
        print_colored("Service Status:", Colors.BLUE)
        if status.get('initialized'):
            print_colored(f"✓ Initialized: {', '.join(status['initialized'])}", Colors.GREEN)
        if status.get('warnings'):
            print_colored(f"⚠ Warnings: {', '.join(status['warnings'])}", Colors.YELLOW)
        if status.get('failed'):
            print_colored(f"✗ Failed: {', '.join(status['failed'])}", Colors.RED)
        if status.get('missing_packages'):
            print_colored(f"✗ Missing: {', '.join(status['missing_packages'])}", Colors.RED)
        
        return status
        
    except Exception as e:
        print_colored(f"✗ MCP server test failed: {e}", Colors.RED)
        return None

async def test_claude_desktop_config():
    """Test if the Claude Desktop config exists and is valid"""
    print_section("Claude Desktop Configuration Test")
    
    config_file = Path("mcp/mcp_config.json")
    if not config_file.exists():
        print_colored("✗ mcp_config.json not found", Colors.RED)
        return False
    
    try:
        with open(config_file) as f:
            config = json.load(f)
        
        # Check if the config has the required structure
        if 'mcpServers' in config and 'code-standards-auditor' in config['mcpServers']:
            server_config = config['mcpServers']['code-standards-auditor']
            print_colored("✓ Valid MCP configuration found", Colors.GREEN)
            print_colored(f"  Command: {server_config.get('command')}", Colors.BLUE)
            print_colored(f"  Args: {server_config.get('args')}", Colors.BLUE)
            print_colored(f"  Capabilities: {server_config.get('capabilities')}", Colors.BLUE)
            return True
        else:
            print_colored("✗ Invalid MCP configuration structure", Colors.RED)
            return False
    except Exception as e:
        print_colored(f"✗ Failed to read MCP config: {e}", Colors.RED)
        return False

async def generate_setup_instructions():
    """Generate setup instructions for Claude Desktop"""
    print_section("Claude Desktop Setup Instructions")
    
    print_colored("To connect this MCP server to Claude Desktop:", Colors.YELLOW)
    print()
    print_colored("1. Copy the MCP configuration:", Colors.WHITE)
    print("   cp mcp/mcp_config.json ~/Library/Application\\ Support/Claude/claude_desktop_config.json")
    print()
    print_colored("2. Or manually edit your Claude Desktop config to include:", Colors.WHITE)
    print('   ~/.config/Claude/claude_desktop_config.json (Linux)')
    print('   ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)')
    print()
    print_colored("3. Restart Claude Desktop", Colors.WHITE)
    print()
    print_colored("4. Look for 'MCP' indicator in Claude Desktop", Colors.WHITE)
    print()
    print_colored("5. Available tools in Claude:", Colors.CYAN)
    print("   - check_status: Check server status")
    print("   - audit_code: Audit code against standards")
    print("   - get_standards: Retrieve coding standards")
    print()

async def main():
    """Run all tests"""
    print_colored("=" * 70, Colors.MAGENTA)
    print_colored("    Code Standards Auditor - MCP Server Connection Test", Colors.MAGENTA)
    print_colored("=" * 70, Colors.MAGENTA)
    
    # Run tests
    env_vars = await test_environment_setup()
    package_results = await test_package_imports()
    service_results = await test_service_initialization()
    server_status = await test_mcp_server_class()
    config_valid = await test_claude_desktop_config()
    
    # Generate summary
    print_section("Test Summary")
    
    critical_missing = []
    if not package_results.get('mcp', False):
        critical_missing.append('mcp package')
    
    if not env_vars.get('GEMINI_API_KEY'):
        critical_missing.append('GEMINI_API_KEY environment variable')
    
    if critical_missing:
        print_colored("✗ Critical issues found:", Colors.RED)
        for issue in critical_missing:
            print_colored(f"  - {issue}", Colors.RED)
        print()
        print_colored("Fix these issues before testing with Claude Desktop", Colors.YELLOW)
        return 1
    
    if server_status and server_status.get('all_ready', False):
        print_colored("🎉 MCP server is ready for Claude Desktop!", Colors.GREEN)
        print_colored("All services initialized successfully", Colors.GREEN)
    elif server_status:
        print_colored("⚠ MCP server can run with limited functionality", Colors.YELLOW)
        print_colored("Some services are using stubs", Colors.YELLOW)
    else:
        print_colored("✗ MCP server has critical issues", Colors.RED)
        return 1
    
    # Generate setup instructions
    await generate_setup_instructions()
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

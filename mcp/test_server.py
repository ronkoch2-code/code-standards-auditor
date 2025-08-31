#!/usr/bin/env python3
"""
Enhanced test script to verify MCP server dependencies and configuration
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
import subprocess

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes for terminal output
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
    print_colored(title, Colors.CYAN)
    print_colored("=" * 60, Colors.CYAN)


async def check_python_version():
    """Check if Python version is adequate"""
    import sys
    version = sys.version_info
    print_section("Python Version Check")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored(f"✗ Python 3.8+ required (found {version.major}.{version.minor})", Colors.RED)
        return False
    else:
        print_colored(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK", Colors.GREEN)
        return True


async def test_package_import(package_name, import_name=None, critical=True):
    """Test if a package can be imported"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print_colored(f"✓ {package_name} - Installed", Colors.GREEN)
        return True
    except ImportError as e:
        if critical:
            print_colored(f"✗ {package_name} - NOT INSTALLED", Colors.RED)
            print_colored(f"  Install with: pip install {package_name}", Colors.YELLOW)
        else:
            print_colored(f"⚠ {package_name} - Optional, not installed", Colors.YELLOW)
        return False


async def test_critical_imports():
    """Test that critical imports work correctly"""
    print_section("Critical Package Checks")
    
    results = {}
    
    # Check MCP
    results['mcp'] = await test_package_import('mcp', 'mcp.server')
    
    # Check Google Generative AI
    results['gemini'] = await test_package_import(
        'google-generativeai', 
        'google.generativeai'
    )
    
    # Check Neo4j
    results['neo4j'] = await test_package_import('neo4j')
    
    # Check Redis
    results['redis'] = await test_package_import('redis')
    
    # Check Pydantic Settings
    results['pydantic_settings'] = await test_package_import(
        'pydantic-settings',
        'pydantic_settings'
    )
    
    # Check other important packages
    print()
    print_colored("Optional packages:", Colors.BLUE)
    await test_package_import('anthropic', critical=False)
    await test_package_import('aiofiles', critical=False)
    await test_package_import('structlog', critical=False)
    
    return results


async def test_environment_variables():
    """Test that required environment variables are set"""
    print_section("Environment Variables Check")
    
    env_vars = {
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY'),
        'NEO4J_PASSWORD': os.environ.get('NEO4J_PASSWORD'),
        'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
    }
    
    all_set = True
    for var, value in env_vars.items():
        if var == 'ANTHROPIC_API_KEY':  # Optional
            if value:
                print_colored(f"✓ {var} - Set", Colors.GREEN)
            else:
                print_colored(f"ℹ {var} - Not set (optional)", Colors.BLUE)
        else:
            if value:
                print_colored(f"✓ {var} - Set", Colors.GREEN)
            else:
                print_colored(f"✗ {var} - NOT SET", Colors.RED)
                print_colored(f"  Set with: export {var}='your_value'", Colors.YELLOW)
                all_set = False
    
    return all_set


async def test_mcp_server_imports():
    """Test that the MCP server can import its dependencies"""
    print_section("MCP Server Import Test")
    
    try:
        # Set dummy environment variables if not set
        if not os.environ.get("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = "test_key_for_import_check"
        if not os.environ.get("NEO4J_PASSWORD"):
            os.environ["NEO4J_PASSWORD"] = "test_password"
        
        # Try to import the server
        from mcp.server import CodeAuditorMCPServer
        
        print_colored("✓ MCP server imports successful", Colors.GREEN)
        
        # Try to create an instance
        server = CodeAuditorMCPServer()
        print_colored("✓ MCP server instantiation successful", Colors.GREEN)
        
        return True
    except ImportError as e:
        print_colored(f"✗ MCP server import failed: {e}", Colors.RED)
        return False
    except Exception as e:
        print_colored(f"✗ MCP server initialization failed: {e}", Colors.RED)
        return False


async def test_server_startup():
    """Test if the server can start (brief test)"""
    print_section("Server Startup Test")
    
    try:
        from mcp.server import CodeAuditorMCPServer
        
        server = CodeAuditorMCPServer()
        status = await server.initialize_services()
        
        if status['all_ready']:
            print_colored("✓ All services initialized successfully", Colors.GREEN)
        else:
            if status['initialized']:
                print_colored(f"✓ Initialized: {', '.join(status['initialized'])}", Colors.GREEN)
            if status.get('warnings'):
                print_colored(f"⚠ Using stubs: {', '.join(status['warnings'])}", Colors.YELLOW)
            if status['failed']:
                print_colored(f"✗ Failed: {', '.join(status['failed'])}", Colors.RED)
            if status['missing_packages']:
                print_colored(f"✗ Missing: {', '.join(status['missing_packages'])}", Colors.RED)
        
        return True
    except Exception as e:
        print_colored(f"✗ Server startup test failed: {e}", Colors.RED)
        return False


def generate_install_commands(missing_packages):
    """Generate installation commands for missing packages"""
    if not missing_packages:
        return
    
    print_section("Installation Instructions")
    
    print_colored("To install missing packages, run:", Colors.YELLOW)
    print()
    
    # Individual commands
    print_colored("Option 1 - Install individually:", Colors.BLUE)
    for pkg, installed in missing_packages.items():
        if not installed:
            if pkg == 'gemini':
                print(f"  pip install google-generativeai")
            elif pkg == 'pydantic_settings':
                print(f"  pip install pydantic-settings")
            else:
                print(f"  pip install {pkg}")
    
    print()
    print_colored("Option 2 - Install all at once:", Colors.BLUE)
    packages = []
    for pkg, installed in missing_packages.items():
        if not installed:
            if pkg == 'gemini':
                packages.append("google-generativeai")
            elif pkg == 'pydantic_settings':
                packages.append("pydantic-settings")
            else:
                packages.append(pkg)
    
    if packages:
        print(f"  pip install {' '.join(packages)}")
    
    print()
    print_colored("Option 3 - Use requirements file:", Colors.BLUE)
    print("  pip install -r /Volumes/FS001/pythonscripts/code-standards-auditor/mcp/requirements_mcp.txt")


async def main():
    """Run all tests"""
    print_colored("=" * 60, Colors.MAGENTA)
    print_colored("  Code Standards Auditor - MCP Server Test Suite", Colors.MAGENTA)
    print_colored("=" * 60, Colors.MAGENTA)
    
    all_passed = True
    
    # Check Python version
    if not await check_python_version():
        print_colored("\n✗ Python version check failed", Colors.RED)
        return 1
    
    # Check critical packages
    package_results = await test_critical_imports()
    missing_packages = {k: v for k, v in package_results.items() if not v}
    
    if missing_packages:
        all_passed = False
    
    # Check environment variables
    env_ok = await test_environment_variables()
    if not env_ok:
        all_passed = False
    
    # Test MCP server imports
    if package_results.get('mcp', False):
        import_ok = await test_mcp_server_imports()
        if import_ok:
            await test_server_startup()
    
    # Generate installation instructions if needed
    if missing_packages:
        generate_install_commands(package_results)
    
    # Final summary
    print_section("Test Summary")
    
    if all_passed and not missing_packages:
        print_colored("✓ All tests passed! The MCP server is ready to run.", Colors.GREEN)
        print()
        print_colored("To start the server:", Colors.BLUE)
        print("  python3 /Volumes/FS001/pythonscripts/code-standards-auditor/mcp/server.py")
        print()
        print_colored("To configure Claude Desktop:", Colors.BLUE)
        print("  cp mcp/mcp_config.json ~/Library/Application\\ Support/Claude/claude_desktop_config.json")
        return 0
    else:
        if missing_packages:
            print_colored("✗ Some packages are missing. Please install them first.", Colors.RED)
        else:
            print_colored("⚠ Server can run with limited functionality.", Colors.YELLOW)
            print_colored("  Some services may not be available.", Colors.YELLOW)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

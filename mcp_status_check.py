#!/usr/bin/env python3
"""
MCP Server Status Check Script
Quick verification of MCP server dependencies and configuration
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project path
sys.path.insert(0, '/Volumes/FS001/pythonscripts/code-standards-auditor')

def print_header(title):
    print("=" * 60)
    print(title)
    print("=" * 60)

def main():
    print_header("MCP Server Status Check")
    print()

    # Test 1: Check Python version
    version = sys.version_info
    print(f"✓ Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ WARNING: Python 3.8+ is recommended")
    
    print()

    # Test 2: Check critical imports
    critical_packages = [
        ('mcp.server', 'mcp', 'MCP Protocol'),
        ('google.generativeai', 'google-generativeai', 'Google Gemini API'),
        ('neo4j', 'neo4j', 'Neo4j Database'),
        ('redis', 'redis', 'Redis Cache'),
        ('pydantic_settings', 'pydantic-settings', 'Pydantic Settings')
    ]

    missing_packages = []
    print("Package Dependencies:")
    
    for import_name, pip_name, description in critical_packages:
        try:
            __import__(import_name)
            print(f"  ✓ {description} ({pip_name})")
        except ImportError as e:
            print(f"  ✗ {description} ({pip_name}) - NOT INSTALLED")
            missing_packages.append(pip_name)

    print()

    # Test 3: Check environment variables
    env_vars = {
        'GEMINI_API_KEY': 'Required for Google Gemini API',
        'NEO4J_PASSWORD': 'Required for Neo4j database',
        'ANTHROPIC_API_KEY': 'Optional fallback API',
    }
    
    print("Environment Variables:")
    missing_env = []
    
    for var, description in env_vars.items():
        value = os.environ.get(var)
        if value:
            # Don't show the actual value for security
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  ✓ {var}: {masked_value} ({description})")
        else:
            if var == 'ANTHROPIC_API_KEY':
                print(f"  ℹ {var}: Not set ({description})")
            else:
                print(f"  ✗ {var}: NOT SET ({description})")
                missing_env.append(var)

    print()

    # Test 4: Check project files
    print("Project Structure:")
    project_files = [
        '/Volumes/FS001/pythonscripts/code-standards-auditor/mcp/server.py',
        '/Volumes/FS001/pythonscripts/code-standards-auditor/mcp/mcp_config.json',
        '/Volumes/FS001/pythonscripts/code-standards-auditor/config/settings.py',
        '/Volumes/FS001/pythonscripts/code-standards-auditor/.env'
    ]
    
    for file_path in project_files:
        if Path(file_path).exists():
            print(f"  ✓ {Path(file_path).name}")
        else:
            print(f"  ✗ {Path(file_path).name} - Missing")
            if file_path.endswith('.env'):
                print(f"    (Copy from .env.example and configure)")

    print()

    # Test 5: Try to import the MCP server
    print("MCP Server Test:")
    try:
        # Temporarily set dummy env vars for import test
        original_env = {}
        test_vars = {'GEMINI_API_KEY': 'test_key', 'NEO4J_PASSWORD': 'test_password'}
        
        for var, value in test_vars.items():
            if not os.environ.get(var):
                original_env[var] = os.environ.get(var)
                os.environ[var] = value
        
        from mcp.server import CodeAuditorMCPServer
        print("  ✓ MCP Server class imported successfully")
        
        server = CodeAuditorMCPServer()
        print("  ✓ MCP Server instance created successfully")
        
        # Restore original environment
        for var, original_value in original_env.items():
            if original_value is None:
                del os.environ[var]
            else:
                os.environ[var] = original_value
                
    except ImportError as e:
        print(f"  ✗ MCP Server import failed: {e}")
    except Exception as e:
        print(f"  ✗ MCP Server creation failed: {e}")

    print()

    # Summary and recommendations
    print_header("Status Summary & Recommendations")
    
    total_issues = len(missing_packages) + len([v for v in missing_env if v != 'ANTHROPIC_API_KEY'])
    
    if total_issues == 0:
        print("🎉 ALL CHECKS PASSED! Your MCP server is ready to run.")
        print()
        print("To start the MCP server:")
        print("  python3 /Volumes/FS001/pythonscripts/code-standards-auditor/mcp/server.py")
        print()
        print("To configure Claude Desktop:")
        print("  cp mcp/mcp_config.json ~/Library/Application\\ Support/Claude/claude_desktop_config.json")
    else:
        print(f"⚠️  Found {total_issues} issues that need attention:")
        
        if missing_packages:
            print()
            print("Missing packages (install with pip):")
            for package in missing_packages:
                print(f"  pip install {package}")
            print("\nOr install all at once:")
            print(f"  pip install {' '.join(missing_packages)}")
        
        if missing_env:
            print()
            print("Missing environment variables:")
            for var in missing_env:
                print(f"  export {var}='your_value_here'")
            print("\nOr add to .env file in project root")

    print()
    print("For detailed setup instructions, see:")
    print("  /Volumes/FS001/pythonscripts/code-standards-auditor/mcp/README.md")

if __name__ == "__main__":
    main()

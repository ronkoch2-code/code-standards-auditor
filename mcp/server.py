"""
MCP Server for Code Standards Auditor
Robust version with graceful handling of missing dependencies
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for required packages before importing
MISSING_PACKAGES = []
INSTALL_COMMANDS = []

# Check MCP package
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool, 
        TextContent, 
        ImageContent,
        EmbeddedResource
    )
    MCP_AVAILABLE = True
except ImportError as e:
    MCP_AVAILABLE = False
    MISSING_PACKAGES.append("mcp")
    INSTALL_COMMANDS.append("pip install mcp")
    logger.error(f"MCP package not found: {e}")

# Service availability flags
SERVICE_AVAILABLE = {
    'gemini': False,
    'neo4j': False,
    'cache': False,
    'settings': False
}

# Stub classes for when services are not available
class GeminiServiceStub:
    """Stub for when Gemini service is not available"""
    def __init__(self):
        logger.warning("Using GeminiServiceStub - Gemini API not available")
    
    async def analyze_code(self, *args, **kwargs):
        return {
            "error": "Gemini service not available. Please install google-generativeai",
            "install_command": "pip install google-generativeai"
        }

class Neo4jServiceStub:
    """Stub for when Neo4j service is not available"""
    def __init__(self):
        logger.warning("Using Neo4jServiceStub - Neo4j not available")
    
    async def initialize(self):
        pass
    
    async def get_standards(self, *args, **kwargs):
        return []
    
    async def record_violations(self, *args, **kwargs):
        pass

class CacheServiceStub:
    """Stub for when Cache service is not available"""
    def __init__(self):
        logger.warning("Using CacheServiceStub - Redis not available")
    
    async def get_audit_result(self, *args, **kwargs):
        return None
    
    async def set_audit_result(self, *args, **kwargs):
        pass

# Try to import services with graceful fallback
try:
    import google.generativeai as genai
    from services.gemini_service import GeminiService
    SERVICE_AVAILABLE['gemini'] = True
except ImportError as e:
    MISSING_PACKAGES.append("google-generativeai")
    INSTALL_COMMANDS.append("pip install google-generativeai")
    GeminiService = GeminiServiceStub
    logger.warning(f"Gemini service unavailable: {e}")

try:
    from services.neo4j_service import Neo4jService
    SERVICE_AVAILABLE['neo4j'] = True
except ImportError as e:
    MISSING_PACKAGES.append("neo4j")
    INSTALL_COMMANDS.append("pip install neo4j")
    Neo4jService = Neo4jServiceStub
    logger.warning(f"Neo4j service unavailable: {e}")

try:
    from services.cache_service import CacheService
    SERVICE_AVAILABLE['cache'] = True
except ImportError as e:
    MISSING_PACKAGES.append("redis")
    INSTALL_COMMANDS.append("pip install redis")
    CacheService = CacheServiceStub
    logger.warning(f"Cache service unavailable: {e}")

try:
    from config.settings import settings
    SERVICE_AVAILABLE['settings'] = True
except ImportError as e:
    logger.warning(f"Settings module unavailable: {e}")
    # Create minimal settings
    class Settings:
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
        NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")
        NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
        ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    settings = Settings()


class CodeAuditorMCPServer:
    """MCP Server implementation for Code Standards Auditor"""
    
    def __init__(self):
        if not MCP_AVAILABLE:
            logger.error("=" * 60)
            logger.error("CRITICAL: MCP package is not installed!")
            logger.error("Please run: pip install mcp")
            logger.error("=" * 60)
            raise RuntimeError("MCP package is required but not installed")
            
        self.server = Server("code-standards-auditor")
        self.gemini_service = None
        self.neo4j_service = None
        self.cache_service = None
        self.service_status = {}
        self._setup_handlers()
    
    async def initialize_services(self):
        """Initialize all required services"""
        initialized = []
        failed = []
        warnings = []
        
        # Check for missing packages first
        if MISSING_PACKAGES:
            logger.warning("=" * 60)
            logger.warning("The following packages are missing:")
            for pkg in MISSING_PACKAGES:
                logger.warning(f"  - {pkg}")
            logger.warning("")
            logger.warning("To install all missing packages, run:")
            logger.warning(f"  pip install {' '.join(MISSING_PACKAGES)}")
            logger.warning("=" * 60)
        
        # Initialize Gemini service
        try:
            self.gemini_service = GeminiService()
            if SERVICE_AVAILABLE['gemini']:
                initialized.append("Gemini")
            else:
                warnings.append("Gemini (using stub)")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            failed.append(f"Gemini: {e}")
            self.gemini_service = GeminiServiceStub()
        
        # Initialize Neo4j service
        try:
            self.neo4j_service = Neo4jService()
            if hasattr(self.neo4j_service, 'initialize'):
                await self.neo4j_service.initialize()
            if SERVICE_AVAILABLE['neo4j']:
                initialized.append("Neo4j")
            else:
                warnings.append("Neo4j (using stub)")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j service: {e}")
            failed.append(f"Neo4j: {e}")
            self.neo4j_service = Neo4jServiceStub()
        
        # Initialize Cache service
        try:
            self.cache_service = CacheService()
            if SERVICE_AVAILABLE['cache']:
                initialized.append("Cache")
            else:
                warnings.append("Cache (using stub)")
        except Exception as e:
            logger.error(f"Failed to initialize Cache service: {e}")
            failed.append(f"Cache: {e}")
            self.cache_service = CacheServiceStub()
        
        # Store status
        self.service_status = {
            'initialized': initialized,
            'failed': failed,
            'warnings': warnings,
            'missing_packages': MISSING_PACKAGES,
            'all_ready': len(failed) == 0 and len(MISSING_PACKAGES) == 0
        }
        
        logger.info("=" * 60)
        logger.info("Service Initialization Summary:")
        if initialized:
            logger.info(f"✓ Initialized: {', '.join(initialized)}")
        if warnings:
            logger.warning(f"⚠ Using stubs: {', '.join(warnings)}")
        if failed:
            logger.error(f"✗ Failed: {', '.join(failed)}")
        logger.info("=" * 60)
        
        return self.service_status
    
    def _setup_handlers(self):
        """Setup MCP protocol handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools for Claude Desktop"""
            tools = []
            
            # Always provide diagnostic tool
            tools.append(Tool(
                name="check_status",
                description="Check the status of the Code Standards Auditor services and get installation instructions",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ))
            
            # Add audit tools based on service availability
            if SERVICE_AVAILABLE['gemini'] or isinstance(self.gemini_service, GeminiServiceStub):
                tools.append(Tool(
                    name="audit_code",
                    description="Audit code against coding standards (requires Gemini service)",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Source code to audit"
                            },
                            "language": {
                                "type": "string",
                                "enum": ["python", "java", "javascript", "general"],
                                "description": "Programming language"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "Optional project identifier"
                            }
                        },
                        "required": ["code", "language"]
                    }
                ))
            
            tools.append(Tool(
                name="get_standards",
                description="Retrieve coding standards documentation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["python", "java", "javascript", "general"],
                            "description": "Programming language"
                        }
                    },
                    "required": ["language"]
                }
            ))
            
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls from Claude Desktop"""
            
            try:
                if name == "check_status":
                    result = await self._check_status()
                elif name == "audit_code":
                    result = await self._audit_code(arguments)
                elif name == "get_standards":
                    result = await self._get_standards(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(
                    type="text", 
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "status": self.service_status
                    }, indent=2)
                )]
    
    async def _check_status(self) -> Dict[str, Any]:
        """Check the status of all services"""
        status = {
            "server": "running",
            "services": self.service_status,
            "environment": {
                "gemini_api_key_set": bool(settings.GEMINI_API_KEY),
                "neo4j_password_set": bool(settings.NEO4J_PASSWORD),
                "anthropic_api_key_set": bool(getattr(settings, 'ANTHROPIC_API_KEY', ''))
            }
        }
        
        if MISSING_PACKAGES:
            status["installation_required"] = {
                "missing_packages": MISSING_PACKAGES,
                "install_command": f"pip install {' '.join(MISSING_PACKAGES)}",
                "or_use_requirements": "pip install -r /Volumes/FS001/pythonscripts/code-standards-auditor/mcp/requirements_mcp.txt"
            }
        
        return status
    
    async def _audit_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Audit code implementation"""
        if not SERVICE_AVAILABLE['gemini']:
            return {
                "error": "Gemini service not available",
                "reason": "google-generativeai package is not installed",
                "solution": "Run: pip install google-generativeai",
                "status": self.service_status
            }
        
        code = args.get("code")
        language = args.get("language")
        project_id = args.get("project_id", "default")
        
        # Basic validation without Gemini
        if not code:
            return {"error": "No code provided"}
        
        # Try to use Gemini service
        if hasattr(self.gemini_service, 'analyze_code'):
            try:
                result = await self.gemini_service.analyze_code(
                    code=code,
                    language=language,
                    context={"project_id": project_id}
                )
                return result
            except Exception as e:
                return {
                    "error": f"Analysis failed: {str(e)}",
                    "fallback": "Using basic analysis",
                    "basic_stats": {
                        "lines": len(code.split('\n')),
                        "characters": len(code),
                        "language": language
                    }
                }
        
        return {
            "message": "Code audit service initializing",
            "code_preview": code[:100] + "..." if len(code) > 100 else code,
            "language": language
        }
    
    async def _get_standards(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve coding standards"""
        language = args.get("language")
        
        # Try to read from file system
        standards_file = Path(f"/Volumes/FS001/pythonscripts/standards/{language}/coding_standards_v1.0.0.md")
        file_content = ""
        
        if standards_file.exists():
            try:
                file_content = standards_file.read_text()
                return {
                    "language": language,
                    "documentation": file_content,
                    "source": "file_system"
                }
            except Exception as e:
                logger.error(f"Failed to read standards file: {e}")
        
        # Fallback to Neo4j if available
        if SERVICE_AVAILABLE['neo4j'] and self.neo4j_service:
            try:
                standards = await self.neo4j_service.get_standards(language=language)
                return {
                    "language": language,
                    "rules": standards,
                    "source": "neo4j"
                }
            except Exception as e:
                logger.error(f"Failed to get standards from Neo4j: {e}")
        
        # Return basic standards
        return {
            "language": language,
            "message": "Standards service initializing",
            "basic_standards": {
                "naming": "Use descriptive names",
                "formatting": "Follow language conventions",
                "documentation": "Document all public interfaces"
            }
        }
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Code Standards Auditor MCP Server...")
        
        # Initialize services
        status = await self.initialize_services()
        
        if not status['all_ready']:
            logger.warning("=" * 60)
            logger.warning("Server starting with limited functionality")
            logger.warning("Some services are not available")
            logger.warning("Run 'check_status' tool in Claude for details")
            logger.warning("=" * 60)
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = CodeAuditorMCPServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        if MISSING_PACKAGES:
            logger.error("=" * 60)
            logger.error("Missing packages detected!")
            logger.error("Please run the following command:")
            logger.error(f"  pip install {' '.join(MISSING_PACKAGES)}")
            logger.error("=" * 60)
        sys.exit(1)

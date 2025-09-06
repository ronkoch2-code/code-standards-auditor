"""
MCP Server for Code Standards Auditor
Clean version with complete stdout protection
"""

import asyncio
import json
import logging
import sys
import os
import io
from typing import Dict, List, Optional, Any
from pathlib import Path

# Configure logging FIRST - MUST go to stderr for MCP protocol!
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,  # Critical: MCP requires stdout to be pure JSON
    force=True  # Force reconfiguration of all loggers
)
logger = logging.getLogger(__name__)

# Suppress ALL other loggers that might write to stdout
for name in ['neo4j', 'neo4j.bolt', 'neo4j.pool', 'neo4j.io', 'httpx', 'httpcore', 'structlog']:
    logging.getLogger(name).setLevel(logging.ERROR)
    logging.getLogger(name).propagate = False

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded environment variables from {env_file}")
except ImportError:
    pass

# Check for required packages before importing
MISSING_PACKAGES = []

# Check MCP package
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError as e:
    MCP_AVAILABLE = False
    MISSING_PACKAGES.append("mcp")
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
    
    async def connect(self):
        pass
    
    async def get_standards(self, *args, **kwargs):
        return []

class CacheServiceStub:
    """Stub for when Cache service is not available"""
    def __init__(self):
        logger.warning("Using CacheServiceStub - Redis not available")
    
    async def get_audit_result(self, *args, **kwargs):
        return None
    
    async def set_audit_result(self, *args, **kwargs):
        pass

# Completely silence stdout during imports
_original_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
    # Try to import services
    try:
        import google.generativeai as genai
        from services.gemini_service import GeminiService
        SERVICE_AVAILABLE['gemini'] = True
    except ImportError:
        MISSING_PACKAGES.append("google-generativeai")
        GeminiService = GeminiServiceStub
    
    try:
        from services.neo4j_service import Neo4jService
        SERVICE_AVAILABLE['neo4j'] = True
    except ImportError:
        MISSING_PACKAGES.append("neo4j")
        Neo4jService = Neo4jServiceStub
    
    try:
        from services.cache_service import CacheService
        SERVICE_AVAILABLE['cache'] = True
    except ImportError:
        MISSING_PACKAGES.append("redis")
        CacheService = CacheServiceStub
    
    try:
        from config.settings import settings
        SERVICE_AVAILABLE['settings'] = True
    except ImportError:
        # Create minimal settings
        class Settings:
            GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
            NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")
            NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
            NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
            NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "code-standards")
            ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
        settings = Settings()
finally:
    # Restore stdout temporarily
    sys.stdout = _original_stdout


class CodeAuditorMCPServer:
    """MCP Server implementation for Code Standards Auditor"""
    
    def __init__(self):
        if not MCP_AVAILABLE:
            logger.error("CRITICAL: MCP package is not installed!")
            raise RuntimeError("MCP package is required but not installed")
            
        self.server = Server("code-standards-auditor")
        self.gemini_service = None
        self.neo4j_service = None
        self.cache_service = None
        self.service_status = {}
        self._setup_handlers()
    
    async def initialize_services(self):
        """Initialize all required services"""
        # Silence stdout during initialization
        _saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            initialized = []
            failed = []
            warnings = []
            
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
                if SERVICE_AVAILABLE['neo4j']:
                    databases_to_try = ["code-standards", "neo4j"]
                    connected = False
                    
                    for db_name in databases_to_try:
                        try:
                            self.neo4j_service = Neo4jService(
                                uri=settings.NEO4J_URI,
                                user=settings.NEO4J_USER,
                                password=settings.NEO4J_PASSWORD,
                                database=db_name
                            )
                            await self.neo4j_service.connect()
                            initialized.append(f"Neo4j (database: {db_name})")
                            connected = True
                            break
                        except Exception as db_error:
                            logger.warning(f"Could not connect to database '{db_name}': {db_error}")
                            continue
                    
                    if not connected:
                        raise Exception("Could not connect to any Neo4j database")
                else:
                    self.neo4j_service = Neo4jServiceStub()
                    warnings.append("Neo4j (package missing - using stub)")
                    
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
            
        finally:
            # Restore stdout
            sys.stdout = _saved_stdout
    
    def _setup_handlers(self):
        """Setup MCP protocol handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools for Claude Desktop"""
            tools = []
            
            tools.append(Tool(
                name="check_status",
                description="Check the status of the Code Standards Auditor services",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ))
            
            tools.append(Tool(
                name="audit_code",
                description="Audit code against coding standards",
                inputSchema={
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
                inputSchema={
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
        
        @self.server.list_prompts()
        async def list_prompts():
            """List available prompts (currently empty)"""
            return []
        
        @self.server.list_resources()
        async def list_resources():
            """List available resources (currently empty)"""
            return []
        
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
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    async def _check_status(self) -> Dict[str, Any]:
        """Check service status"""
        return {
            "status": "operational" if self.service_status.get('all_ready') else "limited",
            "services": {
                "initialized": self.service_status.get('initialized', []),
                "failed": self.service_status.get('failed', []),
                "warnings": self.service_status.get('warnings', [])
            },
            "missing_packages": self.service_status.get('missing_packages', []),
            "message": "All services operational" if self.service_status.get('all_ready') 
                      else "Some services unavailable - check missing_packages"
        }
    
    async def _audit_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Audit code against standards"""
        code = args.get("code", "")
        language = args.get("language", "python")
        
        if SERVICE_AVAILABLE['gemini'] and self.gemini_service:
            try:
                result = await self.gemini_service.analyze_code(
                    code=code,
                    language=language
                )
                return result
            except Exception as e:
                logger.error(f"Gemini analysis failed: {e}")
                return {
                    "error": f"Analysis failed: {e}",
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
        logger.info("Starting Code Standards Auditor MCP Server (Clean Version)...")
        
        # Initialize services
        status = await self.initialize_services()
        
        if not status['all_ready']:
            logger.warning("Server starting with limited functionality")
        
        # CRITICAL: Redirect stdout to stderr BEFORE starting MCP protocol
        # This ensures absolutely no output goes to stdout during JSON-RPC communication
        class StderrRedirector:
            def write(self, data):
                sys.stderr.write(f"[REDIRECTED]: {data}")
                sys.stderr.flush()
            def flush(self):
                sys.stderr.flush()
            def fileno(self):
                return sys.stderr.fileno()
            
        # Save original stdout for MCP to use
        original_stdout = sys.stdout
        
        # Create a clean stdout for MCP that captures any accidental writes
        class CleanStdout:
            def __init__(self):
                self.buffer = original_stdout.buffer if hasattr(original_stdout, 'buffer') else self
                self._original = original_stdout
                
            def write(self, data):
                # Only allow JSON-RPC messages (they start with '{')
                if isinstance(data, str) and data.strip() and data.strip()[0] == '{':
                    return self._original.write(data)
                # Redirect everything else to stderr
                if data.strip():  # Only log non-empty data
                    sys.stderr.write(f"[BLOCKED]: {data}")
                    sys.stderr.flush()
                return len(data)
                
            def flush(self):
                self._original.flush()
                
            def fileno(self):
                return self._original.fileno()
                
            def readable(self):
                return False
                
            def writable(self):
                return True
                
            def seekable(self):
                return False
        
        # Install the clean stdout
        sys.stdout = CleanStdout()
        
        try:
            # Run the server with clean stdout
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        finally:
            # Restore original stdout
            sys.stdout = original_stdout


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
        sys.exit(1)

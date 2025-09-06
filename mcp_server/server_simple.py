#!/usr/bin/env python3
"""
Simplified MCP Server for Code Standards Auditor
Version 3.0 - Clean architecture without embedded Neo4j
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded environment variables from {env_file}")
except ImportError:
    logger.info("Using system environment variables")

# Import MCP components
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError as e:
    logger.error(f"MCP package not found: {e}")
    logger.error("Please install: pip install mcp")
    sys.exit(1)

# Try to import Gemini service
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini not available. Install with: pip install google-generativeai")


class SimpleCodeAuditorServer:
    """Simplified MCP Server for Code Standards Auditor"""
    
    def __init__(self):
        self.server = Server("code-standards-auditor-simple")
        self.standards_dir = Path("/Volumes/FS001/pythonscripts/standards")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP protocol handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            tools = []
            
            tools.append(Tool(
                name="check_status",
                description="Check the status of the Code Standards Auditor",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ))
            
            tools.append(Tool(
                name="get_standards",
                description="Get coding standards from local files",
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
            
            if GEMINI_AVAILABLE:
                tools.append(Tool(
                    name="analyze_code",
                    description="Analyze code using Gemini AI",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to analyze"
                            },
                            "language": {
                                "type": "string",
                                "description": "Programming language"
                            },
                            "focus": {
                                "type": "string",
                                "description": "Analysis focus (quality, security, performance)",
                                "enum": ["quality", "security", "performance", "all"]
                            }
                        },
                        "required": ["code", "language"]
                    }
                ))
            
            tools.append(Tool(
                name="save_standard",
                description="Save a new or updated coding standard",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "description": "Programming language"
                        },
                        "category": {
                            "type": "string",
                            "description": "Standard category"
                        },
                        "content": {
                            "type": "string",
                            "description": "Standard content in markdown"
                        },
                        "filename": {
                            "type": "string",
                            "description": "Filename for the standard"
                        }
                    },
                    "required": ["language", "category", "content", "filename"]
                }
            ))
            
            return tools
        
        @self.server.list_prompts()
        async def list_prompts():
            return []
        
        @self.server.list_resources()
        async def list_resources():
            return []
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "check_status":
                    result = self._check_status()
                elif name == "get_standards":
                    result = self._get_standards(arguments)
                elif name == "analyze_code":
                    result = await self._analyze_code(arguments)
                elif name == "save_standard":
                    result = self._save_standard(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    def _check_status(self) -> Dict[str, Any]:
        """Check service status"""
        return {
            "status": "operational",
            "services": {
                "standards_storage": "file_system",
                "gemini_ai": "available" if GEMINI_AVAILABLE else "not installed",
                "neo4j": "use separate neo4j MCP server"
            },
            "standards_directory": str(self.standards_dir),
            "architecture": "v3.0 - Simplified architecture",
            "note": "For graph database operations, use the Neo4j MCP server directly"
        }
    
    def _get_standards(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get standards from file system"""
        language = args.get("language", "general")
        
        standards_path = self.standards_dir / language
        if not standards_path.exists():
            return {
                "language": language,
                "error": f"No standards found for {language}",
                "available_languages": [d.name for d in self.standards_dir.iterdir() if d.is_dir()]
            }
        
        standards = {}
        for file in standards_path.glob("*.md"):
            try:
                standards[file.stem] = file.read_text()
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
        
        return {
            "language": language,
            "standards": standards,
            "count": len(standards)
        }
    
    async def _analyze_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code using Gemini"""
        if not GEMINI_AVAILABLE:
            return {
                "error": "Gemini not available",
                "install": "pip install google-generativeai",
                "set_env": "export GEMINI_API_KEY=your_key"
            }
        
        code = args.get("code", "")
        language = args.get("language", "python")
        focus = args.get("focus", "all")
        
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            prompt = f"""Analyze this {language} code focusing on {focus}:

```{language}
{code}
```

Provide:
1. Issues found
2. Improvements suggested
3. Best practices to follow
Format as JSON."""

            response = await model.generate_content_async(prompt)
            
            return {
                "language": language,
                "focus": focus,
                "analysis": response.text,
                "code_length": len(code)
            }
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {
                "error": f"Analysis failed: {e}",
                "code_length": len(code),
                "language": language
            }
    
    def _save_standard(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Save a standard to file system"""
        language = args.get("language")
        category = args.get("category")
        content = args.get("content")
        filename = args.get("filename")
        
        # Create directory if needed
        lang_dir = self.standards_dir / language / category
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        file_path = lang_dir / f"{filename}.md"
        
        try:
            # Backup existing file if it exists
            if file_path.exists():
                backup_path = file_path.with_suffix(f".backup.{int(os.time.time())}.md")
                file_path.rename(backup_path)
                logger.info(f"Backed up existing file to {backup_path}")
            
            file_path.write_text(content)
            
            return {
                "status": "saved",
                "path": str(file_path),
                "language": language,
                "category": category,
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"Failed to save standard: {e}")
            return {
                "error": f"Failed to save: {e}",
                "language": language,
                "category": category
            }
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Simplified Code Standards Auditor MCP Server v3.0...")
        logger.info("This server handles code analysis and standards management")
        logger.info("For graph database operations, use the Neo4j MCP server")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = SimpleCodeAuditorServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

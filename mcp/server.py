"""
MCP Server for Code Standards Auditor
Enables Claude Desktop integration with the code auditing system
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    TextContent, 
    ImageContent,
    EmbeddedResource,
    LogLevel
)

# Import our existing services
from services.gemini_service import GeminiService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeAuditorMCPServer:
    """MCP Server implementation for Code Standards Auditor"""
    
    def __init__(self):
        self.server = Server("code-standards-auditor")
        self.gemini_service = None
        self.neo4j_service = None
        self.cache_service = None
        self._setup_handlers()
    
    async def initialize_services(self):
        """Initialize all required services"""
        try:
            self.gemini_service = GeminiService()
            self.neo4j_service = Neo4jService()
            self.cache_service = CacheService()
            
            # Initialize Neo4j connection
            await self.neo4j_service.initialize()
            
            logger.info("All services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _setup_handlers(self):
        """Setup MCP protocol handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools for Claude Desktop"""
            return [
                Tool(
                    name="audit_code",
                    description="Audit code against coding standards",
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
                            },
                            "severity_threshold": {
                                "type": "string",
                                "enum": ["info", "warning", "error", "critical"],
                                "default": "warning"
                            }
                        },
                        "required": ["code", "language"]
                    }
                ),
                Tool(
                    name="get_standards",
                    description="Retrieve coding standards documentation",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "language": {
                                "type": "string",
                                "enum": ["python", "java", "javascript", "general"],
                                "description": "Programming language"
                            },
                            "category": {
                                "type": "string",
                                "description": "Optional category filter"
                            }
                        },
                        "required": ["language"]
                    }
                ),
                Tool(
                    name="update_standards",
                    description="Update or add new coding standards",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "language": {
                                "type": "string",
                                "description": "Programming language"
                            },
                            "rule": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "category": {"type": "string"},
                                    "examples": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["name", "description", "severity"]
                            }
                        },
                        "required": ["language", "rule"]
                    }
                ),
                Tool(
                    name="analyze_project",
                    description="Analyze an entire project directory",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "Path to project directory"
                            },
                            "recursive": {
                                "type": "boolean",
                                "default": True,
                                "description": "Scan subdirectories"
                            },
                            "file_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "default": ["*.py", "*.java", "*.js"],
                                "description": "File patterns to include"
                            }
                        },
                        "required": ["project_path"]
                    }
                ),
                Tool(
                    name="get_audit_history",
                    description="Retrieve audit history for a project",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "Project identifier"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "description": "Number of records to retrieve"
                            }
                        },
                        "required": ["project_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls from Claude Desktop"""
            
            try:
                if name == "audit_code":
                    result = await self._audit_code(arguments)
                elif name == "get_standards":
                    result = await self._get_standards(arguments)
                elif name == "update_standards":
                    result = await self._update_standards(arguments)
                elif name == "analyze_project":
                    result = await self._analyze_project(arguments)
                elif name == "get_audit_history":
                    result = await self._get_audit_history(arguments)
                else:
                    result = f"Unknown tool: {name}"
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(
                    type="text", 
                    text=f"Error: {str(e)}"
                )]
    
    async def _audit_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Audit code implementation"""
        code = args.get("code")
        language = args.get("language")
        project_id = args.get("project_id", "default")
        severity_threshold = args.get("severity_threshold", "warning")
        
        # Check cache first
        cache_key = f"audit:{language}:{hash(code)}"
        cached_result = await self.cache_service.get_audit_result(cache_key)
        if cached_result:
            return cached_result
        
        # Analyze with Gemini
        prompt = self._build_audit_prompt(code, language)
        analysis = await self.gemini_service.analyze_code(
            code=code,
            language=language,
            context={"project_id": project_id}
        )
        
        # Store in Neo4j
        if analysis.get("violations"):
            await self.neo4j_service.record_violations(
                project_id=project_id,
                violations=analysis["violations"]
            )
        
        # Cache result
        await self.cache_service.set_audit_result(cache_key, analysis)
        
        # Format response
        return {
            "summary": {
                "score": analysis.get("score", 0),
                "total_violations": len(analysis.get("violations", [])),
                "critical": sum(1 for v in analysis.get("violations", []) 
                              if v.get("severity") == "critical"),
                "errors": sum(1 for v in analysis.get("violations", []) 
                            if v.get("severity") == "error"),
                "warnings": sum(1 for v in analysis.get("violations", []) 
                              if v.get("severity") == "warning"),
            },
            "violations": analysis.get("violations", []),
            "suggestions": analysis.get("suggestions", []),
            "metadata": {
                "language": language,
                "project_id": project_id,
                "timestamp": analysis.get("timestamp")
            }
        }
    
    async def _get_standards(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve coding standards"""
        language = args.get("language")
        category = args.get("category")
        
        # Get from Neo4j
        standards = await self.neo4j_service.get_standards(
            language=language,
            category=category
        )
        
        # Also read from file system
        standards_file = Path(f"/Volumes/FS001/pythonscripts/standards/{language}/coding_standards_v1.0.0.md")
        file_content = ""
        if standards_file.exists():
            file_content = standards_file.read_text()
        
        return {
            "language": language,
            "category": category,
            "rules": standards,
            "documentation": file_content,
            "total_rules": len(standards)
        }
    
    async def _update_standards(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update coding standards"""
        language = args.get("language")
        rule = args.get("rule")
        
        # Validate with Gemini first
        validation = await self.gemini_service.validate_standard(rule)
        if not validation.get("is_valid"):
            return {
                "success": False,
                "message": validation.get("reason", "Invalid standard")
            }
        
        # Add to Neo4j
        result = await self.neo4j_service.add_standard(
            language=language,
            **rule
        )
        
        return {
            "success": True,
            "standard_id": result.get("id"),
            "message": f"Standard '{rule['name']}' added successfully"
        }
    
    async def _analyze_project(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze entire project"""
        project_path = Path(args.get("project_path"))
        recursive = args.get("recursive", True)
        file_patterns = args.get("file_patterns", ["*.py", "*.java", "*.js"])
        
        if not project_path.exists():
            return {"error": f"Path {project_path} does not exist"}
        
        results = []
        files_analyzed = 0
        total_violations = 0
        
        # Find all matching files
        for pattern in file_patterns:
            if recursive:
                files = project_path.rglob(pattern)
            else:
                files = project_path.glob(pattern)
            
            for file_path in files:
                if file_path.is_file():
                    # Read file content
                    try:
                        content = file_path.read_text()
                        
                        # Determine language
                        language = self._detect_language(file_path.suffix)
                        
                        # Audit the file
                        audit_result = await self._audit_code({
                            "code": content,
                            "language": language,
                            "project_id": str(project_path.name)
                        })
                        
                        files_analyzed += 1
                        violations = audit_result.get("summary", {}).get("total_violations", 0)
                        total_violations += violations
                        
                        results.append({
                            "file": str(file_path.relative_to(project_path)),
                            "language": language,
                            "violations": violations,
                            "score": audit_result.get("summary", {}).get("score", 0)
                        })
                        
                    except Exception as e:
                        logger.error(f"Error analyzing {file_path}: {e}")
                        results.append({
                            "file": str(file_path.relative_to(project_path)),
                            "error": str(e)
                        })
        
        return {
            "project": str(project_path),
            "files_analyzed": files_analyzed,
            "total_violations": total_violations,
            "average_score": sum(r.get("score", 0) for r in results) / max(files_analyzed, 1),
            "results": results
        }
    
    async def _get_audit_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get audit history for a project"""
        project_id = args.get("project_id")
        limit = args.get("limit", 10)
        
        # Get from Neo4j
        history = await self.neo4j_service.get_project_history(
            project_id=project_id,
            limit=limit
        )
        
        return {
            "project_id": project_id,
            "total_audits": len(history),
            "history": history
        }
    
    def _build_audit_prompt(self, code: str, language: str) -> str:
        """Build prompt for Gemini analysis"""
        return f"""
        Analyze the following {language} code for compliance with coding standards:
        
        ```{language}
        {code}
        ```
        
        Check for:
        1. Naming conventions
        2. Code organization
        3. Best practices
        4. Security issues
        5. Performance concerns
        6. Documentation
        
        Provide a detailed analysis with specific violations and suggestions.
        """
    
    def _detect_language(self, suffix: str) -> str:
        """Detect programming language from file extension"""
        language_map = {
            ".py": "python",
            ".java": "java",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "javascript",
            ".tsx": "javascript"
        }
        return language_map.get(suffix, "general")
    
    async def run(self):
        """Run the MCP server"""
        await self.initialize_services()
        
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
    asyncio.run(main())

#!/usr/bin/env python3
"""
MCP Server - API Client Version
Calls FastAPI backend instead of direct Neo4j/file access

This thin client enables:
- Remote access to standards via HTTP
- No Neo4j stdout pollution (API handles it)
- Multi-client support (Claude Desktop, Code, VS Code, etc.)
- Centralized auth, caching, rate limiting

Version: 1.0.0
Date: November 19, 2025
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# Configure logging to stderr (MCP requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file, override=True)
        logger.info(f"Loaded environment from {env_file}")
except Exception as e:
    logger.warning(f"Could not load .env file: {e}")

# Import MCP SDK
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
    import mcp.server.stdio
    import httpx
except ImportError as e:
    logger.error(f"Failed to import required packages: {e}")
    logger.error("Install with: pip install mcp httpx")
    sys.exit(1)

# Configuration - default to port 8001 where the API runs
API_BASE_URL = os.getenv("CODE_AUDITOR_API_URL", "http://localhost:8001")
API_KEY = os.getenv("CODE_AUDITOR_API_KEY", "")
REQUEST_TIMEOUT = 30.0

# Mask API key for logging
masked_key = f"{API_KEY[:10]}...{API_KEY[-4:]}" if len(API_KEY) > 14 else "NOT_SET"
logger.info(f"API Base URL: {API_BASE_URL}")
logger.info(f"API Key: {masked_key}")


class StandardsAPIClient:
    """Thin MCP client that calls the FastAPI backend"""

    def __init__(self):
        """Initialize HTTP client"""
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY

        self.client = httpx.AsyncClient(
            base_url=API_BASE_URL,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True
        )
        logger.info("Initialized API client")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            response = await self.client.get("/api/v1/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}

    async def search_standards(
        self,
        query: str,
        language: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search standards via API"""
        try:
            # Use agent-optimized endpoint with required context
            payload = {
                "query": query,
                "context": {
                    "agent_type": "mcp_client",
                    "context_type": "development",
                    "session_id": "mcp_session"
                },
                "max_results": limit
            }
            if language or category:
                payload["filters"] = {}
                if language:
                    payload["filters"]["language"] = language
                if category:
                    payload["filters"]["category"] = category

            response = await self.client.post("/api/v1/agent/search-standards", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching standards: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}", "details": str(e)}
        except Exception as e:
            logger.error(f"Error searching standards: {e}")
            return {"error": str(e)}

    async def analyze_code(
        self,
        code: str,
        language: str,
        focus: str = "all"
    ) -> Dict[str, Any]:
        """Analyze code via API"""
        try:
            # Use agent-optimized endpoint with required context
            payload = {
                "code": code,
                "language": language,
                "context": {
                    "agent_type": "mcp_client",
                    "context_type": "code_review",
                    "session_id": "mcp_session"
                },
                "analysis_depth": "standard" if focus == "all" else "quick"
            }

            response = await self.client.post("/api/v1/agent/analyze-code", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error analyzing code: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}", "details": str(e)}
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {"error": str(e)}

    async def list_standards(
        self,
        language: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """List standards via API"""
        try:
            params = {"active_only": active_only}
            if language:
                params["language"] = language
            if category:
                params["category"] = category

            response = await self.client.get("/api/v1/standards/list", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing standards: {e.response.status_code}")
            return {"error": f"HTTP {e.response.status_code}", "details": str(e)}
        except Exception as e:
            logger.error(f"Error listing standards: {e}")
            return {"error": str(e)}

    async def get_recommendations(
        self,
        code: str,
        language: str,
        priority_threshold: str = "medium"
    ) -> Dict[str, Any]:
        """Get code improvement recommendations via API"""
        try:
            payload = {
                "code": code,
                "language": language,
                "priority_threshold": priority_threshold
            }

            response = await self.client.post("/api/v1/standards/recommendations", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting recommendations: {e.response.status_code}")
            return {"error": f"HTTP {e.response.status_code}", "details": str(e)}
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return {"error": str(e)}

    async def create_standard(
        self,
        topic: str,
        category: str,
        language: str = "general",
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """Create a new coding standard via research API"""
        try:
            payload = {
                "topic": topic,
                "category": category,
                "context": {"language": language},
                "auto_approve": auto_approve
            }

            response = await self.client.post("/api/v1/standards/research", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating standard: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}", "details": str(e)}
        except Exception as e:
            logger.error(f"Error creating standard: {e}")
            return {"error": str(e)}

    async def update_standard(
        self,
        standard_id: str,
        content: Optional[str] = None,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing coding standard via API"""
        try:
            payload = {"standard_id": standard_id}
            if content:
                payload["content"] = content
            if version:
                payload["version"] = version
            if metadata:
                payload["metadata"] = metadata

            response = await self.client.put(f"/api/v1/standards/{standard_id}", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating standard: {e.response.status_code}")
            return {"error": f"HTTP {e.response.status_code}", "details": str(e)}
        except Exception as e:
            logger.error(f"Error updating standard: {e}")
            return {"error": str(e)}


# Initialize MCP server and API client
server = Server("code-standards-auditor-api")
api_client = StandardsAPIClient()


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="check_status",
            description="Check API server status and connectivity",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_standards",
            description="Search coding standards by query text. Returns relevant standards from all languages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keywords, concepts, topics)"
                    },
                    "language": {
                        "type": "string",
                        "description": "Optional: Filter by language (python, javascript, java, etc.)",
                        "enum": ["python", "javascript", "java", "general", "language_specific", "security"]
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional: Filter by category",
                        "enum": ["security", "performance", "testing", "best-practices", "error-handling", "architecture", "style", "documentation", "api", "deployment"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="analyze_code",
            description="Analyze code against coding standards. Returns violations, recommendations, and quality score.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to analyze"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "enum": ["python", "javascript", "java", "typescript", "go", "rust"]
                    },
                    "focus": {
                        "type": "string",
                        "description": "Analysis focus area (default: all)",
                        "enum": ["all", "security", "performance", "quality"],
                        "default": "all"
                    }
                },
                "required": ["code", "language"]
            }
        ),
        Tool(
            name="list_standards",
            description="List all available coding standards. Can filter by language and category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Optional: Filter by language",
                        "enum": ["python", "javascript", "java", "general", "language_specific", "security"]
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional: Filter by category",
                        "enum": ["security", "performance", "testing", "best-practices", "error-handling", "architecture", "style", "documentation", "api", "deployment"]
                    },
                    "active_only": {
                        "type": "boolean",
                        "description": "Only return active standards (default: true)",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_recommendations",
            description="Get prioritized improvement recommendations for code. Returns actionable suggestions ranked by priority.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to analyze for recommendations"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "enum": ["python", "javascript", "java", "typescript"]
                    },
                    "priority_threshold": {
                        "type": "string",
                        "description": "Minimum priority level (default: medium)",
                        "enum": ["critical", "high", "medium", "low"],
                        "default": "medium"
                    }
                },
                "required": ["code", "language"]
            }
        ),
        Tool(
            name="create_standard",
            description="Create a new coding standard using AI research. Generates comprehensive standards documentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic or description of the standard to create (e.g., 'Python async error handling', 'REST API versioning')"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category for the standard",
                        "enum": ["security", "performance", "testing", "best-practices", "error-handling", "architecture", "style", "documentation", "api", "deployment"]
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (optional, defaults to 'general')",
                        "enum": ["python", "javascript", "java", "typescript", "go", "rust", "general"],
                        "default": "general"
                    },
                    "auto_approve": {
                        "type": "boolean",
                        "description": "Automatically approve the standard (default: false)",
                        "default": False
                    }
                },
                "required": ["topic", "category"]
            }
        ),
        Tool(
            name="update_standard",
            description="Update an existing coding standard with new content, version, or metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "standard_id": {
                        "type": "string",
                        "description": "ID of the standard to update"
                    },
                    "content": {
                        "type": "string",
                        "description": "New content for the standard (optional)"
                    },
                    "version": {
                        "type": "string",
                        "description": "New version number (e.g., '1.1.0') (optional)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata to update (optional)"
                    }
                },
                "required": ["standard_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    try:
        logger.info(f"Tool called: {name}")

        if name == "check_status":
            result = await api_client.health_check()
            result["api_url"] = API_BASE_URL
            result["api_key_configured"] = bool(API_KEY)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "search_standards":
            query = arguments.get("query")
            language = arguments.get("language")
            category = arguments.get("category")
            limit = arguments.get("limit", 10)

            result = await api_client.search_standards(
                query=query,
                language=language,
                category=category,
                limit=limit
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "analyze_code":
            code = arguments.get("code")
            language = arguments.get("language")
            focus = arguments.get("focus", "all")

            result = await api_client.analyze_code(
                code=code,
                language=language,
                focus=focus
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "list_standards":
            language = arguments.get("language")
            category = arguments.get("category")
            active_only = arguments.get("active_only", True)

            result = await api_client.list_standards(
                language=language,
                category=category,
                active_only=active_only
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "get_recommendations":
            code = arguments.get("code")
            language = arguments.get("language")
            priority_threshold = arguments.get("priority_threshold", "medium")

            result = await api_client.get_recommendations(
                code=code,
                language=language,
                priority_threshold=priority_threshold
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "create_standard":
            topic = arguments.get("topic")
            category = arguments.get("category")
            language = arguments.get("language", "general")
            auto_approve = arguments.get("auto_approve", False)

            result = await api_client.create_standard(
                topic=topic,
                category=category,
                language=language,
                auto_approve=auto_approve
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "update_standard":
            standard_id = arguments.get("standard_id")
            content = arguments.get("content")
            version = arguments.get("version")
            metadata = arguments.get("metadata")

            result = await api_client.update_standard(
                standard_id=standard_id,
                content=content,
                version=version,
                metadata=metadata
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]

    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name})
        )]


async def main():
    """Run MCP server"""
    logger.info("Starting Code Standards Auditor MCP Server (API Client)")
    logger.info(f"Connecting to API: {API_BASE_URL}")

    # Test API connectivity
    health = await api_client.health_check()
    if "error" in health:
        logger.warning(f"API health check failed: {health}")
        logger.warning("Server will start but API calls may fail")
    else:
        logger.info(f"API health check passed: {health.get('status', 'unknown')}")

    # Run MCP server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP server running on stdio")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

    # Cleanup
    await api_client.close()
    logger.info("MCP server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

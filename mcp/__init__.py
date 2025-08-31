"""
MCP (Model Context Protocol) Server for Code Standards Auditor
Enables Claude Desktop integration with the code auditing system
"""

from .server import CodeAuditorMCPServer

__version__ = "1.0.0"
__all__ = ["CodeAuditorMCPServer"]

# Enhanced Code Standards Auditor v2.0

A revolutionary AI-powered code standards platform with conversational research, automated workflows, and agent-optimized APIs. Transform your development process with natural language standard creation, intelligent code analysis, and comprehensive improvement recommendations.

## 🚀 Features

### 🆕 **Version 2.0 - Revolutionary Enhancements**

#### 🧠 **Conversational Standards Research**
- **Natural Language Requests**: "Create a standard for REST API error handling in Python"
- **Interactive Requirements Gathering**: AI asks clarifying questions to understand your needs
- **Multi-turn Conversations**: Refine standards through iterative dialogue
- **Context Preservation**: Remembers your preferences and project context
- **Real-time Preview**: See standards being created as you discuss them

#### 🔄 **Integrated Workflow Automation**
- **End-to-End Pipeline**: Research → Documentation → Validation → Deployment → Analysis
- **Background Processing**: Monitor progress of complex workflows
- **Quality Assurance**: Automated validation at every step
- **Comprehensive Reporting**: Detailed feedback and actionable insights
- **Multiple Export Formats**: Markdown, PDF, JSON, and more

#### 🤖 **Agent-Optimized APIs**
- **Batch Operations**: Process multiple requests efficiently
- **Real-time Updates**: Server-Sent Events for live notifications
- **Context-Aware Search**: Enhanced relevance scoring and filtering
- **Structured Responses**: Optimized for AI agent consumption
- **Performance Optimized**: Advanced caching and query optimization

#### 🛠 **Advanced Code Recommendations**
- **Step-by-Step Guides**: Detailed implementation instructions with code examples
- **Automated Fix Generation**: AI-generated fixes with confidence scoring
- **Risk Assessment**: Understand the impact before applying changes
- **Effort Estimation**: Know how long improvements will take
- **Code Transformations**: Before/after examples with explanations

### 🎯 **Core Platform Features**

- **Automated Code Review**: Real-time analysis of code against project-specific and language-specific standards
- **Standards Documentation Management**: Dynamic creation and maintenance of coding standards
- **Pipeline Integration**: Seamless CI/CD integration through RESTful API
- **Claude Desktop Integration**: Native MCP server for direct interaction with Claude
- **Multi-Language Support**: Python, Java, JavaScript, and more
- **Cost-Optimized LLM Usage**: Intelligent prompt caching and batch processing
- **Neo4j Graph Database**: Relationship mapping between code patterns and standards
- 🔬 **Standards Research**: AI-powered research and generation of new standards
- 💡 **Smart Recommendations**: Intelligent code improvement suggestions with implementation examples
- 🎯 **Pattern Discovery**: Automatic discovery of patterns from code samples
- 🔧 **Quick Fixes**: Immediate actionable fixes for common issues
- 📝 **Refactoring Plans**: Comprehensive refactoring strategies with risk assessment
- 🤖 **Agent Interface**: Standards API optimized for AI agent consumption

## 📋 Prerequisites

- Python 3.11+
- Neo4j 5.x
- Redis (for caching)
- API Keys:
  - Google Gemini API key
  - Anthropic API key (optional, for fallback)
  - Neo4j password

## 🛠️ Installation

1. Clone the repository:
```bash
cd /Volumes/FS001/pythonscripts/code-standards-auditor
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export NEO4J_PASSWORD="your-neo4j-password"
```

5. Initialize the database:
```bash
python3 scripts/migrate.py
python3 scripts/seed_standards.py
```

## 🚦 Quick Start v2.0

### 🌆 **Try the Enhanced CLI (Recommended)**

```bash
# Make the CLI executable
chmod +x cli/enhanced_cli.py

# Start the interactive enhanced CLI
python3 cli/enhanced_cli.py interactive

# Or use specific commands
python3 cli/enhanced_cli.py workflow "Create API security standards for Python FastAPI"
python3 cli/enhanced_cli.py analyze my_code.py --language python --focus security
```

### 🗣 **Conversational Standards Research**

```bash
# Start a natural language research session
python3 cli/enhanced_cli.py interactive
# Then select: research
# Example: "I need standards for handling sensitive data in microservices"
```

### 🔄 **Integrated Workflows via API**

```python
import requests

# Start an end-to-end workflow
response = requests.post(
    "http://localhost:8000/api/v1/workflow/start",
    json={
        "research_request": "Create comprehensive logging standards for Node.js applications",
        "code_samples": [open("example.js").read()],
        "project_context": {
            "team_size": "medium",
            "experience_level": "intermediate"
        }
    }
)

workflow_id = response.json()["workflow_id"]
print(f"Workflow started: {workflow_id}")

# Monitor progress
status_response = requests.get(f"http://localhost:8000/api/v1/workflow/{workflow_id}/status")
print(f"Status: {status_response.json()['status']}")
```

### 🤖 **Agent-Optimized Operations**

```python
# Enhanced search for AI agents
response = requests.post(
    "http://localhost:8000/api/v1/agent/search-standards",
    json={
        "query": "authentication security",
        "context": {
            "agent_type": "code_reviewer",
            "context_type": "security",
            "session_id": "session_123"
        },
        "max_results": 5,
        "include_related": True
    }
)

# Get agent-optimized code analysis
analysis_response = requests.post(
    "http://localhost:8000/api/v1/agent/analyze-code",
    json={
        "code": "your_code_here",
        "language": "python",
        "context": {
            "agent_type": "developer_assistant",
            "context_type": "development",
            "session_id": "session_123"
        },
        "analysis_depth": "comprehensive",
        "return_suggestions": True
    }
)
```

### 📊 **Traditional API Server Setup**

### Starting the API Server

```bash
# Development mode
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build

# Or build manually
docker build -f docker/Dockerfile -t code-auditor .
docker run -p 8000:8000 --env-file .env code-auditor
```

## 📚 API Documentation

### Standards Research & Management

#### Research New Standard
```python
POST /api/v1/standards/research
{
    "topic": "REST API Design",
    "category": "architecture",
    "context": {
        "language": "python",
        "framework": "FastAPI"
    },
    "examples": ["code example 1", "code example 2"]
}
```

#### List Standards
```python
GET /api/v1/standards/list?category=python&status=approved&limit=50
```

#### Get Specific Standard
```python
GET /api/v1/standards/{standard_id}
```

#### Update Standard
```python
PUT /api/v1/standards/{standard_id}
{
    "content": "Updated standard content",
    "version": "1.1.0",
    "metadata": {"reviewed": true}
}
```

### Code Analysis & Recommendations

#### Get Code Recommendations
```python
POST /api/v1/standards/recommendations
{
    "code": "def calculate_sum(a,b):\n    return a+b",
    "language": "python",
    "focus_areas": ["performance", "security"],
    "context": {
        "project_type": "api",
        "performance_critical": true
    }
}
```

Response includes:
- Prioritized recommendations with severity levels
- Implementation examples for critical issues
- Estimated effort for fixes
- Links to relevant documentation

#### Discover Patterns
```python
POST /api/v1/standards/discover-patterns
{
    "code_samples": [
        "# Code sample 1",
        "# Code sample 2",
        "# Code sample 3"
    ],
    "language": "python",
    "min_frequency": 2
}
```

#### Get Quick Fixes
```python
POST /api/v1/standards/quick-fixes
{
    "code": "vulnerable_code_here",
    "language": "python",
    "issue_type": "security"
}
```

#### Generate Refactoring Plan
```python
POST /api/v1/standards/refactoring-plan
{
    "code": "legacy_code_here",
    "language": "java",
    "goals": [
        "improve testability",
        "reduce complexity",
        "enhance performance"
    ]
}
```

### Standards Validation & Agent Interface

#### Validate Standard
```python
POST /api/v1/standards/validate
{
    "content": "Standard content to validate",
    "category": "security"
}
```

#### Query Standards for AI Agents
```python
GET /api/v1/standards/agent/query?query=authentication&language=python&limit=10
```

Returns simplified, agent-optimized results with relevance scoring.

## 🤖 Claude Desktop Integration

### MCP Server Setup

The Code Standards Auditor includes a native MCP (Model Context Protocol) server for seamless integration with Claude Desktop.

#### Quick Setup

```bash
# Run the enhanced installation script
chmod +x install_mcp.sh
./install_mcp.sh

# Or manually install critical packages
python3 -m pip install mcp google-generativeai neo4j redis pydantic-settings

# Test the MCP server with diagnostics
python3 mcp/test_server.py
```

**Note:** The server now runs with graceful degradation. If some services are unavailable, it will still start and provide limited functionality with clear status reporting.

#### Configure Claude Desktop

```bash
# Copy the configuration to Claude Desktop
cp mcp/mcp_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Or manually add to ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "code-standards-auditor": {
      "command": "python3",
      "args": ["/Volumes/FS001/pythonscripts/code-standards-auditor/mcp/server.py"]
    }
  }
}
```

### Available Tools in Claude
- **audit_code**: Analyze code for standards compliance
- **get_standards**: Retrieve coding standards documentation
- **update_standards**: Add or modify standards
- **analyze_project**: Audit entire project directories
- **get_audit_history**: View historical audit results

See [`mcp/README.md`](mcp/README.md) for detailed setup and usage instructions.

#### 🔧 **Troubleshooting MCP Server Issues**

**Issue: "Unexpected non-whitespace character after JSON" in Claude Desktop logs**

This error typically indicates a Pydantic validation error in the MCP server's tool definitions.

**Solution Applied (September 2025):**
- Fixed missing `"type": "object"` field in `check_status` tool's `inputSchema`
- All MCP tools now comply with JSON Schema requirements
- Server validates properly with Claude Desktop

**Diagnostic Steps:**
```bash
# Test MCP server validation
python3 mcp/test_server.py

# Check server startup
python3 mcp/server.py

# Verify tool schemas
python3 -c "from mcp.server import CodeAuditorMCPServer; server = CodeAuditorMCPServer()"
```

**Common Validation Errors:**
- Missing `"type": "object"` in tool `inputSchema`
- Invalid JSON structure in tool definitions
- Pydantic model validation failures

**If issues persist:**
1. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp.log`
2. Verify all dependencies installed: `pip install mcp google-generativeai neo4j redis`
3. Test individual components with diagnostic tools

## 📖 Usage Examples

### Basic Code Audit

```python
import requests

# Submit code for audit
response = requests.post(
    "http://localhost:8000/api/v1/audit",
    json={
        "code": "def calculate_sum(a,b):\n    return a+b",
        "language": "python",
        "project_context": {
            "project_id": "my-project",
            "severity_threshold": "warning"
        }
    }
)

audit_result = response.json()
print(f"Found {audit_result['violations_count']} violations")
```

### Research New Standard

```python
# Research and generate a new standard
response = requests.post(
    "http://localhost:8000/api/v1/standards/research",
    json={
        "topic": "GraphQL API Security",
        "category": "security",
        "context": {
            "framework": "Apollo Server",
            "concerns": ["authentication", "rate limiting", "query depth"]
        }
    }
)

new_standard = response.json()
print(f"Created standard: {new_standard['id']}")
```

### Get Improvement Recommendations

```python
# Get recommendations for code improvement
response = requests.post(
    "http://localhost:8000/api/v1/standards/recommendations",
    json={
        "code": open("my_module.py").read(),
        "language": "python",
        "focus_areas": ["security", "performance"]
    }
)

recommendations = response.json()
for rec in recommendations['recommendations'][:5]:
    print(f"[{rec['priority']}] {rec['title']}")
    if 'implementation_example' in rec:
        print(f"  Fix: {rec['implementation_example']['after']}")
```

## 🏗️ Architecture

```
code-standards-auditor/
├── api/                  # FastAPI application
│   ├── routers/         # API endpoints
│   │   ├── audit.py     # Code auditing endpoints
│   │   ├── standards.py # Standards management & research
│   │   └── admin.py     # Administrative endpoints
│   ├── middleware/      # Custom middleware
│   └── main.py          # Application entry point
├── core/                # Business logic
│   ├── audit/          # Audit engine
│   └── standards/      # Standards processing
├── services/           # External service integrations
│   ├── gemini_service.py           # Gemini AI integration
│   ├── neo4j_service.py           # Graph database
│   ├── cache_service.py           # Redis caching
│   ├── standards_research_service.py  # AI research
│   └── recommendations_service.py     # Recommendations engine
├── mcp/                # Claude Desktop integration
│   └── server.py       # MCP server implementation
├── standards/          # Standards documentation
│   ├── python/        # Python standards
│   ├── java/          # Java standards
│   └── general/       # Language-agnostic standards
└── docker/            # Container configuration
```

## 🔄 Development Status

### ✅ Completed
- Core architecture and project structure
- Configuration management with environment variables
- Neo4j graph database service with indexing
- Gemini AI integration with prompt caching
- Redis caching service with TTL management
- Standards documentation (Python, Java, General)
- Claude Desktop MCP integration
- Standards Research Service (AI-powered generation)
- Recommendations Service (improvement suggestions)
- Standards API Router (comprehensive endpoints)
- Pattern discovery from code samples
- Quick fixes and refactoring plans
- Agent-optimized query interface

### 🚧 In Progress
- Additional API routers (audit, admin)
- Authentication and authorization middleware
- Rate limiting and request logging
- Comprehensive testing suite
- Docker containerization
- CI/CD pipeline integration

### 📅 Planned
- Web UI dashboard
- GitHub/GitLab integration
- Slack/Teams notifications
- Custom rule creation interface
- Standards versioning and rollback
- Multi-tenant support
- Performance profiling tools
- Advanced analytics dashboard

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_gemini_service.py
```

## 📊 Performance Optimization

The system uses several optimization strategies:

1. **Prompt Caching**: Gemini API prompt caching reduces costs by 50-70%
2. **Redis Caching**: Frequently accessed data cached with configurable TTL
3. **Batch Processing**: Multiple requests processed together for efficiency
4. **Connection Pooling**: Reused connections for database and cache
5. **Async Operations**: Non-blocking I/O for better concurrency
6. **Graph Indexing**: Neo4j indexes for fast query performance

## 🔒 Security

- Environment-based configuration (no hardcoded secrets)
- API key authentication for endpoints
- Rate limiting to prevent abuse
- Input validation and sanitization
- SQL injection prevention
- CORS configuration for web clients
- Audit logging for compliance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- Anthropic for Claude integration
- Neo4j for graph database
- FastAPI for the web framework
- The open-source community

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on [GitHub](https://github.com/ronkoch2-code/code-standards-auditor/issues)
- Check the [documentation](docs/)
- Review the [API docs](http://localhost:8000/docs) when running locally

## 🔄 Version History

### v2.0.2 (September 02, 2025) - 🔧 MCP Server Validation Fix
- **🚨 CRITICAL: Fixed MCP Server Pydantic Validation Error** - Claude Desktop integration now works
- **🐛 Tool Schema Fix**: Added missing `"type": "object"` field to `check_status` tool's `inputSchema`
- **✅ JSON Schema Compliance**: All MCP tools now validate properly with Pydantic
- **📋 Enhanced Documentation**: Added MCP troubleshooting guide with diagnostic steps
- **🛠 Development State Tracking**: Added `DEVELOPMENT_STATE.md` for session management

### v2.0.1 (September 01, 2025) - 🔧 Comprehensive Workflow Fixes
- **🚨 CRITICAL: Fixed 3 Major Workflow Errors** - Complete workflow now functional
- **🐛 CacheService Method Mismatch**: Fixed `get_cached_audit()` and `cache_audit_result()` calls
- **🚀 GeminiService Missing Methods**: Added `generate_content_async()` and `generate_with_caching()`
- **⚙️ Neo4j Settings Configuration**: Added `USE_NEO4J` with intelligent auto-detection
- **🛠 Enhanced JSON Parsing**: Robust parsing with fallback mechanisms for invalid responses
- **🧪 Comprehensive Testing**: Added 3 test scripts to verify all fixes work correctly
- **📋 Complete Phase 1-6 Workflow**: Natural language → deployed standards with analysis

### v2.0.0 (September 01, 2025) - 🚀 Revolutionary Enhancement Release
- **🧠 Conversational Research Interface**: Natural language standard creation with interactive AI
- **🔄 Integrated Workflow Service**: End-to-end automation from research to deployment
- **🤖 Agent-Optimized APIs**: Specialized endpoints for AI agent consumption
- **🛠 Enhanced Recommendations Engine**: Step-by-step guides with automated fixes
- **🌆 Unified CLI Interface**: Interactive and command-line access to all features
- **📊 Real-time Monitoring**: Live workflow progress and status updates
- **🎯 Quality Assurance**: Comprehensive validation throughout all processes
- **📈 Performance Optimization**: Advanced caching and batch processing
- **25+ new capabilities** with full backwards compatibility

### v1.2.0 (January 31, 2025)
- Added Standards Research Service for AI-powered standard generation
- Implemented Recommendations Service with prioritized suggestions
- Created comprehensive Standards API with research endpoints
- Added pattern discovery from code samples
- Implemented quick fixes and refactoring plans
- Added agent-optimized query interface

### v1.1.0 (January 31, 2025)
- Enhanced MCP server with graceful degradation
- Improved error handling and diagnostics
- Added comprehensive logging

### v1.0.0 (January 27, 2025)
- Initial release with core functionality
- Basic audit capabilities
- Standards management
- Claude Desktop integration

---

**Last Updated:** September 01, 2025 - Version 2.0.0 Release

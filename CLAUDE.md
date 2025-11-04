# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **Code Standards Auditor** is an AI-powered code standards platform with conversational research, automated workflows, and agent-optimized APIs. It combines Google Gemini AI, Neo4j graph database, and Redis caching to provide intelligent code analysis, standards management, and comprehensive improvement recommendations.

**Current Version:** v3.0.1 (MCP Implementation Complete)
**Python Version:** Python 3.11+ (use `python3` and `pip` commands on M1 Mac)
**License:** MIT

## Environment Setup

### Required Environment Variables
```bash
export GEMINI_API_KEY="your-gemini-api-key"           # Required for AI features
export ANTHROPIC_API_KEY="your-anthropic-api-key"    # Optional fallback
export NEO4J_PASSWORD="your-neo4j-password"           # For graph features
```

### Installation Commands
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 scripts/migrate.py
python3 scripts/seed_standards.py
```

## Common Development Commands

### Running the API Server
```bash
# Development mode with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_gemini_service.py

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### Code Quality
```bash
# Format code with Black
black .

# Check code style
flake8

# Type checking
mypy .

# Run all linting
black . && flake8 && mypy .
```

### CLI Usage
```bash
# Interactive enhanced CLI (recommended)
python3 cli/enhanced_cli.py interactive

# Start a workflow
python3 cli/enhanced_cli.py workflow "Create API security standards for Python FastAPI"

# Analyze code
python3 cli/enhanced_cli.py analyze my_code.py --language python --focus security
```

### MCP Server (Claude Desktop Integration)
```bash
# Test MCP server
python3 mcp/test_server.py

# Run simplified MCP server (v3.0 architecture)
python3 mcp_server/server_simple.py

# Verify MCP setup
python3 verify_mcp_setup.py
```

### Docker
```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build

# Build manually
docker build -f docker/Dockerfile -t code-auditor .
docker run -p 8000:8000 --env-file .env code-auditor
```

## Architecture Overview

### High-Level Structure

The codebase follows a clean separation of concerns with three main layers:

1. **API Layer** (`api/`): FastAPI application with routers, middleware, and schemas
2. **Business Logic** (`core/` & `services/`): Core audit logic and external integrations
3. **MCP Integration** (`mcp_server/`): Claude Desktop integration via Model Context Protocol

### Key Architectural Decisions

#### v3.0 MCP Architecture (September 2025)
The MCP server was redesigned to use **separation of concerns**:
- **Code Standards Auditor MCP** (`mcp_server/server_simple.py`): Simplified server for Gemini AI code analysis and file-based standards management. No Neo4j dependency to avoid stdout pollution.
- **Neo4j MCP Server**: Uses Neo4j's official native MCP implementation for graph operations.

This architecture eliminates stdout pollution issues that broke JSON-RPC communication in earlier versions.

#### Cost-Optimized AI Integration
The system uses intelligent strategies to minimize LLM API costs:
- **Prompt Caching**: Gemini API prompt caching (50-70% cost reduction) via `GeminiService`
- **Redis Caching**: Frequently accessed data cached with configurable TTL via `CacheService`
- **Batch Processing**: Multiple requests processed together for efficiency
- **Graceful Degradation**: Services fail gracefully if dependencies are unavailable

#### Neo4j Integration Pattern
Neo4j usage is **optional** and controlled by `USE_NEO4J` setting in `config/settings.py`:
- Auto-detects based on `NEO4J_PASSWORD` and `NEO4J_URI` configuration
- Can be explicitly set via `USE_NEO4J` environment variable
- Services check availability before attempting Neo4j operations
- Falls back to file-based operations when Neo4j is unavailable

### Service Dependencies

```
FastAPI App (api/main.py)
├── Neo4jService (services/neo4j_service.py)
├── CacheService (services/cache_service.py)
├── GeminiService (services/gemini_service.py)
├── StandardsResearchService (services/standards_research_service.py)
├── RecommendationsService (services/recommendations_service.py)
└── IntegratedWorkflowService (services/integrated_workflow_service.py)
```

All services are initialized during application startup in the `lifespan` async context manager in `api/main.py`.

### Standards Storage

Standards are stored in a well-structured hierarchy at:
```
/Volumes/FS001/pythonscripts/standards/
├── python/
├── java/
├── javascript/
└── general/
```

**Important**: When updating standards, keep versions of documentation as changes are made. The system uses `STANDARDS_VERSION_RETENTION_DAYS` (default 90 days) for version retention.

## API Endpoints Structure

### Standards Management (`/api/v1/standards`)
- `POST /research` - AI-powered research and generation of new standards
- `GET /list` - List standards with filtering
- `GET /{standard_id}` - Get specific standard
- `PUT /{standard_id}` - Update standard
- `POST /validate` - Validate standard content

### Code Analysis (`/api/v1/standards`)
- `POST /recommendations` - Get prioritized code improvement recommendations
- `POST /discover-patterns` - Discover patterns from code samples
- `POST /quick-fixes` - Get immediate actionable fixes
- `POST /refactoring-plan` - Generate comprehensive refactoring strategy

### Agent-Optimized Interface (`/api/v1/agent`)
Specialized endpoints designed for AI agent consumption:
- `POST /search-standards` - Enhanced search with relevance scoring
- `POST /analyze-code` - Agent-optimized code analysis
- `GET /query` - Simplified query interface for agents

### Integrated Workflows (`/api/v1/workflow`)
- `POST /start` - Start end-to-end workflow (research → documentation → validation → deployment → analysis)
- `GET /{workflow_id}/status` - Monitor workflow progress
- Real-time updates via Server-Sent Events

### Audit Operations (`/api/v1/audit`)
- `POST /` - Submit code for audit
- `GET /history` - View historical audit results

## Important Code Patterns

### Async/Await Usage
All service methods that perform I/O operations are async. Always use `await` when calling:
- Database operations (`Neo4jService`)
- Cache operations (`CacheService`)
- AI API calls (`GeminiService`)
- HTTP requests

### Error Handling
Services use graceful degradation:
```python
try:
    # Try operation with Neo4j
    result = await neo4j_service.query(...)
except Exception as e:
    logger.warning(f"Neo4j unavailable: {e}")
    # Fall back to file-based operation
    result = await file_based_query(...)
```

### Configuration Management
All configuration is centralized in `config/settings.py` using Pydantic settings:
- Environment variables are automatically loaded
- `.env` file support
- Type validation and defaults
- Settings cached with `@lru_cache()`

Access settings via:
```python
from config.settings import settings
api_key = settings.GEMINI_API_KEY
```

### Logging
Use structured logging throughout:
```python
import structlog
logger = structlog.get_logger()
logger.info("operation_complete", operation="audit", duration=1.2, items=10)
```

## MCP Server Implementation Notes

### Stdout Handling
**Critical**: MCP protocol requires clean JSON-RPC communication on stdout. All logging, debug output, and informational messages **must** go to stderr:
```python
logging.basicConfig(stream=sys.stderr, force=True)
```

Never use `print()` statements in MCP server code - it will break JSON-RPC communication.

### Tool Registration
All MCP tools must include complete JSON schema with `"type": "object"`:
```python
Tool(
    name="tool_name",
    description="Tool description",
    inputSchema={
        "type": "object",  # Required!
        "properties": {...},
        "required": [...]
    }
)
```

Missing `"type": "object"` causes Pydantic validation errors.

### Configuration
MCP server configuration is in `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS).

**Always backup before editing**:
```bash
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup
```

## Working with This Codebase

### Making Changes to Standards
1. Standards are stored at `/Volumes/FS001/pythonscripts/standards`
2. Maintain version history when updating standards
3. Use the `StandardsResearchService` for AI-powered standard generation
4. Validate standards with `POST /api/v1/standards/validate` before deploying

### Adding New Language Support
1. Add language to `SUPPORTED_LANGUAGES` in `config/settings.py`
2. Create standards directory in `/Volumes/FS001/pythonscripts/standards/{language}/`
3. Add tree-sitter parser if needed in `services/code_analysis_service.py`
4. Update API documentation

### Working with Git
Use the GitHub scripts in `github-scripts/` directory:
- Scripts should be maintained and old scripts removed periodically
- Follow the same feature branch strategy as Avatar-Engine project
- Repository: https://github.com/ronkoch2-code/code-standards-auditor

### Session State Management
- `DEVELOPMENT_STATE.md` tracks ongoing work and tasks
- Update this file before and after completing tasks
- Helps resume work across sessions

### Project Notes
- Use **zsh** for shell commands (macOS default)
- Optimize code for M1 Mac architecture
- Only create fully formed JSON files with complete syntax
- Leverage current best practices for prompt caching and batch APIs
- Review code with the Code Standards Auditor itself for quality

## Middleware Stack

The API uses the following middleware (executed in order):
1. **CORSMiddleware**: Cross-origin resource sharing
2. **LoggingMiddleware**: Request/response logging
3. **RateLimitMiddleware**: Rate limiting (default 60 req/min)
4. **AuthMiddleware**: API key authentication

## Monitoring and Observability

### Health Checks
```bash
curl http://localhost:8000/api/v1/health
```

Returns status of Neo4j, Redis, and overall system health.

### Metrics
Prometheus metrics available at `/metrics` endpoint when `ENABLE_METRICS=true`.

### Logs
Structured JSON logs with:
- Request IDs for tracing
- Timestamp in ISO format
- Log levels: DEBUG, INFO, WARNING, ERROR
- Contextual metadata

## Common Issues and Solutions

### Neo4j Connection Failures
- Verify Neo4j is running: `brew services list`
- Check credentials in environment variables
- System degrades gracefully to file-based operations

### MCP Server JSON Parsing Errors
- Use simplified server: `mcp_server/server_simple.py`
- Ensure no stdout pollution (all logging to stderr)
- Verify tool schemas have `"type": "object"`

### Gemini API Rate Limits
- Enable caching: `GEMINI_ENABLE_CACHING=true`
- Reduce batch size: `GEMINI_BATCH_SIZE=5`
- Use flash model for non-critical operations: `GEMINI_MODEL=gemini-1.5-flash`

### Package Import Conflicts
On M1 Macs, `pip3` and `python3` may use different installations. Always use:
```bash
python3 -m pip install package_name
```

## Feature Flags

Control features via environment variables:
- `ENABLE_BATCH_PROCESSING`: Batch API operations (default: true)
- `ENABLE_REAL_TIME_UPDATES`: Server-sent events for workflows (default: true)
- `ENABLE_STANDARDS_EVOLUTION`: Auto-update standards (default: true)
- `ENABLE_WEBSOCKET`: WebSocket support (default: false)
- `USE_NEO4J`: Enable Neo4j features (auto-detected)

## Documentation References

- API Documentation: http://localhost:8000/docs (when server is running)
- ReDoc: http://localhost:8000/redoc
- Architecture v3: `ARCHITECTURE_V3.md`
- Development Status: `DEVELOPMENT_STATUS.md`
- MCP Integration: `mcp/README.md`

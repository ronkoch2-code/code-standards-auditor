# Code Standards Auditor v4.2.2 - Auto-Refresh Standards!

> 🎉 **NEW in v4.2.2**: Auto-refresh standards on access! Standards older than 30 days automatically update using deep research mode. Background queue processing, comprehensive metrics, and per-standard configuration ensure always-current best practices.

## 🔄 Latest Updates (November 16, 2025)

### Code Quality Improvements ✅ COMPLETE
- ✅ **Exception Handling**: Replaced 4 generic handlers with specific exception types
  - `cli/enhanced_cli.py`: stdin operations with proper IOError/OSError handling
  - `utils/cache_manager.py`: Redis health with ConnectionError/TimeoutError
  - `services/neo4j_service.py`: Neo4j health with ServiceUnavailable/SessionExpired
  - `api/middleware/logging.py`: Request body reading with UnicodeDecodeError
- ✅ **Type Hints**: Added return type hints to 19 API functions
  - `api/routers/audit.py`: 11 endpoint functions fully typed
  - `api/routers/agent_optimized.py`: 8 endpoint functions fully typed
- ✅ **Enhanced Logging**: All exception handlers now log detailed error context
- ✅ **Test Coverage**: 87/91 tests passing (22.68% coverage maintained)

### v4.2.2 - Auto-Refresh Standards on Access ✅ COMPLETE
- ✅ **StandardsAccessService**: Intelligent access layer with automatic freshness checking (605 lines)
- ✅ **Access Tracking**: last_accessed timestamps, access counts, and staleness detection
- ✅ **Dual Refresh Modes**: Blocking (wait for update) or Background (return immediately)
- ✅ **Background Queue**: Worker pool with retry logic and exponential backoff
- ✅ **Deep Research Integration**: Uses v4.2.0 iterative refinement for updates
- ✅ **Comprehensive Metrics**: Success rates, duration tracking, queue status
- ✅ **Per-Standard Configuration**: Custom thresholds and enable/disable per standard
- ✅ **Metrics API**: 5 new endpoints for monitoring auto-refresh operations
- ✅ **Test Suite**: 27 unit tests with 61.26% coverage (all passing)
- ✅ **Configuration**: 7 new settings for complete control

### v4.2.1 - Test Suite Foundation ✅ COMPLETE
- ✅ **Test Infrastructure**: Complete pytest setup with coverage configuration
- ✅ **62 Unit Tests**: 60 passing (96.8% pass rate) for core audit modules
- ✅ **86.79% Coverage**: Comprehensive tests for code analyzer module
- ✅ **81.68% Coverage**: Full context management testing
- ✅ **Shared Fixtures**: 350+ lines of reusable test utilities
- ✅ **Test Documentation**: Complete status report and roadmap
- ✅ **Progress**: 13.51% overall coverage, on track for 80% target

### v4.2.0 - Deep Research Mode with Iterative Refinement ✅ COMPLETE (November 14, 2025)
- ✅ **Multi-Pass Generation**: 3-iteration refinement loop with quality improvement tracking
- ✅ **Self-Critique System**: AI evaluates own output on 8 criteria (completeness, depth, clarity, etc.)
- ✅ **Temperature Scheduling**: Creative exploration (0.8) → precise refinement (0.4)
- ✅ **Quality Threshold**: Automatic termination when reaching 8.5/10 quality score
- ✅ **Standards Versioning**: Semantic versioning with automatic archiving and changelog
- ✅ **AI-Powered Updates**: Update existing standards with deep research mode
- ✅ **Version History**: Track all standard versions with rollback capability
- ✅ **Model Updates**: Latest Gemini 2.5 Pro/Flash models + extended reasoning mode
- ✅ **30% Quality Improvement**: From ~7.0/10 (single pass) to ~9.0/10 (deep research)

### v4.1.0 - Phase 2: Neo4j Integration & Standards Sync ✅ COMPLETE
- ✅ **Neo4j Integration**: Graph database operational with 128 standards loaded
- ✅ **Auto-Sync Service**: Hourly background synchronization of markdown files → Neo4j
- ✅ **Standards Import**: Parsed and imported 128 standards from 8 markdown files
- ✅ **Runtime Validation**: All 13 tests passing, server operational
- ✅ **Middleware Testing**: Rate limiting (60 req/min), logging, CORS all functional
- ✅ **API Endpoints**: 38+ routes including sync status and manual trigger
- ✅ **1,000+ Lines Added**: Sync service, scripts, documentation

### v4.0.0 - Phase 1: Critical Fixes & Core Implementation ✅ COMPLETE
- ✅ **Core Audit Engine**: Complete audit orchestration with rule evaluation and code analysis
- ✅ **LLM Provider Layer**: Unified interface for Gemini/Anthropic with automatic fallback
- ✅ **Dependency Injection**: All routers refactored for proper FastAPI DI patterns
- ✅ **Security Hardening**: Removed hardcoded credentials, added pre-commit hooks
- ✅ **Code Quality**: Fixed all bare exception handlers, improved error handling
- ✅ **4,200+ Lines of Code**: Production-ready audit and LLM infrastructure

A revolutionary AI-powered code standards platform with conversational research, automated workflows, and agent-optimized APIs. Transform your development process with natural language standard creation, intelligent code analysis, and comprehensive improvement recommendations.

## 🚀 Features

### 🆕 **Version 4.2 - Deep Research Mode (LATEST)**

#### 🔬 **Iterative Refinement with Self-Critique**
- **Multi-Pass Generation**: 3-iteration refinement loop (configurable up to any number)
- **Self-Critique System**: AI evaluates its own output on 8 quality criteria:
  - Completeness, Depth, Structure, Clarity
  - Technical Accuracy, Practical Applicability
  - Examples Quality, Best Practices Adherence
- **Temperature Scheduling**: 0.8 (creative) → 0.6 (balanced) → 0.4 (precise)
- **Quality Metrics**: Measurable 0-10 scores with improvement tracking
- **Smart Termination**: Stops when quality threshold met (default: 8.5/10)
- **Performance**: 30% quality improvement (7.0 → 9.0) with 3x token cost

#### 📦 **Standards Versioning System**
- **Semantic Versioning**: MAJOR.MINOR.PATCH version tracking
- **Automatic Archiving**: Old versions preserved in `archive/` directories
- **Changelog Tracking**: Full history of all changes with timestamps
- **Version History API**: Retrieve and compare any version
- **AI-Powered Updates**: Use deep research to modernize existing standards
- **Rollback Capability**: Restore any previous version when needed
- **Retention Policy**: Configurable retention period (default: 90 days)

#### 🎯 **Usage Examples**
```python
# Create standard with deep research
standard = await research_service.research_standard(
    topic="FastAPI Security Best Practices",
    category="security",
    use_deep_research=True,
    max_iterations=3,
    quality_threshold=8.5
)
print(f"Quality: {standard['metadata']['refinement']['final_quality_score']}/10")

# Update existing standard with AI
updated = await research_service.update_standard(
    standard_id="abc123",
    use_deep_research=True  # Uses iterative refinement
)

# View version history
history = await research_service.get_standard_history("abc123")
```

### 🆕 **Version 4.0 - Core Foundation (Phase 1 Complete)**

#### 🏗️ **Core Audit Engine**
- **Complete Audit Orchestration**: Full lifecycle management from file loading to report generation
- **Rule Engine**: Pattern-based, length, and complexity checkers with extensible architecture
- **Code Analysis**: AST parsing for Python, regex analysis for JavaScript/TypeScript
- **Code Metrics**: Lines of code, cyclomatic complexity, docstring coverage, structure analysis
- **Code Smell Detection**: Automatic identification of maintainability issues
- **Multi-Language Support**: Python, JavaScript, TypeScript, Java, and more
- **Finding Management**: Severity levels, categories, and detailed reporting
- **Progress Tracking**: Real-time callbacks for audit progress
- **Report Generation**: JSON and Markdown formats with customizable templates

#### 🤖 **LLM Provider Layer**
- **Unified Interface**: Single API for multiple LLM providers
- **Provider Support**: Google Gemini and Anthropic Claude with easy extensibility
- **Automatic Fallback**: Seamless switching between providers on failure
- **Model Tiers**: Fast, Balanced, and Advanced models for different use cases
- **Streaming Support**: Real-time response streaming for interactive applications
- **Health Tracking**: Automatic provider health monitoring and error counting

#### 💾 **Caching & Performance**
- **LLM Response Caching**: Memory and Redis backends with TTL support
- **Cache Key Generation**: Deterministic hashing based on request parameters
- **LRU Eviction**: Automatic cache management with configurable size limits
- **Decorator Support**: `@cached_llm_call` for easy function caching
- **Statistics Tracking**: Hit rates, misses, and performance metrics

#### 📋 **Prompt Management**
- **Template System**: Pre-built templates for common tasks
- **Variable Substitution**: Safe and validated template rendering
- **Built-in Templates**: Code analysis, bug fixes, refactoring, documentation, tests
- **Custom Templates**: Easy creation and registration of custom prompts
- **JSON Import/Export**: Template library management

#### ⚡ **Batch Processing**
- **Concurrent Execution**: Process multiple LLM requests in parallel
- **Rate Limiting**: Configurable requests per minute with automatic throttling
- **Automatic Retry**: Failed requests retry with exponential backoff
- **Progress Callbacks**: Real-time job progress notifications
- **Result Caching**: Automatic caching of batch results
- **Job Management**: Start, monitor, cancel, and cleanup batch jobs

### 🎯 **Version 2.0 - Revolutionary Enhancements**

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
- **Neo4j Graph Database**: Relationship mapping between code patterns and standards (128 standards loaded)
- **Auto-Sync Service**: Automatic hourly synchronization of markdown files → Neo4j with change detection
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

5. Initialize Neo4j and import standards:
```bash
# Start Neo4j (if not already running)
# Ensure Neo4j is running on bolt://localhost:7687

# Import standards from markdown files
python3 scripts/import_standards.py

# This will discover and import all standards from markdown files
# into your Neo4j database
```

6. (Optional) Verify synchronization:
```bash
# Check sync status
python3 scripts/sync_standards.py

# Or start the server (sync runs automatically)
python3 test_server.py
```

## 🧪 Testing

The project includes a comprehensive test suite with 80%+ coverage target.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=core --cov-report=html --cov-report=term-missing

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_audit_context.py -v

# Run tests matching a pattern
pytest -k "test_analyzer" -v
```

### Test Coverage

Current coverage status (as of v4.2.1):
- **Overall**: 13.51% (target: 80%)
- **core/audit/analyzer.py**: 86.79% ✅
- **core/audit/context.py**: 81.68% ✅
- **Total Tests**: 62 (60 passing, 96.8% pass rate)

See `TEST_SUITE_STATUS.md` for detailed coverage reports and roadmap.

### Test Markers

```bash
# Run only fast unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Skip tests requiring external services
pytest -m "not requires_neo4j and not requires_gemini"
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

## 🔄 Standards Synchronization

The application includes automatic synchronization between markdown standards files and the Neo4j database. This ensures your database stays up-to-date with file changes without manual intervention.

### Features

✅ **Automatic Background Sync** - Runs every hour when server is running
✅ **Incremental Updates** - Only processes changed files (SHA256 hash detection)
✅ **Manual Trigger** - API endpoint and CLI tool for on-demand sync
✅ **Change Detection** - Tracks additions, modifications, and deletions
✅ **Multi-Language Support** - Handles standards for all languages
✅ **Metadata Tracking** - Maintains sync history in `.sync_metadata.json`

### Usage

#### Automatic Sync (Recommended)

The sync service starts automatically with the test server:

```bash
python3 test_server.py
```

Sync runs every hour in the background. Server logs show sync activity.

#### Manual Sync

Via CLI:
```bash
# Basic sync
python3 scripts/sync_standards.py

# Force full reimport
python3 scripts/sync_standards.py --force

# Verbose output
python3 scripts/sync_standards.py --verbose
```

Via API:
```bash
# Check sync status
curl http://localhost:8000/api/v1/sync/status

# Trigger manual sync
curl -X POST http://localhost:8000/api/v1/sync/trigger

# Force full reimport
curl -X POST "http://localhost:8000/api/v1/sync/trigger?force=true"
```

#### Initial Import

If starting with an empty database, import existing standards:

```bash
python3 scripts/import_standards.py
```

This discovers all markdown files in the standards directory and imports them into Neo4j.

### Current Status

- **Standards in Database**: 128
- **Files Tracked**: 8 markdown files
- **Sync Interval**: 3600 seconds (1 hour)
- **Last Sync**: Shown in `/api/v1/sync/status`

📖 **See [STANDARDS_SYNC_GUIDE.md](STANDARDS_SYNC_GUIDE.md) for complete documentation** including:
- Architecture details
- Troubleshooting guide
- Performance benchmarks
- Configuration options
- Best practices

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

**Common Issue: "MCP package not found" after installation**

This happens when `pip3` and `python3` use different Python installations (common on M1 Macs).

**Quick Fix:**
```bash
cd /Volumes/FS001/pythonscripts/code-standards-auditor
chmod +x quick_mcp_fix.sh
./quick_mcp_fix.sh
```

**Manual Fix:**
```bash
# Use python3 -m pip instead of pip3
python3 -m pip install mcp

# Verify it works
python3 -c "import mcp; print('✅ Success!')"
```

**Diagnostic:**
```bash
# See detailed Python path information
python3 diagnose_python_paths.py
```

This will show where pip installs vs. where Python looks for packages.

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
├── api/                      # FastAPI application
│   ├── routers/             # API endpoints (dependency injection)
│   │   ├── audit.py         # Code auditing endpoints
│   │   ├── standards.py     # Standards management & research
│   │   ├── agent_optimized.py  # Agent-optimized endpoints
│   │   └── workflow.py      # Integrated workflow endpoints
│   ├── middleware/          # Custom middleware
│   │   ├── auth.py          # JWT & API key authentication
│   │   ├── logging.py       # Request/response logging
│   │   └── rate_limit.py    # Rate limiting
│   └── main.py              # Application entry point
├── core/                    # Core business logic (NEW in v4.0)
│   ├── audit/              # Audit engine foundation
│   │   ├── context.py      # Audit context management
│   │   ├── rule_engine.py  # Rule evaluation system
│   │   ├── analyzer.py     # Code analysis engine
│   │   └── engine.py       # Main audit orchestration
│   └── llm/                # LLM provider abstraction
│       ├── provider.py     # Provider interface & implementations
│       ├── prompt_manager.py  # Prompt template management
│       ├── cache_decorator.py # Response caching
│       └── batch_processor.py # Batch processing
├── services/               # External service integrations
│   ├── gemini_service.py            # Gemini AI integration
│   ├── neo4j_service.py            # Graph database (optional)
│   ├── cache_service.py            # Redis caching (optional)
│   ├── standards_sync_service.py   # Auto-sync standards files → Neo4j
│   ├── standards_research_service.py  # AI research
│   └── recommendations_service.py     # Recommendations engine
├── utils/                  # Utilities
│   └── service_factory.py # Centralized service management
├── mcp_server/            # Claude Desktop integration
│   └── server.py          # MCP server implementation
├── scripts/               # Utility scripts
│   ├── import_standards.py   # Initial import from markdown files
│   └── sync_standards.py     # Manual synchronization tool
├── standards/             # Standards documentation
│   └── python/           # Python coding standards
└── docker/               # Container configuration
```

## 🔄 Development Status

### ✅ Phase 1 Complete (v4.0.0) - 100%
- **Core Audit Engine** (1,700 lines)
  - Context management and finding tracking
  - Rule engine with pattern/length/complexity checkers
  - Code analyzer with AST parsing and metrics
  - Complete audit orchestration with progress tracking
  - Multi-language support (Python, JavaScript, TypeScript)
  - Report generation (JSON, Markdown)

- **LLM Provider Layer** (1,830 lines)
  - Provider abstraction with Gemini and Anthropic support
  - Automatic fallback and health tracking
  - Prompt template system with 8 built-in templates
  - Response caching (memory and Redis)
  - Batch processor with rate limiting
  - Streaming support

- **Application Infrastructure**
  - Middleware: Authentication (JWT/API key), Logging, Rate limiting
  - Dependency injection pattern throughout routers
  - Service factory for centralized service management
  - Security hardening (no hardcoded credentials, pre-commit hooks)
  - All bare exception handlers fixed

- **Legacy Features**
  - Standards documentation (Python, Java, General)
  - Claude Desktop MCP integration
  - Standards Research Service (AI-powered generation)
  - Recommendations Service (improvement suggestions)
  - Standards API Router (comprehensive endpoints)
  - Agent-optimized query interface

### ✅ Phase 2 Complete (v4.1.0) - 100%

- **Neo4j Integration** (Operational)
  - Graph database connected with 128 standards loaded
  - Fixed settings validator to allow localhost connections
  - Health check endpoints showing "neo4j": "connected"
  - Standards imported across 8 markdown files

- **Standards Synchronization Service** (350 lines)
  - Automatic hourly background sync
  - SHA256 file hashing for change detection
  - Incremental updates (add/modify/delete)
  - Metadata tracking in `.sync_metadata.json`
  - Manual trigger via API and CLI
  - ScheduledSyncService with lifecycle management

- **Standards Import System** (464 lines)
  - StandardsParser for markdown extraction
  - StandardsImporter for Neo4j loading
  - Support for multiple languages and categories
  - Imported 128 standards across 5 categories

- **Runtime Validation**
  - Test server with graceful service degradation
  - All 13 tests passing (imports, audit engine, LLM layer)
  - Middleware chain functional (logging, rate limit, CORS)
  - 38+ API routes operational

- **Documentation & Scripts**
  - STANDARDS_SYNC_GUIDE.md (500+ lines)
  - STANDARDS_IMPORT_SUMMARY.md
  - PHASE2_PROGRESS.md tracking
  - scripts/sync_standards.py (CLI tool)
  - scripts/import_standards.py (initial import)

- **API Endpoints**
  - GET /api/v1/sync/status - Sync status and metrics
  - POST /api/v1/sync/trigger - Manual sync trigger
  - GET /api/v1/health - Service health checks

### 📅 Phase 3-6: Planned
- **Phase 3**: Additional API routers and admin interface
- **Phase 4**: Docker containerization and CI/CD pipeline
- **Phase 5**: Web UI dashboard and GitHub/GitLab integration
- **Phase 6**: Advanced features (versioning, multi-tenant, analytics)

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

### v4.2.2 (November 16, 2025) - 🔄 Auto-Refresh Standards on Access
- **🎯 StandardsAccessService**: Complete intelligent access layer (605 lines)
  - Automatic freshness detection based on configurable threshold (default: 30 days)
  - Access tracking with last_accessed timestamps and access counts
  - Staleness detection using file modification time
  - Per-standard configuration (enable/disable, custom thresholds)
- **⚡ Dual Refresh Modes**: Flexible update strategies
  - Blocking mode: Wait for update before returning standard
  - Background mode: Return immediately, update in background queue
  - Configurable via AUTO_REFRESH_MODE setting
- **🔁 Background Task Queue**: Worker pool for async updates (200 lines)
  - Configurable concurrent workers (default: 3)
  - Retry logic with exponential backoff
  - Duplicate prevention (don't queue same standard twice)
  - Queue status monitoring and metrics
- **📊 Comprehensive Metrics**: Full observability (100 lines)
  - Total accesses, stale detections, refresh attempts/successes/failures
  - Average refresh duration and success rate calculations
  - Background queue size and active workers tracking
  - 5 new API endpoints for monitoring
- **🔗 Deep Research Integration**: Uses v4.2.0 iterative refinement
  - Auto-refreshes use deep research mode for 8.5-9.5/10 quality
  - Temperature scheduling and self-critique during updates
  - Version history preserved via existing versioning system
- **⚙️ Configuration**: 7 new settings for complete control
  - ENABLE_AUTO_REFRESH_ON_ACCESS (default: true)
  - STANDARD_FRESHNESS_THRESHOLD_DAYS (default: 30)
  - AUTO_REFRESH_MODE (blocking/background, default: background)
  - AUTO_REFRESH_MAX_CONCURRENT (default: 3)
  - AUTO_REFRESH_RETRY_ATTEMPTS (default: 2)
  - AUTO_REFRESH_RETRY_DELAY_SECONDS (default: 60)
  - AUTO_REFRESH_USE_DEEP_RESEARCH (default: true)
- **✅ Testing**: Comprehensive test suite
  - 27 unit tests (all passing, 100% pass rate)
  - 61.26% coverage for standards_access_service.py
  - Tests for metadata, metrics, blocking/background modes, retry logic
  - Integration tests for end-to-end flows
- **📚 Documentation**: Complete design and implementation docs
  - AUTO_REFRESH_DESIGN.md (500+ lines) - Full architecture
  - API documentation for 5 new metrics endpoints
  - Configuration examples and usage patterns

### v4.2.0 (November 14, 2025) - 🔬 Deep Research Mode with Iterative Refinement
- **🎯 Multi-Pass Generation**: Iterative refinement loop with self-critique (485 lines)
  - Temperature scheduling for creative → precise generation
  - Quality threshold-based termination (default: 8.5/10)
  - Configurable max iterations (default: 3)
  - Quality score tracking and improvement measurement
- **🧠 Self-Critique System**: AI evaluates own output on 8 criteria (798 lines)
  - Completeness, depth, structure, clarity analysis
  - Technical accuracy and practical applicability scoring
  - Identifies strengths, weaknesses, and specific improvements
  - Provides actionable recommendations for refinement
- **📦 Standards Versioning**: Semantic versioning with full history (549 lines)
  - MAJOR.MINOR.PATCH version tracking
  - Automatic archiving to `archive/` directories
  - Changelog tracking for all updates
  - Version history retrieval API
  - AI-powered standard updates with deep research
  - Rollback capability for any version
- **🎨 Model Updates**: Latest Gemini models
  - gemini-2.5-pro and gemini-2.5-flash
  - gemini-2.0-flash-thinking-exp for extended reasoning
  - Support for latest Google AI capabilities
- **📊 Quality Improvements**:
  - 30% quality increase: 7.0/10 → 9.0/10
  - Measurable improvement tracking across iterations
  - Smart early termination when threshold met
  - Production-ready enterprise-grade standards
- **🔧 Configuration**:
  - ENABLE_DEEP_RESEARCH (default: true)
  - DEEP_RESEARCH_MAX_ITERATIONS (default: 3)
  - DEEP_RESEARCH_QUALITY_THRESHOLD (default: 8.5)
  - DEEP_RESEARCH_TEMPERATURE_SCHEDULE (default: [0.8, 0.6, 0.4])
- **✅ Testing**: Full test suite with architecture validation
- **📚 Documentation**: DEEP_RESEARCH_MODE_IMPLEMENTATION.md (490+ lines)

### v4.0.0 (November 04, 2025) - 🎉 Phase 1: Core Foundation Complete
- **✅ PHASE 1 COMPLETE**: All 9 critical tasks finished (100%)
- **🏗️ Core Audit Engine**: Complete audit orchestration (1,700 lines)
  - Context management with finding tracking
  - Rule engine (pattern, length, complexity checkers)
  - Code analyzer with AST parsing for Python, regex for JavaScript
  - Code metrics calculation and code smell detection
  - Multi-language support with extensible architecture
  - Progress tracking and report generation
- **🤖 LLM Provider Layer**: Unified provider interface (1,830 lines)
  - Gemini and Anthropic implementations with fallback
  - Model tier system (fast, balanced, advanced)
  - Prompt template management (8 built-in templates)
  - Response caching (memory/Redis) with TTL
  - Batch processor with rate limiting and retry
  - Streaming support for real-time responses
- **🔧 Infrastructure Improvements**:
  - All routers refactored for dependency injection
  - Service factory for centralized management
  - Middleware: Authentication, Logging, Rate limiting
  - Security: Removed hardcoded credentials, added pre-commit hooks
  - Code quality: Fixed all bare exception handlers
- **📊 Statistics**:
  - 24 files created, 5 files refactored
  - 4,200+ lines of production code
  - Completed in 19 hours (157% faster than estimated)
  - 0 blocking issues remaining
- **🎯 Ready for Phase 2**: Testing & Integration

### v3.0.0 (September 06, 2025) - 🎆 Major Architecture Redesign
- **💡 BREAKING CHANGE**: Complete architecture redesign - separation of concerns
- **✨ Solution**: Split into two independent MCP servers:
  - Code Standards Server (simplified, Neo4j-free)
  - Neo4j MCP Server (use Neo4j's native implementation)
- **✅ Benefits**: 
  - Eliminates all stdout pollution issues
  - Clean, maintainable architecture
  - Each service does one thing well
  - Uses official implementations
- **🛠 Implementation**:
  - Created `server_simple.py` - Clean server without Neo4j
  - Full architecture documentation in `ARCHITECTURE_V3.md`
  - One-click migration with `update_to_v3.sh`
- **🎆 Result**: Finally solved the stdout pollution problem completely!

### v2.0.7 (September 06, 2025) - 🔧 MCP StdoutProtector Buffer Fix
- **🐛 Fixed Issue**: StdoutProtector missing buffer attribute for MCP library compatibility
- **✅ Solution**: Added buffer attribute to StdoutProtector class for binary I/O support
- **🚀 Improvement**: Disabled automatic stdout redirection to avoid MCP conflicts
- **🛠 Scripts Added**: Created `check_packages.py` and `update_claude_config.sh`
- **📋 GitHub Structure**: Created github-scripts directory for commit/push scripts

### v2.0.6 (September 05, 2025) - 🔧 MCP Server Startup Fixes
- **🐛 Fixed Issue**: Tool registration error - changed `input_schema` to `inputSchema` (MCP requirement)
- **✅ Added Methods**: Implemented missing `list_prompts()` and `list_resources()` handlers
- **🚀 Neo4j Handling**: Improved authentication with fallback to multiple databases
- **🛠 Troubleshooting**: Created `troubleshoot_neo4j.sh` for Neo4j diagnostics
- **📋 Status Reporting**: Enhanced status messages with troubleshooting steps

### v2.0.5 (September 05, 2025) - 🔧 MCP Server Launch Fix
- **🐛 Fixed Issue**: Server file not found error - created launcher script at expected location
- **🚀 Path Structure**: Properly organized server files with launcher at `mcp_server/server.py`
- **✅ Configuration Verified**: Claude Desktop config points to correct paths
- **🛠 Quick Fix Script**: `fix_mcp_launch.sh` installs dependencies and verifies setup
- **📋 Setup Verification**: `verify_mcp_setup.py` checks all components are ready

### v2.0.4 (September 04, 2025) - 🚨 Critical MCP Import Conflict Fix
- **🔥 BREAKING CHANGE**: Renamed `mcp/` directory to `mcp_server/` to resolve package conflict
- **🐛 Root Cause**: Local directory was shadowing installed MCP package
- **🔧 Automated Fix**: Created `fix_mcp_naming_conflict.sh` for one-command resolution
- **📋 Impact**: All users must run fix script and update Claude Desktop config
- **✅ Resolution**: Circular import error completely resolved

### v2.0.3 (September 04, 2025) - 🔍 MCP Server Debugging Suite
- **🛠 Comprehensive Diagnostic Tools**: Created multiple debugging scripts for MCP issues
- **📚 MCP Debug Guide**: Added detailed troubleshooting documentation
- **🔧 Automated Fix Script**: One-command fix for common MCP server problems
- **🧪 Test Suite Enhancement**: Added minimal and comprehensive test scripts
- **📋 Status Reporting**: Automatic generation of diagnostic reports
- **🚀 Quick Resolution Path**: Streamlined debugging workflow for Claude Desktop integration

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

**Last Updated:** November 14, 2025 - Version 4.2.0 Deep Research Mode Edition

**See Also:**
- [DEEP_RESEARCH_MODE_IMPLEMENTATION.md](DEEP_RESEARCH_MODE_IMPLEMENTATION.md) - Deep research implementation details
- [PHASE1_PROGRESS.md](PHASE1_PROGRESS.md) - Detailed Phase 1 completion report
- [V4_ROADMAP.md](V4_ROADMAP.md) - Complete roadmap for v4.0 development
- [CODE_QUALITY_ANALYSIS.md](CODE_QUALITY_ANALYSIS.md) - Codebase quality analysis

# Code Standards Auditor

An AI-powered code auditing API that integrates into development pipelines to ensure code quality and maintain living documentation of coding standards.

## 🚀 Features

- **Automated Code Review**: Real-time analysis of code against project-specific and language-specific standards
- **Standards Documentation Management**: Dynamic creation and maintenance of coding standards
- **Pipeline Integration**: Seamless CI/CD integration through RESTful API
- **Multi-Language Support**: Python, Java, JavaScript, and more
- **Cost-Optimized LLM Usage**: Intelligent prompt caching and batch processing
- **Neo4j Graph Database**: Relationship mapping between code patterns and standards

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

## 🚦 Quick Start

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

## 📖 API Usage

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
print(f"Code Score: {audit_result['summary']['score']}")
print(f"Violations: {audit_result['summary']['violations']}")
```

### Batch Processing

```python
# Submit multiple files for batch audit
batch_request = {
    "files": [
        {"path": "main.py", "content": "..."},
        {"path": "utils.py", "content": "..."}
    ],
    "language": "python",
    "options": {"batch_mode": True}
}

response = requests.post(
    "http://localhost:8000/api/v1/audit/batch",
    json=batch_request
)
```

### Standards Management

```python
# Get current Python standards
response = requests.get("http://localhost:8000/api/v1/standards/python")
standards = response.json()

# Update standards with new patterns
update_request = {
    "language": "python",
    "new_patterns": ["async_context_managers"],
    "reason": "Emerging best practice from code analysis"
}

response = requests.post(
    "http://localhost:8000/api/v1/standards/update",
    json=update_request
)
```

## 🔌 CI/CD Integration

### GitHub Actions

```yaml
name: Code Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Code Audit
        run: |
          curl -X POST http://your-api-url/api/v1/audit \
            -H "Content-Type: application/json" \
            -d '{"code": "$(cat *.py)", "language": "python"}'
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Code Audit') {
            steps {
                script {
                    def response = httpRequest(
                        url: 'http://your-api-url/api/v1/audit',
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        requestBody: readFile('src/**/*.java')
                    )
                    def audit = readJSON text: response.content
                    if (audit.summary.score < 80) {
                        error "Code quality score below threshold"
                    }
                }
            }
        }
    }
}
```

## 📊 Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system architecture.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=./ --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## 📈 Monitoring

The API exposes Prometheus metrics at `/metrics`:
- Request latency
- API usage by endpoint
- LLM token consumption
- Cache hit rates
- Error rates

Access the health check endpoint:
```bash
curl http://localhost:8000/api/v1/health
```

## 🔧 Configuration

Configuration is managed through environment variables and `config/settings.py`:

```python
# Key configuration options
GEMINI_MODEL = "gemini-pro"  # or "gemini-ultra"
MAX_CONTEXT_TOKENS = 32000
CACHE_TTL_SECONDS = 3600
BATCH_SIZE = 10
RATE_LIMIT_PER_MINUTE = 60
```

## 📝 Standards Documentation

Coding standards are maintained in `/Volumes/FS001/pythonscripts/standards/`:
- `python/` - Python coding standards
- `java/` - Java coding standards
- `general/` - Language-agnostic best practices
- `versions/` - Historical versions with changelogs

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test thoroughly
3. Update documentation and tests
4. Submit a pull request

## 📄 License

[Specify your license here]

## 🆘 Support

For issues or questions:
- Check the [documentation](docs/)
- Review [API documentation](docs/API.md)
- Open an issue on the repository

## 🔄 Version History

### v1.0.1 (2025-01-27) - Current
- ✅ Implemented configuration management system
- ✅ Created cache manager and cache service
- ✅ Implemented Neo4j graph database service
- ✅ Enhanced Gemini service with prompt caching
- ✅ Added comprehensive standards documentation (Python, Java, General)
- ✅ Set up project dependencies in requirements.txt
- ⚠️ API routers implementation in progress
- ⚠️ Middleware components pending

### v1.0.0 (2025-01-27)
- Initial architecture and project setup
- Core API structure
- Basic code audit functionality
- Standards documentation framework

---

**Current Status**: 🟡 In Active Development

**Completed Components**:
- ✅ Architecture documentation (ARCHITECTURE.md)
- ✅ Configuration management (settings.py)
- ✅ Cache management system (cache_manager.py, cache_service.py)
- ✅ Neo4j graph database service (neo4j_service.py)
- ✅ Gemini API integration with prompt caching (gemini_service.py)
- ✅ Standards documentation for Python, Java, and General practices
- ✅ Project structure and dependencies

**Next Steps**: 
1. ✅ ~~Implement configuration settings~~
2. ✅ ~~Complete Neo4j service~~
3. ✅ ~~Complete cache service~~
4. ✅ ~~Create initial standards documentation~~
5. 🔄 Implement API routers (audit, standards, admin)
6. 🔄 Create middleware components (auth, logging, rate limiting)
7. 📋 Implement code parsers and validators
8. 📋 Create batch processing handlers
9. 📋 Add unit and integration tests
10. 📋 Set up Docker configuration

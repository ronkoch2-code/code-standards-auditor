"""
Pytest Configuration and Shared Fixtures

This module provides shared fixtures and configuration for all tests.
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import tempfile
import shutil

# Mock services to avoid external dependencies
from unittest.mock import MagicMock, AsyncMock


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, require services)"
    )
    config.addinivalue_line(
        "markers", "requires_gemini: Tests requiring Gemini API"
    )
    config.addinivalue_line(
        "markers", "requires_neo4j: Tests requiring Neo4j"
    )
    config.addinivalue_line(
        "markers", "requires_redis: Tests requiring Redis"
    )


# ============================================================================
# Event Loop Fixture
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file for testing."""
    file_path = temp_dir / "sample.py"
    content = '''"""Sample module for testing."""

def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"


class Calculator:
    """Simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b


# This is a code smell - function too long
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                result = x + y + z
                if result > 100:
                    return result * 2
                else:
                    return result
            else:
                return x + y
        else:
            return x
    else:
        return 0
'''
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_javascript_file(temp_dir):
    """Create a sample JavaScript file for testing."""
    file_path = temp_dir / "sample.js"
    content = '''// Sample JavaScript module

function greet(name) {
    return `Hello, ${name}!`;
}

class Calculator {
    add(a, b) {
        return a + b;
    }

    subtract(a, b) {
        return a - b;
    }
}

// Complex function with high cyclomatic complexity
function complexFunction(x, y, z) {
    if (x > 0) {
        if (y > 0) {
            if (z > 0) {
                const result = x + y + z;
                if (result > 100) {
                    return result * 2;
                } else {
                    return result;
                }
            } else {
                return x + y;
            }
        } else {
            return x;
        }
    } else {
        return 0;
    }
}

export { greet, Calculator, complexFunction };
'''
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_code_with_issues(temp_dir):
    """Create a Python file with common code quality issues."""
    file_path = temp_dir / "bad_code.py"
    content = '''
# Missing docstrings
def function_without_docstring(x, y):
    return x + y

# Very long line
very_long_variable_name = "This is a very long string that exceeds the recommended line length of 120 characters and should be flagged by the linter for being too long"

# High complexity
def high_complexity_function(a, b, c, d, e):
    if a and b:
        if c or d:
            if e:
                for i in range(10):
                    if i % 2 == 0:
                        while True:
                            break
    return None

# Missing type hints
def no_type_hints(param1, param2):
    return param1 + param2
'''
    file_path.write_text(content)
    return file_path


# ============================================================================
# Core Module Fixtures
# ============================================================================

@pytest.fixture
def sample_audit_config():
    """Sample audit configuration."""
    return {
        "severity_threshold": "info",
        "enable_metrics": True,
        "max_file_size": 1000000,
        "excluded_patterns": ["*.pyc", "__pycache__"],
        "languages": ["python", "javascript"],
    }


@pytest.fixture
def sample_standard():
    """Sample coding standard."""
    return {
        "id": "PY001",
        "name": "Python Docstring Standard",
        "description": "All public functions must have docstrings",
        "language": "python",
        "category": "documentation",
        "severity": "medium",
        "rule": {
            "type": "pattern",
            "pattern": r"def\s+\w+\([^)]*\):",
            "check": "has_docstring"
        }
    }


@pytest.fixture
def sample_finding():
    """Sample audit finding."""
    from core.audit.context import AuditFinding, AuditSeverity, AuditCategory

    return AuditFinding(
        id="test_finding_001",
        severity=AuditSeverity.MEDIUM,
        category=AuditCategory.STYLE,
        message="Line exceeds maximum length",
        file_path=Path("test.py"),
        line_number=42,
        suggestion="Break line into multiple lines"
    )


# ============================================================================
# Service Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_gemini_service():
    """Mock Gemini service for testing."""
    service = MagicMock()
    service.analyze_code = AsyncMock(return_value={
        "quality_score": 8.5,
        "issues": [],
        "suggestions": ["Consider adding type hints"]
    })
    service.generate_content_async = AsyncMock(return_value={
        "text": "Sample generated content",
        "metadata": {}
    })
    return service


@pytest.fixture
def mock_neo4j_service():
    """Mock Neo4j service for testing."""
    service = MagicMock()
    service.create_standard = AsyncMock(return_value="std_001")
    service.get_standard = AsyncMock(return_value={
        "id": "std_001",
        "name": "Test Standard",
        "content": "Test content"
    })
    service.track_violation = AsyncMock(return_value="vio_001")
    service.close = AsyncMock()
    return service


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    service = MagicMock()
    cache_data = {}

    async def mock_get(key):
        return cache_data.get(key)

    async def mock_set(key, value, ttl=None):
        cache_data[key] = value
        return True

    service.get_audit_result = AsyncMock(side_effect=mock_get)
    service.set_audit_result = AsyncMock(side_effect=mock_set)
    return service


# ============================================================================
# API Testing Fixtures
# ============================================================================

@pytest.fixture
def mock_request():
    """Mock FastAPI Request object."""
    request = MagicMock()
    request.url.path = "/api/v1/test"
    request.method = "GET"
    request.headers = {}
    request.state.user = {"user_id": "test_user"}
    return request


@pytest.fixture
def api_test_client():
    """Create a test client for API testing."""
    from fastapi.testclient import TestClient
    from api.main import app

    with TestClient(app) as client:
        yield client


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_code_metrics():
    """Sample code metrics for testing."""
    from core.audit.analyzer import CodeMetrics

    return CodeMetrics(
        total_lines=100,
        code_lines=70,
        comment_lines=20,
        blank_lines=10,
        cyclomatic_complexity=15,
        cognitive_complexity=18,
        function_count=5,
        class_count=2,
        import_count=8,
        docstring_coverage=0.8,
        avg_function_length=14.0,
        max_function_length=25,
        avg_line_length=45.5,
        max_line_length=120
    )


@pytest.fixture
def sample_llm_response():
    """Sample LLM response for testing."""
    return {
        "id": "resp_001",
        "model": "gemini-1.5-pro",
        "created": datetime.now().isoformat(),
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "This is a sample response"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Reset audit engine singleton
    from core.audit import engine
    if hasattr(engine, '_engine_instance'):
        engine._engine_instance = None

    yield

    # Cleanup after test
    if hasattr(engine, '_engine_instance') and engine._engine_instance:
        # Cleanup any resources
        pass


# ============================================================================
# Skip Markers for Integration Tests
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

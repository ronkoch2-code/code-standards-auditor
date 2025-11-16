"""
Unit Tests for core.audit.analyzer

Tests for code analysis functionality including metrics calculation,
AST parsing, and code smell detection.
"""

import pytest
from pathlib import Path

from core.audit.analyzer import (
    CodeMetrics,
    LanguageAnalyzer,
    PythonAnalyzer,
    JavaScriptAnalyzer,
    CodeAnalyzer
)
from core.audit.context import (
    FileContext,
    AuditContext,
    AuditSeverity,
    AuditCategory
)


# ============================================================================
# Test CodeMetrics
# ============================================================================

class TestCodeMetrics:
    """Tests for CodeMetrics dataclass."""

    def test_create_empty_metrics(self):
        """Test creating empty metrics."""
        metrics = CodeMetrics()

        assert metrics.total_lines == 0
        assert metrics.code_lines == 0
        assert metrics.comment_lines == 0
        assert metrics.blank_lines == 0
        assert metrics.cyclomatic_complexity == 0
        assert metrics.function_count == 0
        assert metrics.class_count == 0

    def test_create_complete_metrics(self):
        """Test creating metrics with all fields."""
        metrics = CodeMetrics(
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

        assert metrics.total_lines == 100
        assert metrics.code_lines == 70
        assert metrics.comment_lines == 20
        assert metrics.blank_lines == 10
        assert metrics.cyclomatic_complexity == 15
        assert metrics.function_count == 5
        assert metrics.class_count == 2
        assert metrics.docstring_coverage == 0.8
        assert metrics.max_line_length == 120

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = CodeMetrics(
            total_lines=50,
            code_lines=40,
            comment_lines=5,
            blank_lines=5
        )

        result = metrics.to_dict()

        assert isinstance(result, dict)
        assert result["total_lines"] == 50
        assert result["code_lines"] == 40
        assert result["comment_lines"] == 5
        assert result["blank_lines"] == 5


# ============================================================================
# Test LanguageAnalyzer Base Class
# ============================================================================

class TestLanguageAnalyzer:
    """Tests for base LanguageAnalyzer class."""

    @pytest.mark.asyncio
    async def test_basic_line_counting(self, sample_python_file):
        """Test basic line counting functionality."""
        analyzer = LanguageAnalyzer("generic")

        file_ctx = FileContext(
            path=sample_python_file,
            content=sample_python_file.read_text(),
            language="generic",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.total_lines > 0
        assert metrics.code_lines > 0
        assert metrics.blank_lines >= 0
        assert metrics.comment_lines >= 0

    @pytest.mark.asyncio
    async def test_empty_file_analysis(self):
        """Test analyzing an empty file."""
        analyzer = LanguageAnalyzer("generic")

        file_ctx = FileContext(
            path=Path("empty.txt"),
            content="",
            language="generic",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.total_lines == 0
        assert metrics.code_lines == 0
        assert metrics.blank_lines == 0

    @pytest.mark.asyncio
    async def test_line_length_calculation(self):
        """Test line length metrics calculation."""
        analyzer = LanguageAnalyzer("generic")

        content = "short\n" + ("x" * 150) + "\nmedium line"

        file_ctx = FileContext(
            path=Path("test.txt"),
            content=content,
            language="generic",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.max_line_length == 150
        assert metrics.avg_line_length > 0


# ============================================================================
# Test PythonAnalyzer
# ============================================================================

class TestPythonAnalyzer:
    """Tests for Python-specific code analyzer."""

    @pytest.mark.asyncio
    async def test_analyze_python_file(self, sample_python_file):
        """Test analyzing a Python file."""
        analyzer = PythonAnalyzer()

        file_ctx = FileContext(
            path=sample_python_file,
            content=sample_python_file.read_text(),
            language="python",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        # Should detect functions and classes
        assert metrics.function_count > 0
        assert metrics.class_count > 0
        assert metrics.total_lines > 0

    @pytest.mark.asyncio
    async def test_function_detection(self):
        """Test detection of Python functions."""
        analyzer = PythonAnalyzer()

        content = '''
def function_one():
    pass

def function_two():
    pass

async def async_function():
    pass
'''

        file_ctx = FileContext(
            path=Path("test.py"),
            content=content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.function_count == 3

    @pytest.mark.asyncio
    async def test_class_detection(self):
        """Test detection of Python classes."""
        analyzer = PythonAnalyzer()

        content = '''
class ClassOne:
    pass

class ClassTwo:
    def method(self):
        pass
'''

        file_ctx = FileContext(
            path=Path("test.py"),
            content=content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.class_count == 2
        # ClassTwo has one method
        assert metrics.function_count == 1

    @pytest.mark.asyncio
    async def test_docstring_coverage(self):
        """Test docstring coverage calculation."""
        analyzer = PythonAnalyzer()

        content = '''
def with_docstring():
    """This has a docstring."""
    pass

def without_docstring():
    pass

def another_with_docstring():
    """Another docstring."""
    pass
'''

        file_ctx = FileContext(
            path=Path("test.py"),
            content=content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.function_count == 3
        # 2 out of 3 functions have docstrings = 0.666...
        assert 0.65 < metrics.docstring_coverage < 0.67

    @pytest.mark.asyncio
    async def test_import_detection(self):
        """Test detection of imports."""
        analyzer = PythonAnalyzer()

        content = '''
import os
import sys
from pathlib import Path
from typing import Dict, List
'''

        file_ctx = FileContext(
            path=Path("test.py"),
            content=content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.import_count == 4

    @pytest.mark.asyncio
    async def test_cyclomatic_complexity(self):
        """Test cyclomatic complexity calculation."""
        analyzer = PythonAnalyzer()

        # Simple function with no branches
        simple_content = '''
def simple():
    return 42
'''

        # Complex function with many branches
        complex_content = '''
def complex(a, b, c):
    if a:
        if b:
            if c:
                while True:
                    for i in range(10):
                        if i % 2:
                            pass
    return None
'''

        simple_ctx = FileContext(
            path=Path("simple.py"),
            content=simple_content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        complex_ctx = FileContext(
            path=Path("complex.py"),
            content=complex_content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        simple_metrics = await analyzer.analyze(simple_ctx)
        complex_metrics = await analyzer.analyze(complex_ctx)

        assert simple_metrics.cyclomatic_complexity < complex_metrics.cyclomatic_complexity

    @pytest.mark.asyncio
    async def test_syntax_error_handling(self):
        """Test handling of syntax errors in Python code."""
        analyzer = PythonAnalyzer()

        content = '''
def broken_function(
    # Missing closing parenthesis
    pass
'''

        file_ctx = FileContext(
            path=Path("broken.py"),
            content=content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        # Should not raise exception, should return basic metrics
        metrics = await analyzer.analyze(file_ctx)

        # Should still count lines even if AST parsing fails
        assert metrics.total_lines > 0

    @pytest.mark.asyncio
    async def test_function_length_calculation(self):
        """Test function length metrics."""
        analyzer = PythonAnalyzer()

        content = '''
def short_function():
    return 1

def longer_function():
    x = 1
    y = 2
    z = 3
    result = x + y + z
    return result
'''

        file_ctx = FileContext(
            path=Path("test.py"),
            content=content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.function_count == 2
        assert metrics.max_function_length > 0
        assert metrics.avg_function_length > 0


# ============================================================================
# Test JavaScriptAnalyzer
# ============================================================================

class TestJavaScriptAnalyzer:
    """Tests for JavaScript/TypeScript code analyzer."""

    @pytest.mark.asyncio
    async def test_analyze_javascript_file(self, sample_javascript_file):
        """Test analyzing a JavaScript file."""
        analyzer = JavaScriptAnalyzer("javascript")

        file_ctx = FileContext(
            path=sample_javascript_file,
            content=sample_javascript_file.read_text(),
            language="javascript",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.function_count > 0
        assert metrics.class_count > 0
        assert metrics.total_lines > 0

    @pytest.mark.asyncio
    async def test_function_detection_js(self):
        """Test JavaScript function detection."""
        analyzer = JavaScriptAnalyzer("javascript")

        content = '''
function regularFunction() {}
const arrowFunc = () => {};
const funcExpression = function() {};
async function asyncFunc() {}
'''

        file_ctx = FileContext(
            path=Path("test.js"),
            content=content,
            language="javascript",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        # Should detect all function types
        assert metrics.function_count >= 3

    @pytest.mark.asyncio
    async def test_class_detection_js(self):
        """Test JavaScript class detection."""
        analyzer = JavaScriptAnalyzer("javascript")

        content = '''
class MyClass {
    constructor() {}
}

class AnotherClass extends MyClass {
    method() {}
}
'''

        file_ctx = FileContext(
            path=Path("test.js"),
            content=content,
            language="javascript",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.class_count == 2

    @pytest.mark.asyncio
    async def test_import_detection_js(self):
        """Test JavaScript import detection."""
        analyzer = JavaScriptAnalyzer("javascript")

        content = '''
import React from 'react';
import { useState } from 'react';
const fs = require('fs');
const path = require('path');
'''

        file_ctx = FileContext(
            path=Path("test.js"),
            content=content,
            language="javascript",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze(file_ctx)

        assert metrics.import_count >= 3


# ============================================================================
# Test CodeAnalyzer Main Class
# ============================================================================

class TestCodeAnalyzer:
    """Tests for main CodeAnalyzer class."""

    @pytest.mark.asyncio
    async def test_analyze_python_file(self, sample_python_file):
        """Test analyzing Python file through main analyzer."""
        analyzer = CodeAnalyzer()

        file_ctx = FileContext(
            path=sample_python_file,
            content=sample_python_file.read_text(),
            language="python",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze_file(file_ctx)

        assert isinstance(metrics, CodeMetrics)
        assert metrics.total_lines > 0

    @pytest.mark.asyncio
    async def test_analyze_javascript_file(self, sample_javascript_file):
        """Test analyzing JavaScript file through main analyzer."""
        analyzer = CodeAnalyzer()

        file_ctx = FileContext(
            path=sample_javascript_file,
            content=sample_javascript_file.read_text(),
            language="javascript",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze_file(file_ctx)

        assert isinstance(metrics, CodeMetrics)
        assert metrics.total_lines > 0

    @pytest.mark.asyncio
    async def test_analyze_unknown_language(self):
        """Test analyzing file with unknown language."""
        analyzer = CodeAnalyzer()

        file_ctx = FileContext(
            path=Path("test.xyz"),
            content="some content\nmore content",
            language="unknown",
            size_bytes=0,
            line_count=0
        )

        metrics = await analyzer.analyze_file(file_ctx)

        # Should use base analyzer and return basic metrics
        assert metrics.total_lines == 2

    @pytest.mark.asyncio
    async def test_register_custom_analyzer(self):
        """Test registering a custom language analyzer."""
        analyzer = CodeAnalyzer()

        custom_analyzer = LanguageAnalyzer("custom")
        analyzer.register_analyzer("custom", custom_analyzer)

        assert "custom" in analyzer.language_analyzers

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        analyzer = CodeAnalyzer()

        languages = analyzer.get_supported_languages()

        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages

    @pytest.mark.asyncio
    async def test_find_code_smells(self, sample_code_with_issues):
        """Test code smell detection."""
        analyzer = CodeAnalyzer()

        file_ctx = FileContext(
            path=sample_code_with_issues,
            content=sample_code_with_issues.read_text(),
            language="python",
            size_bytes=0,
            line_count=0
        )

        audit_ctx = AuditContext(
            audit_id="test_audit",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        findings = await analyzer.find_code_smells(file_ctx, audit_ctx)

        # Should detect multiple code smells
        assert len(findings) > 0

        # Check that findings have correct structure
        for finding in findings:
            assert finding.severity in AuditSeverity
            assert finding.category in AuditCategory
            assert finding.message
            assert finding.file_path == sample_code_with_issues

    @pytest.mark.asyncio
    async def test_long_function_detection(self):
        """Test detection of overly long functions."""
        analyzer = CodeAnalyzer()

        # Create a file with a very long function (>50 lines)
        long_func = "def long_func():\n" + "    pass\n" * 60

        file_ctx = FileContext(
            path=Path("long.py"),
            content=long_func,
            language="python",
            size_bytes=0,
            line_count=0
        )

        audit_ctx = AuditContext(
            audit_id="test",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        findings = await analyzer.find_code_smells(file_ctx, audit_ctx)

        # Should detect long function
        long_func_findings = [
            f for f in findings
            if "length" in f.message.lower() or "long" in f.message.lower()
        ]

        assert len(long_func_findings) > 0

    @pytest.mark.asyncio
    async def test_high_complexity_detection(self):
        """Test detection of high cyclomatic complexity."""
        analyzer = CodeAnalyzer()

        # Create highly complex function
        complex_code = '''
def complex():
    if a and b:
        if c or d:
            if e:
                while f:
                    if g:
                        if h:
                            if i:
                                pass
'''

        file_ctx = FileContext(
            path=Path("complex.py"),
            content=complex_code,
            language="python",
            size_bytes=0,
            line_count=0
        )

        audit_ctx = AuditContext(
            audit_id="test",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        findings = await analyzer.find_code_smells(file_ctx, audit_ctx)

        # Should detect high complexity
        complexity_findings = [
            f for f in findings
            if "complexity" in f.message.lower()
        ]

        assert len(complexity_findings) > 0

    @pytest.mark.asyncio
    async def test_low_docstring_coverage_detection(self):
        """Test detection of low docstring coverage."""
        analyzer = CodeAnalyzer()

        # File with low docstring coverage
        code = '''
def no_doc_1():
    pass

def no_doc_2():
    pass

def with_doc():
    """This has a docstring."""
    pass

def no_doc_3():
    pass
'''

        file_ctx = FileContext(
            path=Path("test.py"),
            content=code,
            language="python",
            size_bytes=0,
            line_count=0
        )

        audit_ctx = AuditContext(
            audit_id="test",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        findings = await analyzer.find_code_smells(file_ctx, audit_ctx)

        # Should detect low docstring coverage (25% = 1 out of 4)
        docstring_findings = [
            f for f in findings
            if "docstring" in f.message.lower()
        ]

        assert len(docstring_findings) > 0

    @pytest.mark.asyncio
    async def test_analyze_structure_python(self, sample_python_file):
        """Test analyzing Python code structure."""
        analyzer = CodeAnalyzer()

        file_ctx = FileContext(
            path=sample_python_file,
            content=sample_python_file.read_text(),
            language="python",
            size_bytes=0,
            line_count=0
        )

        structure = await analyzer.analyze_structure(file_ctx)

        assert "functions" in structure
        assert "classes" in structure
        assert "imports" in structure
        assert "dependencies" in structure

        # Should find the greet function and Calculator class
        assert len(structure["functions"]) > 0
        assert len(structure["classes"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_structure_javascript(self, sample_javascript_file):
        """Test analyzing JavaScript code structure."""
        analyzer = CodeAnalyzer()

        file_ctx = FileContext(
            path=sample_javascript_file,
            content=sample_javascript_file.read_text(),
            language="javascript",
            size_bytes=0,
            line_count=0
        )

        structure = await analyzer.analyze_structure(file_ctx)

        assert "functions" in structure
        assert "classes" in structure
        assert "imports" in structure
        assert "exports" in structure

        # Should find functions and classes
        assert len(structure["functions"]) > 0
        assert len(structure["classes"]) > 0

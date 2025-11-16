"""
Unit Tests for core.audit.context

Tests for audit context management including FileContext, AuditFinding,
and AuditContext classes.
"""

import pytest
from pathlib import Path
from datetime import datetime

from core.audit.context import (
    AuditSeverity,
    AuditCategory,
    FileContext,
    AuditFinding,
    AuditContext,
    AuditContextManager
)


# ============================================================================
# Test AuditSeverity Enum
# ============================================================================

class TestAuditSeverity:
    """Tests for AuditSeverity enum."""

    def test_severity_levels_exist(self):
        """Test that all severity levels are defined."""
        assert AuditSeverity.CRITICAL == "critical"
        assert AuditSeverity.HIGH == "high"
        assert AuditSeverity.MEDIUM == "medium"
        assert AuditSeverity.LOW == "low"
        assert AuditSeverity.INFO == "info"

    def test_severity_is_string_enum(self):
        """Test that severity enum values are strings."""
        assert isinstance(AuditSeverity.CRITICAL.value, str)
        assert AuditSeverity.CRITICAL.value == "critical"

    def test_severity_comparison(self):
        """Test severity level comparison."""
        # String comparison should work
        assert AuditSeverity.CRITICAL == "critical"
        assert AuditSeverity.HIGH != "critical"


# ============================================================================
# Test AuditCategory Enum
# ============================================================================

class TestAuditCategory:
    """Tests for AuditCategory enum."""

    def test_all_categories_exist(self):
        """Test that all categories are defined."""
        expected_categories = [
            "security",
            "performance",
            "maintainability",
            "style",
            "documentation",
            "testing",
            "architecture",
            "best_practices"
        ]

        for category in expected_categories:
            # Should not raise exception
            AuditCategory(category)

    def test_category_values(self):
        """Test category enum values."""
        assert AuditCategory.SECURITY == "security"
        assert AuditCategory.PERFORMANCE == "performance"
        assert AuditCategory.MAINTAINABILITY == "maintainability"


# ============================================================================
# Test FileContext
# ============================================================================

class TestFileContext:
    """Tests for FileContext dataclass."""

    def test_create_file_context(self):
        """Test creating a file context."""
        path = Path("/test/file.py")
        content = "def hello():\n    print('Hello')\n"

        ctx = FileContext(
            path=path,
            content=content,
            language="python",
            size_bytes=0,  # Will be calculated
            line_count=0   # Will be calculated
        )

        assert ctx.path == path
        assert ctx.content == content
        assert ctx.language == "python"
        assert ctx.line_count == 2  # Auto-calculated
        assert ctx.size_bytes > 0   # Auto-calculated
        assert ctx.encoding == "utf-8"

    def test_file_context_metadata(self):
        """Test file context metadata."""
        ctx = FileContext(
            path=Path("test.py"),
            content="test",
            language="python",
            size_bytes=4,
            line_count=1,
            metadata={"custom_field": "value"}
        )

        assert ctx.metadata["custom_field"] == "value"

    def test_file_context_auto_line_count(self):
        """Test automatic line count calculation."""
        content = "\n".join([f"line {i}" for i in range(10)])

        ctx = FileContext(
            path=Path("test.py"),
            content=content,
            language="python",
            size_bytes=0,
            line_count=0
        )

        assert ctx.line_count == 10

    def test_file_context_auto_size_bytes(self):
        """Test automatic size calculation."""
        content = "Hello, World!"

        ctx = FileContext(
            path=Path("test.py"),
            content=content,
            language="python",
            size_bytes=0,
            line_count=1
        )

        assert ctx.size_bytes == len(content.encode('utf-8'))

    def test_file_context_different_encoding(self):
        """Test file context with different encoding."""
        ctx = FileContext(
            path=Path("test.py"),
            content="test",
            language="python",
            size_bytes=0,
            line_count=1,
            encoding="latin-1"
        )

        assert ctx.encoding == "latin-1"


# ============================================================================
# Test AuditFinding
# ============================================================================

class TestAuditFinding:
    """Tests for AuditFinding dataclass."""

    def test_create_basic_finding(self):
        """Test creating a basic audit finding."""
        finding = AuditFinding(
            id="test_001",
            severity=AuditSeverity.HIGH,
            category=AuditCategory.SECURITY,
            message="SQL Injection vulnerability detected"
        )

        assert finding.id == "test_001"
        assert finding.severity == AuditSeverity.HIGH
        assert finding.category == AuditCategory.SECURITY
        assert finding.message == "SQL Injection vulnerability detected"
        assert finding.file_path is None
        assert finding.line_number is None

    def test_create_complete_finding(self):
        """Test creating a complete finding with all fields."""
        finding = AuditFinding(
            id="test_002",
            severity=AuditSeverity.MEDIUM,
            category=AuditCategory.STYLE,
            message="Line too long",
            file_path=Path("test.py"),
            line_number=42,
            column_number=80,
            code_snippet="very_long_line = 'x' * 200",
            rule_id="E501",
            suggestion="Break line into multiple lines",
            metadata={"max_length": 79, "actual_length": 200}
        )

        assert finding.line_number == 42
        assert finding.column_number == 80
        assert finding.code_snippet == "very_long_line = 'x' * 200"
        assert finding.rule_id == "E501"
        assert finding.suggestion == "Break line into multiple lines"
        assert finding.metadata["max_length"] == 79

    def test_finding_to_dict(self):
        """Test converting finding to dictionary."""
        finding = AuditFinding(
            id="test_003",
            severity=AuditSeverity.LOW,
            category=AuditCategory.DOCUMENTATION,
            message="Missing docstring",
            file_path=Path("module.py"),
            line_number=10
        )

        result = finding.to_dict()

        assert result["id"] == "test_003"
        assert result["severity"] == "low"
        assert result["category"] == "documentation"
        assert result["message"] == "Missing docstring"
        assert result["file_path"] == "module.py"
        assert result["line_number"] == 10
        assert "timestamp" in result

    def test_finding_timestamp_auto_generated(self):
        """Test that timestamp is automatically generated."""
        before = datetime.now()

        finding = AuditFinding(
            id="test_004",
            severity=AuditSeverity.INFO,
            category=AuditCategory.STYLE,
            message="Test"
        )

        after = datetime.now()

        # Parse the timestamp
        timestamp = datetime.fromisoformat(finding.timestamp)
        assert before <= timestamp <= after

    def test_finding_with_custom_metadata(self):
        """Test finding with custom metadata."""
        metadata = {
            "complexity": 15,
            "threshold": 10,
            "function_name": "complex_func"
        }

        finding = AuditFinding(
            id="test_005",
            severity=AuditSeverity.MEDIUM,
            category=AuditCategory.MAINTAINABILITY,
            message="High complexity",
            metadata=metadata
        )

        assert finding.metadata["complexity"] == 15
        assert finding.metadata["threshold"] == 10
        assert finding.metadata["function_name"] == "complex_func"


# ============================================================================
# Test AuditContext
# ============================================================================

class TestAuditContext:
    """Tests for AuditContext class."""

    def test_create_audit_context(self):
        """Test creating an audit context."""
        ctx = AuditContext(
            audit_id="audit_001",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        assert ctx.audit_id == "audit_001"
        assert ctx.status == "pending"  # Default status
        assert ctx.severity_threshold == AuditSeverity.INFO
        assert len(ctx.files) == 0
        assert len(ctx.findings) == 0
        assert len(ctx.standards) == 0

    def test_add_file_to_context(self):
        """Test adding files to audit context."""
        ctx = AuditContext(
            audit_id="audit_002",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        file_ctx = FileContext(
            path=Path("test.py"),
            content="test",
            language="python",
            size_bytes=4,
            line_count=1
        )

        ctx.add_file(file_ctx)

        assert len(ctx.files) == 1
        assert ctx.files[0] == file_ctx

    def test_add_finding_to_context(self):
        """Test adding findings to audit context."""
        ctx = AuditContext(
            audit_id="audit_003",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        finding = AuditFinding(
            id="find_001",
            severity=AuditSeverity.HIGH,
            category=AuditCategory.SECURITY,
            message="Test finding"
        )

        ctx.add_finding(finding)

        assert len(ctx.findings) == 1
        assert ctx.findings[0] == finding

    def test_add_standard_to_context(self):
        """Test adding standards to audit context."""
        ctx = AuditContext(
            audit_id="audit_004",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        standard = {
            "id": "std_001",
            "name": "Test Standard",
            "rules": []
        }

        ctx.add_standard(standard)

        assert len(ctx.standards) == 1
        assert ctx.standards[0] == standard

    def test_get_findings_by_severity(self):
        """Test filtering findings by severity."""
        ctx = AuditContext(
            audit_id="audit_005",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        # Add findings with different severities
        ctx.add_finding(AuditFinding(
            id="f1", severity=AuditSeverity.CRITICAL,
            category=AuditCategory.SECURITY, message="Critical"
        ))
        ctx.add_finding(AuditFinding(
            id="f2", severity=AuditSeverity.HIGH,
            category=AuditCategory.SECURITY, message="High"
        ))
        ctx.add_finding(AuditFinding(
            id="f3", severity=AuditSeverity.HIGH,
            category=AuditCategory.PERFORMANCE, message="High 2"
        ))
        ctx.add_finding(AuditFinding(
            id="f4", severity=AuditSeverity.LOW,
            category=AuditCategory.STYLE, message="Low"
        ))

        critical = ctx.get_findings_by_severity(AuditSeverity.CRITICAL)
        high = ctx.get_findings_by_severity(AuditSeverity.HIGH)
        low = ctx.get_findings_by_severity(AuditSeverity.LOW)

        assert len(critical) == 1
        assert len(high) == 2
        assert len(low) == 1

    def test_get_findings_by_category(self):
        """Test filtering findings by category."""
        ctx = AuditContext(
            audit_id="audit_006",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        ctx.add_finding(AuditFinding(
            id="f1", severity=AuditSeverity.HIGH,
            category=AuditCategory.SECURITY, message="Security 1"
        ))
        ctx.add_finding(AuditFinding(
            id="f2", severity=AuditSeverity.MEDIUM,
            category=AuditCategory.SECURITY, message="Security 2"
        ))
        ctx.add_finding(AuditFinding(
            id="f3", severity=AuditSeverity.LOW,
            category=AuditCategory.STYLE, message="Style"
        ))

        security = ctx.get_findings_by_category(AuditCategory.SECURITY)
        style = ctx.get_findings_by_category(AuditCategory.STYLE)

        assert len(security) == 2
        assert len(style) == 1

    def test_mark_completed(self):
        """Test marking audit as completed."""
        ctx = AuditContext(
            audit_id="audit_007",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        assert ctx.status == "pending"  # Default status
        assert ctx.completed_at is None

        ctx.mark_completed()

        assert ctx.status == "completed"
        assert ctx.completed_at is not None
        assert ctx.error_message is None

    def test_mark_completed_with_error(self):
        """Test marking audit as completed with error."""
        ctx = AuditContext(
            audit_id="audit_008",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        ctx.mark_completed(error="Test error occurred")

        assert ctx.status == "failed"
        assert ctx.error_message == "Test error occurred"
        assert ctx.completed_at is not None

    def test_audit_context_summary(self):
        """Test generating audit summary."""
        ctx = AuditContext(
            audit_id="audit_009",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        # Add some data
        ctx.add_file(FileContext(
            path=Path("file1.py"), content="test",
            language="python", size_bytes=4, line_count=1
        ))
        ctx.add_finding(AuditFinding(
            id="f1", severity=AuditSeverity.CRITICAL,
            category=AuditCategory.SECURITY, message="Critical issue"
        ))
        ctx.add_finding(AuditFinding(
            id="f2", severity=AuditSeverity.HIGH,
            category=AuditCategory.PERFORMANCE, message="Performance issue"
        ))

        summary = ctx.summary()

        assert summary["audit_id"] == "audit_009"
        assert summary["files_analyzed"] == 1  # Correct key
        assert summary["total_findings"] == 2
        assert summary["status"] == "pending"

    def test_audit_context_to_dict(self):
        """Test converting audit context to dictionary."""
        ctx = AuditContext(
            audit_id="audit_010",
            config={"test": "value"},
            severity_threshold=AuditSeverity.MEDIUM
        )

        ctx.add_file(FileContext(
            path=Path("test.py"), content="test",
            language="python", size_bytes=4, line_count=1
        ))

        result = ctx.to_dict()

        assert result["audit_id"] == "audit_010"
        assert result["config"]["test"] == "value"
        assert result["status"] == "pending"  # Default status
        assert len(result["files"]) == 1


# ============================================================================
# Test AuditContextManager
# ============================================================================

class TestAuditContextManager:
    """Tests for AuditContextManager class."""

    def test_create_context(self):
        """Test creating a new audit context."""
        manager = AuditContextManager()

        ctx = manager.create_context(
            audit_id="test_001",
            config={},
            severity_threshold=AuditSeverity.INFO
        )

        assert ctx.audit_id == "test_001"
        assert manager.get_context("test_001") == ctx

    def test_get_context(self):
        """Test retrieving an audit context."""
        manager = AuditContextManager()

        ctx1 = manager.create_context("audit_1", config={}, severity_threshold=AuditSeverity.INFO)
        ctx2 = manager.get_context("audit_1")

        assert ctx1 == ctx2

    def test_get_nonexistent_context(self):
        """Test retrieving a non-existent context."""
        manager = AuditContextManager()

        ctx = manager.get_context("nonexistent")

        assert ctx is None

    def test_list_contexts(self):
        """Test listing all context IDs."""
        manager = AuditContextManager()

        manager.create_context("audit_1", config={}, severity_threshold=AuditSeverity.INFO)
        manager.create_context("audit_2", config={}, severity_threshold=AuditSeverity.HIGH)
        manager.create_context("audit_3", config={}, severity_threshold=AuditSeverity.MEDIUM)

        audit_ids = manager.list_contexts()

        assert len(audit_ids) == 3
        assert "audit_1" in audit_ids
        assert "audit_2" in audit_ids
        assert "audit_3" in audit_ids

    def test_clear_context(self):
        """Test clearing a specific context."""
        manager = AuditContextManager()

        manager.create_context("audit_1", config={}, severity_threshold=AuditSeverity.INFO)
        manager.create_context("audit_2", config={}, severity_threshold=AuditSeverity.INFO)

        assert len(manager.list_contexts()) == 2

        manager.remove_context("audit_1")  # Correct method name

        assert len(manager.list_contexts()) == 1
        assert manager.get_context("audit_1") is None
        assert manager.get_context("audit_2") is not None

    def test_clear_all_contexts(self):
        """Test clearing all contexts."""
        manager = AuditContextManager()

        manager.create_context("audit_1", config={}, severity_threshold=AuditSeverity.INFO)
        manager.create_context("audit_2", config={}, severity_threshold=AuditSeverity.INFO)
        manager.create_context("audit_3", config={}, severity_threshold=AuditSeverity.INFO)

        # Clear all manually (no clear_all method, so remove each)
        for audit_id in list(manager.contexts.keys()):
            manager.remove_context(audit_id)

        assert len(manager.list_contexts()) == 0

    def test_clear_completed_contexts(self):
        """Test clearing only completed contexts."""
        manager = AuditContextManager()

        ctx1 = manager.create_context("audit_1", config={}, severity_threshold=AuditSeverity.INFO)
        ctx2 = manager.create_context("audit_2", config={}, severity_threshold=AuditSeverity.INFO)
        ctx3 = manager.create_context("audit_3", config={}, severity_threshold=AuditSeverity.INFO)

        # Mark some as completed
        ctx1.mark_completed()
        ctx2.mark_completed()
        # ctx3 remains in "pending" status

        cleared = manager.clear_completed_contexts(keep_recent=0)

        assert cleared == 2
        assert len(manager.list_contexts()) == 1
        assert manager.get_context("audit_3") is not None

    def test_clear_completed_keep_recent(self):
        """Test clearing completed contexts while keeping recent ones."""
        manager = AuditContextManager()

        # Create and complete multiple contexts
        for i in range(5):
            ctx = manager.create_context(f"audit_{i}", config={}, severity_threshold=AuditSeverity.INFO)
            ctx.mark_completed()

        cleared = manager.clear_completed_contexts(keep_recent=2)

        assert cleared == 3
        assert len(manager.list_contexts()) == 2

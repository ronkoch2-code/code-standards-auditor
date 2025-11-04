"""
Audit Context Management

Provides context management for code audits, including file information,
language detection, and audit metadata.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuditSeverity(str, Enum):
    """Severity levels for audit findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AuditCategory(str, Enum):
    """Categories for audit findings."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    BEST_PRACTICES = "best_practices"


@dataclass
class FileContext:
    """Context information for a file being audited."""
    path: Path
    content: str
    language: str
    size_bytes: int
    line_count: int
    encoding: str = "utf-8"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate derived properties."""
        if self.line_count == 0:
            self.line_count = len(self.content.splitlines())
        if self.size_bytes == 0:
            self.size_bytes = len(self.content.encode(self.encoding))


@dataclass
class AuditFinding:
    """Represents a single audit finding."""
    id: str
    severity: AuditSeverity
    category: AuditCategory
    message: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code_snippet: Optional[str] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "file_path": str(self.file_path) if self.file_path else None,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "code_snippet": self.code_snippet,
            "rule_id": self.rule_id,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class AuditContext:
    """
    Main audit context containing all information about an audit session.

    This class manages the state of an audit, including files being analyzed,
    standards being applied, findings, and configuration.
    """

    # Identification
    audit_id: str
    session_id: Optional[str] = None

    # Files and code
    files: List[FileContext] = field(default_factory=list)
    root_path: Optional[Path] = None

    # Standards and rules
    standards: List[Dict[str, Any]] = field(default_factory=list)
    enabled_rules: Set[str] = field(default_factory=set)
    disabled_rules: Set[str] = field(default_factory=set)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    severity_threshold: AuditSeverity = AuditSeverity.INFO

    # Results
    findings: List[AuditFinding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None

    # User context
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    project_metadata: Dict[str, Any] = field(default_factory=dict)

    def add_file(self, file_context: FileContext) -> None:
        """Add a file to the audit context."""
        self.files.append(file_context)
        logger.debug(f"Added file to audit: {file_context.path}")

    def add_finding(self, finding: AuditFinding) -> None:
        """Add a finding to the audit context."""
        self.findings.append(finding)
        logger.debug(f"Added {finding.severity.value} finding: {finding.message}")

    def add_standard(self, standard: Dict[str, Any]) -> None:
        """Add a standard to be applied during the audit."""
        self.standards.append(standard)
        logger.debug(f"Added standard: {standard.get('title', 'Unknown')}")

    def enable_rule(self, rule_id: str) -> None:
        """Enable a specific rule."""
        self.enabled_rules.add(rule_id)
        self.disabled_rules.discard(rule_id)

    def disable_rule(self, rule_id: str) -> None:
        """Disable a specific rule."""
        self.disabled_rules.add(rule_id)
        self.enabled_rules.discard(rule_id)

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled."""
        if rule_id in self.disabled_rules:
            return False
        if self.enabled_rules and rule_id not in self.enabled_rules:
            return False
        return True

    def get_findings_by_severity(self, severity: AuditSeverity) -> List[AuditFinding]:
        """Get all findings of a specific severity."""
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_category(self, category: AuditCategory) -> List[AuditFinding]:
        """Get all findings of a specific category."""
        return [f for f in self.findings if f.category == category]

    def get_findings_by_file(self, file_path: Path) -> List[AuditFinding]:
        """Get all findings for a specific file."""
        return [f for f in self.findings if f.file_path == file_path]

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate audit metrics."""
        total_findings = len(self.findings)

        severity_counts = {
            severity.value: len(self.get_findings_by_severity(severity))
            for severity in AuditSeverity
        }

        category_counts = {
            category.value: len(self.get_findings_by_category(category))
            for category in AuditCategory
        }

        total_lines = sum(f.line_count for f in self.files)
        total_files = len(self.files)

        self.metrics = {
            "total_findings": total_findings,
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "total_files_analyzed": total_files,
            "total_lines_analyzed": total_lines,
            "findings_per_file": total_findings / total_files if total_files > 0 else 0,
            "findings_per_1000_lines": (total_findings / total_lines * 1000) if total_lines > 0 else 0,
            "standards_applied": len(self.standards),
            "rules_enabled": len(self.enabled_rules) if self.enabled_rules else "all"
        }

        return self.metrics

    def mark_completed(self, error: Optional[str] = None) -> None:
        """Mark the audit as completed."""
        self.completed_at = datetime.now().isoformat()
        if error:
            self.status = "failed"
            self.error_message = error
        else:
            self.status = "completed"
        self.calculate_metrics()

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit context to dictionary."""
        return {
            "audit_id": self.audit_id,
            "session_id": self.session_id,
            "root_path": str(self.root_path) if self.root_path else None,
            "files": [
                {
                    "path": str(f.path),
                    "language": f.language,
                    "size_bytes": f.size_bytes,
                    "line_count": f.line_count
                }
                for f in self.files
            ],
            "standards": self.standards,
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics,
            "config": self.config,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "error_message": self.error_message
        }

    def summary(self) -> Dict[str, Any]:
        """Get a summary of the audit."""
        if not self.metrics:
            self.calculate_metrics()

        return {
            "audit_id": self.audit_id,
            "status": self.status,
            "total_findings": self.metrics.get("total_findings", 0),
            "critical_findings": self.metrics.get("severity_counts", {}).get("critical", 0),
            "high_findings": self.metrics.get("severity_counts", {}).get("high", 0),
            "files_analyzed": self.metrics.get("total_files_analyzed", 0),
            "lines_analyzed": self.metrics.get("total_lines_analyzed", 0),
            "duration_seconds": self._calculate_duration(),
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }

    def _calculate_duration(self) -> Optional[float]:
        """Calculate audit duration in seconds."""
        if not self.completed_at:
            return None

        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None


class AuditContextManager:
    """
    Manages multiple audit contexts and provides utilities for context operations.
    """

    def __init__(self):
        self.contexts: Dict[str, AuditContext] = {}
        self.active_context_id: Optional[str] = None

    def create_context(self, audit_id: str, **kwargs) -> AuditContext:
        """Create a new audit context."""
        context = AuditContext(audit_id=audit_id, **kwargs)
        self.contexts[audit_id] = context
        self.active_context_id = audit_id
        logger.info(f"Created audit context: {audit_id}")
        return context

    def get_context(self, audit_id: str) -> Optional[AuditContext]:
        """Get an audit context by ID."""
        return self.contexts.get(audit_id)

    def get_active_context(self) -> Optional[AuditContext]:
        """Get the currently active audit context."""
        if self.active_context_id:
            return self.contexts.get(self.active_context_id)
        return None

    def set_active_context(self, audit_id: str) -> bool:
        """Set the active audit context."""
        if audit_id in self.contexts:
            self.active_context_id = audit_id
            return True
        return False

    def remove_context(self, audit_id: str) -> bool:
        """Remove an audit context."""
        if audit_id in self.contexts:
            del self.contexts[audit_id]
            if self.active_context_id == audit_id:
                self.active_context_id = None
            logger.info(f"Removed audit context: {audit_id}")
            return True
        return False

    def list_contexts(self) -> List[str]:
        """List all audit context IDs."""
        return list(self.contexts.keys())

    def clear_completed_contexts(self, keep_recent: int = 10) -> int:
        """Clear completed audit contexts, keeping only the most recent ones."""
        completed = [
            (audit_id, ctx) for audit_id, ctx in self.contexts.items()
            if ctx.status in ["completed", "failed"]
        ]

        # Sort by completion time
        completed.sort(key=lambda x: x[1].completed_at or "", reverse=True)

        # Remove old completed contexts
        removed_count = 0
        for audit_id, _ in completed[keep_recent:]:
            self.remove_context(audit_id)
            removed_count += 1

        return removed_count

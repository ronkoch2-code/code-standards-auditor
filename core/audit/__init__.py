"""
Core Audit Module

Provides code auditing capabilities including rule evaluation,
code analysis, and findings reporting.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from .context import (
    AuditContext,
    AuditContextManager,
    FileContext,
    AuditFinding,
    AuditSeverity,
    AuditCategory
)
from .rule_engine import (
    Rule,
    RuleChecker,
    RuleEngine,
    PatternRuleChecker,
    LengthRuleChecker,
    ComplexityRuleChecker
)
from .analyzer import (
    CodeAnalyzer,
    CodeMetrics,
    LanguageAnalyzer,
    PythonAnalyzer,
    JavaScriptAnalyzer
)
from .engine import AuditEngine, get_audit_engine

__all__ = [
    # Context
    "AuditContext",
    "AuditContextManager",
    "FileContext",
    "AuditFinding",
    "AuditSeverity",
    "AuditCategory",
    # Rule Engine
    "Rule",
    "RuleChecker",
    "RuleEngine",
    "PatternRuleChecker",
    "LengthRuleChecker",
    "ComplexityRuleChecker",
    # Analyzer
    "CodeAnalyzer",
    "CodeMetrics",
    "LanguageAnalyzer",
    "PythonAnalyzer",
    "JavaScriptAnalyzer",
    # Engine
    "AuditEngine",
    "get_audit_engine"
]

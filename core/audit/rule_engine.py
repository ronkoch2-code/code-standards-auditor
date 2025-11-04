"""
Rule Engine for Code Auditing

Provides rule evaluation, pattern matching, and standards checking
for code audits.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Callable, Pattern
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import re
import logging
from pathlib import Path

from .context import (
    AuditContext,
    AuditFinding,
    AuditSeverity,
    AuditCategory,
    FileContext
)

logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """
    Represents a single audit rule.

    Rules define what to check for in code and how to report violations.
    """

    id: str
    name: str
    description: str
    severity: AuditSeverity
    category: AuditCategory
    enabled: bool = True
    languages: List[str] = field(default_factory=lambda: ["all"])
    patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches_language(self, language: str) -> bool:
        """Check if this rule applies to the given language."""
        return "all" in self.languages or language in self.languages

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "enabled": self.enabled,
            "languages": self.languages,
            "patterns": self.patterns,
            "metadata": self.metadata
        }


class RuleChecker(ABC):
    """
    Abstract base class for rule checkers.

    Each rule checker implements specific logic for checking code against rules.
    """

    def __init__(self, rule: Rule):
        self.rule = rule

    @abstractmethod
    async def check(
        self,
        file_context: FileContext,
        audit_context: AuditContext
    ) -> List[AuditFinding]:
        """
        Check code against the rule.

        Args:
            file_context: Context of the file being checked
            audit_context: Overall audit context

        Returns:
            List of findings (empty if no violations)
        """
        pass

    def create_finding(
        self,
        message: str,
        file_path: Path,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        suggestion: Optional[str] = None,
        **kwargs
    ) -> AuditFinding:
        """Helper method to create a finding from this rule."""
        import uuid

        return AuditFinding(
            id=str(uuid.uuid4()),
            severity=self.rule.severity,
            category=self.rule.category,
            message=message,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            code_snippet=code_snippet,
            rule_id=self.rule.id,
            suggestion=suggestion,
            metadata=kwargs
        )


class PatternRuleChecker(RuleChecker):
    """
    Rule checker that uses regex patterns to find violations.
    """

    def __init__(self, rule: Rule):
        super().__init__(rule)
        self.compiled_patterns: List[Pattern] = []

        # Compile patterns
        for pattern in rule.patterns:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.MULTILINE))
            except re.error as e:
                logger.error(f"Invalid pattern in rule {rule.id}: {pattern} - {e}")

    async def check(
        self,
        file_context: FileContext,
        audit_context: AuditContext
    ) -> List[AuditFinding]:
        """Check code using regex patterns."""
        findings = []

        if not self.rule.matches_language(file_context.language):
            return findings

        lines = file_context.content.splitlines()

        for pattern in self.compiled_patterns:
            for line_num, line in enumerate(lines, start=1):
                matches = pattern.finditer(line)

                for match in matches:
                    finding = self.create_finding(
                        message=f"{self.rule.description} (matched pattern)",
                        file_path=file_context.path,
                        line_number=line_num,
                        column_number=match.start(),
                        code_snippet=line.strip(),
                        suggestion=self.rule.metadata.get("suggestion"),
                        matched_text=match.group(0)
                    )
                    findings.append(finding)

        return findings


class LengthRuleChecker(RuleChecker):
    """
    Rule checker for length-related violations (line length, function length, etc.).
    """

    async def check(
        self,
        file_context: FileContext,
        audit_context: AuditContext
    ) -> List[AuditFinding]:
        """Check for length violations."""
        findings = []

        if not self.rule.matches_language(file_context.language):
            return findings

        max_line_length = self.rule.metadata.get("max_line_length", 100)
        lines = file_context.content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            if len(line) > max_line_length:
                finding = self.create_finding(
                    message=f"Line exceeds maximum length ({len(line)} > {max_line_length})",
                    file_path=file_context.path,
                    line_number=line_num,
                    code_snippet=line[:80] + "..." if len(line) > 80 else line,
                    suggestion=f"Break line into multiple lines (max {max_line_length} chars)",
                    actual_length=len(line),
                    max_length=max_line_length
                )
                findings.append(finding)

        return findings


class ComplexityRuleChecker(RuleChecker):
    """
    Rule checker for complexity-related violations.
    """

    async def check(
        self,
        file_context: FileContext,
        audit_context: AuditContext
    ) -> List[AuditFinding]:
        """Check for complexity violations."""
        findings = []

        if not self.rule.matches_language(file_context.language):
            return findings

        # Simple cyclomatic complexity estimation
        # Count decision points: if, while, for, and, or, case, catch
        decision_keywords = ['if', 'while', 'for', 'and', 'or', 'case', 'catch', 'elif', 'else if']

        lines = file_context.content.splitlines()
        function_start = None
        function_complexity = 0
        max_complexity = self.rule.metadata.get("max_complexity", 10)

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Detect function start (simple heuristic)
            if any(keyword in stripped for keyword in ['def ', 'function ', 'func ']):
                if function_start is not None and function_complexity > max_complexity:
                    finding = self.create_finding(
                        message=f"Function complexity too high ({function_complexity} > {max_complexity})",
                        file_path=file_context.path,
                        line_number=function_start,
                        suggestion="Consider breaking function into smaller functions",
                        complexity=function_complexity,
                        max_complexity=max_complexity
                    )
                    findings.append(finding)

                function_start = line_num
                function_complexity = 1  # Base complexity

            # Count decision points
            for keyword in decision_keywords:
                if keyword in stripped:
                    function_complexity += stripped.count(keyword)

        # Check last function
        if function_start is not None and function_complexity > max_complexity:
            finding = self.create_finding(
                message=f"Function complexity too high ({function_complexity} > {max_complexity})",
                file_path=file_context.path,
                line_number=function_start,
                suggestion="Consider breaking function into smaller functions",
                complexity=function_complexity,
                max_complexity=max_complexity
            )
            findings.append(finding)

        return findings


class RuleEngine:
    """
    Main rule engine that manages and executes rules.
    """

    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self.checkers: Dict[str, RuleChecker] = {}

    def register_rule(self, rule: Rule, checker: Optional[RuleChecker] = None) -> None:
        """
        Register a rule with the engine.

        Args:
            rule: The rule to register
            checker: Optional custom checker (defaults to PatternRuleChecker)
        """
        self.rules[rule.id] = rule

        if checker:
            self.checkers[rule.id] = checker
        elif rule.patterns:
            self.checkers[rule.id] = PatternRuleChecker(rule)
        else:
            logger.warning(f"Rule {rule.id} has no patterns and no custom checker")

        logger.info(f"Registered rule: {rule.id} - {rule.name}")

    def unregister_rule(self, rule_id: str) -> bool:
        """Unregister a rule from the engine."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            if rule_id in self.checkers:
                del self.checkers[rule_id]
            logger.info(f"Unregistered rule: {rule_id}")
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)

    def get_all_rules(self) -> List[Rule]:
        """Get all registered rules."""
        return list(self.rules.values())

    def get_enabled_rules(self) -> List[Rule]:
        """Get all enabled rules."""
        return [rule for rule in self.rules.values() if rule.enabled]

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False

    async def check_file(
        self,
        file_context: FileContext,
        audit_context: AuditContext
    ) -> List[AuditFinding]:
        """
        Check a file against all applicable rules.

        Args:
            file_context: Context of the file to check
            audit_context: Overall audit context

        Returns:
            List of all findings from all rules
        """
        findings = []

        for rule_id, rule in self.rules.items():
            # Skip disabled rules
            if not rule.enabled:
                continue

            # Skip rules not applicable to this language
            if not rule.matches_language(file_context.language):
                continue

            # Skip rules explicitly disabled in audit context
            if not audit_context.is_rule_enabled(rule_id):
                continue

            # Get checker for this rule
            checker = self.checkers.get(rule_id)
            if not checker:
                logger.warning(f"No checker found for rule {rule_id}")
                continue

            # Run the checker
            try:
                rule_findings = await checker.check(file_context, audit_context)
                findings.extend(rule_findings)
                logger.debug(f"Rule {rule_id} found {len(rule_findings)} findings in {file_context.path}")
            except Exception as e:
                logger.error(f"Error checking rule {rule_id} on {file_context.path}: {e}")

        return findings

    def load_rules_from_standard(self, standard: Dict[str, Any]) -> int:
        """
        Load rules from a standard definition.

        Args:
            standard: Standard dictionary containing rules

        Returns:
            Number of rules loaded
        """
        rules_loaded = 0
        rules_data = standard.get("rules", [])

        for rule_data in rules_data:
            try:
                rule = Rule(
                    id=rule_data["id"],
                    name=rule_data["name"],
                    description=rule_data["description"],
                    severity=AuditSeverity(rule_data.get("severity", "medium")),
                    category=AuditCategory(rule_data.get("category", "best_practices")),
                    enabled=rule_data.get("enabled", True),
                    languages=rule_data.get("languages", ["all"]),
                    patterns=rule_data.get("patterns", []),
                    metadata=rule_data.get("metadata", {})
                )

                # Determine checker type
                checker_type = rule_data.get("checker_type", "pattern")
                if checker_type == "length":
                    checker = LengthRuleChecker(rule)
                elif checker_type == "complexity":
                    checker = ComplexityRuleChecker(rule)
                else:
                    checker = None  # Will default to PatternRuleChecker

                self.register_rule(rule, checker)
                rules_loaded += 1

            except (KeyError, ValueError) as e:
                logger.error(f"Error loading rule from standard: {e}")

        logger.info(f"Loaded {rules_loaded} rules from standard: {standard.get('title', 'Unknown')}")
        return rules_loaded

    def get_rules_summary(self) -> Dict[str, Any]:
        """Get summary of registered rules."""
        total_rules = len(self.rules)
        enabled_rules = len(self.get_enabled_rules())

        severity_counts = {}
        for severity in AuditSeverity:
            severity_counts[severity.value] = sum(
                1 for rule in self.rules.values()
                if rule.severity == severity
            )

        category_counts = {}
        for category in AuditCategory:
            category_counts[category.value] = sum(
                1 for rule in self.rules.values()
                if rule.category == category
            )

        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": total_rules - enabled_rules,
            "severity_distribution": severity_counts,
            "category_distribution": category_counts
        }

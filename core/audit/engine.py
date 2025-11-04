"""
Audit Engine

Main orchestration engine for code audits. Coordinates context management,
rule evaluation, code analysis, and reporting.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import logging
import asyncio
import uuid
from datetime import datetime

from .context import (
    AuditContext,
    AuditContextManager,
    FileContext,
    AuditFinding,
    AuditSeverity
)
from .rule_engine import RuleEngine
from .analyzer import CodeAnalyzer, CodeMetrics

logger = logging.getLogger(__name__)


class AuditEngine:
    """
    Main audit engine that orchestrates the entire audit process.

    The engine coordinates:
    - Context management
    - Rule evaluation
    - Code analysis
    - Finding aggregation
    - Reporting
    """

    def __init__(self):
        self.context_manager = AuditContextManager()
        self.rule_engine = RuleEngine()
        self.code_analyzer = CodeAnalyzer()
        self.progress_callbacks: List[Callable] = []

    def register_progress_callback(self, callback: Callable) -> None:
        """Register a callback for audit progress updates."""
        self.progress_callbacks.append(callback)

    async def _notify_progress(self, audit_id: str, progress: Dict[str, Any]) -> None:
        """Notify all progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(audit_id, progress)
                else:
                    callback(audit_id, progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    async def create_audit(
        self,
        files: List[Path],
        standards: Optional[List[Dict[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new audit.

        Args:
            files: List of file paths to audit
            standards: Optional list of standards to apply
            config: Optional configuration for the audit

        Returns:
            Audit ID
        """
        audit_id = str(uuid.uuid4())
        config = config or {}

        # Create audit context
        context = self.context_manager.create_context(
            audit_id=audit_id,
            config=config,
            severity_threshold=AuditSeverity(
                config.get("severity_threshold", "info")
            )
        )

        # Load standards and rules
        if standards:
            for standard in standards:
                context.add_standard(standard)
                self.rule_engine.load_rules_from_standard(standard)

        # Load files
        for file_path in files:
            try:
                file_context = await self._load_file(file_path)
                context.add_file(file_context)
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")

        logger.info(f"Created audit {audit_id} with {len(context.files)} files")
        return audit_id

    async def _load_file(self, file_path: Path) -> FileContext:
        """Load a file and create file context."""
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        # Detect language
        language = self._detect_language(file_path)

        # Read file
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                content = file_path.read_text(encoding='latin-1')
            except Exception as e:
                raise ValueError(f"Unable to read file {file_path}: {e}")

        return FileContext(
            path=file_path,
            content=content,
            language=language,
            size_bytes=0,  # Will be calculated in __post_init__
            line_count=0    # Will be calculated in __post_init__
        )

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.cs': 'csharp',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql'
        }

        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, 'unknown')

    async def run_audit(self, audit_id: str) -> AuditContext:
        """
        Run a complete audit.

        Args:
            audit_id: ID of the audit to run

        Returns:
            Completed audit context with findings
        """
        context = self.context_manager.get_context(audit_id)
        if not context:
            raise ValueError(f"Audit {audit_id} not found")

        logger.info(f"Starting audit {audit_id}")
        context.status = "running"

        try:
            total_files = len(context.files)

            for idx, file_context in enumerate(context.files, start=1):
                # Notify progress
                await self._notify_progress(audit_id, {
                    "phase": "analyzing",
                    "current_file": str(file_context.path),
                    "progress": idx / total_files,
                    "files_completed": idx - 1,
                    "files_total": total_files
                })

                # Analyze file
                await self._audit_file(file_context, context)

            # Mark as completed
            context.mark_completed()
            logger.info(f"Audit {audit_id} completed with {len(context.findings)} findings")

            # Final progress notification
            await self._notify_progress(audit_id, {
                "phase": "completed",
                "progress": 1.0,
                "findings": len(context.findings),
                "metrics": context.metrics
            })

        except Exception as e:
            logger.error(f"Error running audit {audit_id}: {e}")
            context.mark_completed(error=str(e))
            raise

        return context

    async def _audit_file(
        self,
        file_context: FileContext,
        audit_context: AuditContext
    ) -> None:
        """Audit a single file."""
        logger.debug(f"Auditing file: {file_context.path}")

        # Run code analysis
        try:
            metrics = await self.code_analyzer.analyze_file(file_context)
            file_context.metadata["metrics"] = metrics.to_dict()

            # Find code smells
            smell_findings = await self.code_analyzer.find_code_smells(
                file_context,
                audit_context
            )
            for finding in smell_findings:
                audit_context.add_finding(finding)

        except Exception as e:
            logger.error(f"Error analyzing file {file_context.path}: {e}")

        # Run rule checks
        try:
            rule_findings = await self.rule_engine.check_file(
                file_context,
                audit_context
            )
            for finding in rule_findings:
                audit_context.add_finding(finding)

        except Exception as e:
            logger.error(f"Error checking rules for {file_context.path}: {e}")

    async def run_quick_audit(
        self,
        files: List[Path],
        standards: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run a quick audit and return results immediately.

        Args:
            files: List of files to audit
            standards: Optional standards to apply

        Returns:
            Audit results dictionary
        """
        audit_id = await self.create_audit(files, standards)
        context = await self.run_audit(audit_id)
        return context.to_dict()

    def get_audit_status(self, audit_id: str) -> Dict[str, Any]:
        """Get the current status of an audit."""
        context = self.context_manager.get_context(audit_id)
        if not context:
            return {"error": "Audit not found"}

        return {
            "audit_id": audit_id,
            "status": context.status,
            "files_analyzed": len(context.files),
            "findings_count": len(context.findings),
            "started_at": context.started_at,
            "completed_at": context.completed_at,
            "error": context.error_message
        }

    def get_audit_results(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Get the full results of a completed audit."""
        context = self.context_manager.get_context(audit_id)
        if not context:
            return None

        return context.to_dict()

    def get_audit_summary(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of audit results."""
        context = self.context_manager.get_context(audit_id)
        if not context:
            return None

        return context.summary()

    async def cancel_audit(self, audit_id: str) -> bool:
        """Cancel a running audit."""
        context = self.context_manager.get_context(audit_id)
        if not context:
            return False

        if context.status == "running":
            context.mark_completed(error="Audit cancelled by user")
            return True

        return False

    def list_audits(self) -> List[Dict[str, Any]]:
        """List all audits."""
        audits = []
        for audit_id in self.context_manager.list_contexts():
            context = self.context_manager.get_context(audit_id)
            if context:
                audits.append(context.summary())
        return audits

    def cleanup_old_audits(self, keep_recent: int = 10) -> int:
        """Clean up old completed audits."""
        return self.context_manager.clear_completed_contexts(keep_recent)

    # Configuration methods

    def load_standard(self, standard: Dict[str, Any]) -> int:
        """
        Load a standard and its rules.

        Args:
            standard: Standard dictionary

        Returns:
            Number of rules loaded
        """
        return self.rule_engine.load_rules_from_standard(standard)

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a specific rule."""
        return self.rule_engine.enable_rule(rule_id)

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a specific rule."""
        return self.rule_engine.disable_rule(rule_id)

    def get_rules_summary(self) -> Dict[str, Any]:
        """Get summary of registered rules."""
        return self.rule_engine.get_rules_summary()

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.code_analyzer.get_supported_languages()

    # Reporting methods

    def generate_report(
        self,
        audit_id: str,
        format: str = "json"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an audit report.

        Args:
            audit_id: ID of the audit
            format: Report format (json, markdown, html)

        Returns:
            Report data
        """
        context = self.context_manager.get_context(audit_id)
        if not context:
            return None

        if format == "json":
            return self._generate_json_report(context)
        elif format == "markdown":
            return self._generate_markdown_report(context)
        else:
            raise ValueError(f"Unsupported report format: {format}")

    def _generate_json_report(self, context: AuditContext) -> Dict[str, Any]:
        """Generate JSON report."""
        return context.to_dict()

    def _generate_markdown_report(self, context: AuditContext) -> Dict[str, Any]:
        """Generate markdown report."""
        findings_by_severity = {}
        for severity in AuditSeverity:
            findings = context.get_findings_by_severity(severity)
            if findings:
                findings_by_severity[severity.value] = findings

        report = f"""# Code Audit Report

**Audit ID**: {context.audit_id}
**Status**: {context.status}
**Started**: {context.started_at}
**Completed**: {context.completed_at}

## Summary

- **Total Files**: {len(context.files)}
- **Total Findings**: {len(context.findings)}
- **Critical**: {context.metrics.get('severity_counts', {}).get('critical', 0)}
- **High**: {context.metrics.get('severity_counts', {}).get('high', 0)}
- **Medium**: {context.metrics.get('severity_counts', {}).get('medium', 0)}
- **Low**: {context.metrics.get('severity_counts', {}).get('low', 0)}

## Findings by Severity

"""

        for severity, findings in findings_by_severity.items():
            report += f"\n### {severity.upper()} ({len(findings)} findings)\n\n"
            for finding in findings[:10]:  # Limit to 10 per severity
                report += f"- **{finding.message}**\n"
                report += f"  - File: {finding.file_path}\n"
                if finding.line_number:
                    report += f"  - Line: {finding.line_number}\n"
                if finding.suggestion:
                    report += f"  - Suggestion: {finding.suggestion}\n"
                report += "\n"

        report += f"\n---\n*Generated by Code Standards Auditor*\n"

        return {
            "format": "markdown",
            "content": report
        }


# Singleton instance
_engine_instance: Optional[AuditEngine] = None


def get_audit_engine() -> AuditEngine:
    """Get the singleton audit engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AuditEngine()
    return _engine_instance

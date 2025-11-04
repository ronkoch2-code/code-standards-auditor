"""
Code Analyzer

Provides static code analysis capabilities including AST parsing,
metrics calculation, and code structure analysis.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import ast
import logging
import re

from .context import FileContext, AuditContext, AuditFinding, AuditSeverity, AuditCategory

logger = logging.getLogger(__name__)


@dataclass
class CodeMetrics:
    """Metrics for a code file."""

    # Basic metrics
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0

    # Complexity metrics
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0

    # Structure metrics
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0

    # Quality indicators
    docstring_coverage: float = 0.0
    test_coverage: float = 0.0

    # Additional metrics
    avg_function_length: float = 0.0
    max_function_length: int = 0
    avg_line_length: float = 0.0
    max_line_length: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "import_count": self.import_count,
            "docstring_coverage": self.docstring_coverage,
            "avg_function_length": self.avg_function_length,
            "max_function_length": self.max_function_length,
            "avg_line_length": self.avg_line_length,
            "max_line_length": self.max_line_length
        }


class LanguageAnalyzer:
    """Base class for language-specific analyzers."""

    def __init__(self, language: str):
        self.language = language

    async def analyze(self, file_context: FileContext) -> CodeMetrics:
        """Analyze code and return metrics."""
        metrics = CodeMetrics()

        # Basic line counting
        lines = file_context.content.splitlines()
        metrics.total_lines = len(lines)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith('#') or stripped.startswith('//'):
                metrics.comment_lines += 1
            else:
                metrics.code_lines += 1

        # Calculate line length stats
        if lines:
            line_lengths = [len(line) for line in lines]
            metrics.avg_line_length = sum(line_lengths) / len(line_lengths)
            metrics.max_line_length = max(line_lengths)

        return metrics


class PythonAnalyzer(LanguageAnalyzer):
    """Analyzer for Python code."""

    def __init__(self):
        super().__init__("python")

    async def analyze(self, file_context: FileContext) -> CodeMetrics:
        """Analyze Python code using AST."""
        metrics = await super().analyze(file_context)

        try:
            tree = ast.parse(file_context.content)

            # Count functions and classes
            function_lengths = []
            functions_with_docstrings = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics.function_count += 1

                    # Check for docstring
                    if ast.get_docstring(node):
                        functions_with_docstrings += 1

                    # Calculate function length
                    if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                        func_length = node.end_lineno - node.lineno
                        function_lengths.append(func_length)

                elif isinstance(node, ast.ClassDef):
                    metrics.class_count += 1

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics.import_count += 1

            # Calculate function length stats
            if function_lengths:
                metrics.avg_function_length = sum(function_lengths) / len(function_lengths)
                metrics.max_function_length = max(function_lengths)

            # Calculate docstring coverage
            if metrics.function_count > 0:
                metrics.docstring_coverage = functions_with_docstrings / metrics.function_count

            # Calculate cyclomatic complexity (simplified)
            metrics.cyclomatic_complexity = self._calculate_complexity(tree)

        except SyntaxError as e:
            logger.warning(f"Syntax error parsing {file_context.path}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_context.path}: {e}")

        return metrics

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity

        decision_nodes = (
            ast.If, ast.While, ast.For, ast.ExceptHandler,
            ast.With, ast.Assert, ast.comprehension
        )

        for node in ast.walk(tree):
            if isinstance(node, decision_nodes):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity


class JavaScriptAnalyzer(LanguageAnalyzer):
    """Analyzer for JavaScript/TypeScript code."""

    def __init__(self, language: str = "javascript"):
        super().__init__(language)

    async def analyze(self, file_context: FileContext) -> CodeMetrics:
        """Analyze JavaScript code using regex patterns."""
        metrics = await super().analyze(file_context)

        content = file_context.content

        # Count functions (simple regex approach)
        function_patterns = [
            r'function\s+\w+',  # function declarations
            r'const\s+\w+\s*=\s*function',  # function expressions
            r'const\s+\w+\s*=\s*\([^)]*\)\s*=>',  # arrow functions
            r'async\s+function\s+\w+',  # async functions
        ]

        for pattern in function_patterns:
            matches = re.findall(pattern, content)
            metrics.function_count += len(matches)

        # Count classes
        class_pattern = r'class\s+\w+'
        metrics.class_count = len(re.findall(class_pattern, content))

        # Count imports
        import_patterns = [
            r'import\s+',
            r'require\s*\(',
        ]
        for pattern in import_patterns:
            metrics.import_count += len(re.findall(pattern, content))

        # Simple complexity estimation based on keywords
        complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch', '&&', '||']
        for keyword in complexity_keywords:
            metrics.cyclomatic_complexity += content.count(keyword)

        return metrics


class CodeAnalyzer:
    """
    Main code analyzer that coordinates language-specific analysis.
    """

    def __init__(self):
        self.language_analyzers: Dict[str, LanguageAnalyzer] = {
            "python": PythonAnalyzer(),
            "javascript": JavaScriptAnalyzer("javascript"),
            "typescript": JavaScriptAnalyzer("typescript"),
        }

    def register_analyzer(self, language: str, analyzer: LanguageAnalyzer) -> None:
        """Register a language-specific analyzer."""
        self.language_analyzers[language] = analyzer
        logger.info(f"Registered analyzer for {language}")

    async def analyze_file(self, file_context: FileContext) -> CodeMetrics:
        """
        Analyze a file and return metrics.

        Args:
            file_context: Context of the file to analyze

        Returns:
            Code metrics for the file
        """
        analyzer = self.language_analyzers.get(
            file_context.language,
            LanguageAnalyzer(file_context.language)
        )

        metrics = await analyzer.analyze(file_context)
        logger.debug(f"Analyzed {file_context.path}: {metrics.code_lines} lines of code")

        return metrics

    async def analyze_structure(self, file_context: FileContext) -> Dict[str, Any]:
        """
        Analyze code structure (functions, classes, imports, etc.).

        Args:
            file_context: Context of the file to analyze

        Returns:
            Dictionary containing structure information
        """
        structure = {
            "functions": [],
            "classes": [],
            "imports": [],
            "exports": [],
            "dependencies": set()
        }

        if file_context.language == "python":
            structure = await self._analyze_python_structure(file_context)
        elif file_context.language in ["javascript", "typescript"]:
            structure = await self._analyze_javascript_structure(file_context)

        return structure

    async def _analyze_python_structure(self, file_context: FileContext) -> Dict[str, Any]:
        """Analyze Python code structure."""
        structure = {
            "functions": [],
            "classes": [],
            "imports": [],
            "exports": [],
            "dependencies": set()
        }

        try:
            tree = ast.parse(file_context.content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    structure["functions"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "has_docstring": ast.get_docstring(node) is not None
                    })

                elif isinstance(node, ast.ClassDef):
                    structure["classes"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [
                            m.name for m in node.body
                            if isinstance(m, ast.FunctionDef)
                        ]
                    })

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append({
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                        structure["dependencies"].add(alias.name.split('.')[0])

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        structure["imports"].append({
                            "module": f"{module}.{alias.name}",
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                    if module:
                        structure["dependencies"].add(module.split('.')[0])

        except (SyntaxError, Exception) as e:
            logger.error(f"Error analyzing Python structure: {e}")

        structure["dependencies"] = list(structure["dependencies"])
        return structure

    async def _analyze_javascript_structure(self, file_context: FileContext) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code structure (simplified)."""
        structure = {
            "functions": [],
            "classes": [],
            "imports": [],
            "exports": [],
            "dependencies": set()
        }

        lines = file_context.content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Find function declarations
            func_match = re.search(r'function\s+(\w+)', stripped)
            if func_match:
                structure["functions"].append({
                    "name": func_match.group(1),
                    "line": line_num
                })

            # Find class declarations
            class_match = re.search(r'class\s+(\w+)', stripped)
            if class_match:
                structure["classes"].append({
                    "name": class_match.group(1),
                    "line": line_num
                })

            # Find imports
            import_match = re.search(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', stripped)
            if import_match:
                module = import_match.group(1)
                structure["imports"].append({
                    "module": module,
                    "line": line_num
                })
                # Add to dependencies if it's not a relative import
                if not module.startswith('.'):
                    structure["dependencies"].add(module.split('/')[0])

            # Find exports
            if 'export' in stripped:
                export_match = re.search(r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)', stripped)
                if export_match:
                    structure["exports"].append({
                        "name": export_match.group(1),
                        "line": line_num
                    })

        structure["dependencies"] = list(structure["dependencies"])
        return structure

    async def find_code_smells(
        self,
        file_context: FileContext,
        audit_context: AuditContext
    ) -> List[AuditFinding]:
        """
        Find common code smells in the file.

        Args:
            file_context: Context of the file to analyze
            audit_context: Overall audit context

        Returns:
            List of findings for detected code smells
        """
        findings = []
        metrics = await self.analyze_file(file_context)

        # Check for long functions
        if metrics.max_function_length > 50:
            findings.append(AuditFinding(
                id=f"smell_{file_context.path}_long_function",
                severity=AuditSeverity.MEDIUM,
                category=AuditCategory.MAINTAINABILITY,
                message=f"Function exceeds recommended length ({metrics.max_function_length} lines)",
                file_path=file_context.path,
                suggestion="Consider breaking down into smaller functions",
                metadata={"max_function_length": metrics.max_function_length}
            ))

        # Check for high complexity
        if metrics.cyclomatic_complexity > 20:
            findings.append(AuditFinding(
                id=f"smell_{file_context.path}_high_complexity",
                severity=AuditSeverity.HIGH,
                category=AuditCategory.MAINTAINABILITY,
                message=f"High cyclomatic complexity ({metrics.cyclomatic_complexity})",
                file_path=file_context.path,
                suggestion="Refactor to reduce complexity and improve testability",
                metadata={"complexity": metrics.cyclomatic_complexity}
            ))

        # Check for low docstring coverage (Python)
        if file_context.language == "python" and metrics.docstring_coverage < 0.5:
            if metrics.function_count > 0:
                findings.append(AuditFinding(
                    id=f"smell_{file_context.path}_low_docstrings",
                    severity=AuditSeverity.LOW,
                    category=AuditCategory.DOCUMENTATION,
                    message=f"Low docstring coverage ({metrics.docstring_coverage:.1%})",
                    file_path=file_context.path,
                    suggestion="Add docstrings to functions and classes",
                    metadata={"docstring_coverage": metrics.docstring_coverage}
                ))

        # Check for very long lines
        if metrics.max_line_length > 120:
            findings.append(AuditFinding(
                id=f"smell_{file_context.path}_long_lines",
                severity=AuditSeverity.LOW,
                category=AuditCategory.STYLE,
                message=f"Lines exceed recommended length ({metrics.max_line_length} chars)",
                file_path=file_context.path,
                suggestion="Break long lines for better readability",
                metadata={"max_line_length": metrics.max_line_length}
            ))

        return findings

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.language_analyzers.keys())

"""
Prompt Manager

Manages prompt templates, variables, and prompt generation for LLM interactions.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """A prompt template with variables."""
    id: str
    name: str
    template: str
    variables: List[str]
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

        # Extract variables from template if not provided
        if not self.variables:
            self.variables = self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """Extract variable names from template."""
        # Find all {variable_name} patterns
        pattern = r'\{(\w+)\}'
        matches = re.findall(pattern, self.template)
        return list(set(matches))

    def render(self, **kwargs) -> str:
        """
        Render the template with provided variables.

        Args:
            **kwargs: Variable values

        Returns:
            Rendered prompt

        Raises:
            ValueError: If required variables are missing
        """
        # Check for missing variables
        missing = [var for var in self.variables if var not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

        # Render template
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Error rendering template: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "template": self.template,
            "variables": self.variables,
            "system_prompt": self.system_prompt,
            "metadata": self.metadata
        }


class PromptManager:
    """
    Manages prompt templates and generation.
    """

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default prompt templates."""

        # Code analysis prompt
        self.register_template(PromptTemplate(
            id="code_analysis",
            name="Code Analysis",
            template="""Analyze the following {language} code and provide insights on:
- Code quality
- Potential issues
- Best practices violations
- Suggested improvements

Code:
```{language}
{code}
```

Please provide a detailed analysis.""",
            variables=["language", "code"],
            system_prompt="You are an expert code reviewer with deep knowledge of software engineering best practices."
        ))

        # Standards research prompt
        self.register_template(PromptTemplate(
            id="standards_research",
            name="Standards Research",
            template="""Research and create a comprehensive coding standard for:

Topic: {topic}
Language: {language}
Focus Areas: {focus_areas}

The standard should include:
1. Overview and rationale
2. Key principles
3. Code examples (both good and bad)
4. Common pitfalls to avoid
5. Testing requirements
6. References

Please create a detailed, professional coding standard.""",
            variables=["topic", "language", "focus_areas"],
            system_prompt="You are a software architecture expert creating professional coding standards."
        ))

        # Code generation prompt
        self.register_template(PromptTemplate(
            id="code_generation",
            name="Code Generation",
            template="""Generate {language} code that implements the following:

Requirements:
{requirements}

Constraints:
{constraints}

The code should:
- Follow best practices
- Be well-documented
- Include error handling
- Be production-ready

Please provide the implementation.""",
            variables=["language", "requirements", "constraints"],
            system_prompt="You are an expert software engineer writing production-quality code."
        ))

        # Bug fix prompt
        self.register_template(PromptTemplate(
            id="bug_fix",
            name="Bug Fix",
            template="""Analyze and fix the following bug:

Description: {bug_description}

Code:
```{language}
{code}
```

Error/Symptoms:
{error}

Please:
1. Identify the root cause
2. Provide a fix
3. Explain why it was happening
4. Suggest how to prevent similar issues""",
            variables=["bug_description", "language", "code", "error"],
            system_prompt="You are an expert debugger skilled at finding and fixing software bugs."
        ))

        # Code review prompt
        self.register_template(PromptTemplate(
            id="code_review",
            name="Code Review",
            template="""Review the following {language} code changes:

Context: {context}

Changes:
```{language}
{changes}
```

Please review for:
- Correctness
- Performance
- Security
- Maintainability
- Style consistency

Provide specific, actionable feedback.""",
            variables=["language", "context", "changes"],
            system_prompt="You are a senior engineer conducting a thorough code review."
        ))

        # Refactoring prompt
        self.register_template(PromptTemplate(
            id="refactoring",
            name="Code Refactoring",
            template="""Refactor the following {language} code to improve:

Focus: {focus}

Current Code:
```{language}
{code}
```

Issues to address:
{issues}

Please provide:
1. Refactored code
2. Explanation of changes
3. Benefits of the refactoring""",
            variables=["language", "focus", "code", "issues"],
            system_prompt="You are a refactoring expert skilled at improving code quality."
        ))

        # Documentation prompt
        self.register_template(PromptTemplate(
            id="documentation",
            name="Documentation Generation",
            template="""Generate comprehensive documentation for:

Code:
```{language}
{code}
```

Documentation Type: {doc_type}

Please include:
- Purpose and overview
- Parameters and return values
- Usage examples
- Edge cases and limitations
- Related functions/classes""",
            variables=["language", "code", "doc_type"],
            system_prompt="You are a technical writer creating clear, comprehensive documentation."
        ))

        # Test generation prompt
        self.register_template(PromptTemplate(
            id="test_generation",
            name="Test Generation",
            template="""Generate comprehensive tests for:

Code:
```{language}
{code}
```

Test Framework: {test_framework}
Coverage Requirements: {coverage}

Please generate tests that cover:
- Normal cases
- Edge cases
- Error conditions
- Integration scenarios""",
            variables=["language", "code", "test_framework", "coverage"],
            system_prompt="You are a testing expert writing thorough, maintainable tests."
        ))

    def register_template(self, template: PromptTemplate) -> None:
        """Register a prompt template."""
        self.templates[template.id] = template
        logger.debug(f"Registered prompt template: {template.id}")

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        return [
            {
                "id": template.id,
                "name": template.name,
                "variables": template.variables,
                "metadata": template.metadata
            }
            for template in self.templates.values()
        ]

    def render_prompt(
        self,
        template_id: str,
        **kwargs
    ) -> tuple[str, Optional[str]]:
        """
        Render a prompt from a template.

        Args:
            template_id: ID of the template
            **kwargs: Template variables

        Returns:
            Tuple of (rendered_prompt, system_prompt)

        Raises:
            ValueError: If template not found or variables missing
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        prompt = template.render(**kwargs)
        return prompt, template.system_prompt

    def create_custom_prompt(
        self,
        template: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> tuple[str, Optional[str]]:
        """
        Create a custom prompt on the fly.

        Args:
            template: Template string with {variables}
            system_prompt: Optional system prompt
            **kwargs: Template variables

        Returns:
            Tuple of (rendered_prompt, system_prompt)
        """
        temp_template = PromptTemplate(
            id="temp",
            name="Temporary",
            template=template,
            variables=[],
            system_prompt=system_prompt
        )

        rendered = temp_template.render(**kwargs)
        return rendered, system_prompt

    def load_templates_from_file(self, file_path: Path) -> int:
        """
        Load templates from a JSON file.

        Args:
            file_path: Path to JSON file containing templates

        Returns:
            Number of templates loaded
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            templates_data = data.get("templates", [])
            loaded_count = 0

            for template_data in templates_data:
                template = PromptTemplate(
                    id=template_data["id"],
                    name=template_data["name"],
                    template=template_data["template"],
                    variables=template_data.get("variables", []),
                    system_prompt=template_data.get("system_prompt"),
                    metadata=template_data.get("metadata", {})
                )
                self.register_template(template)
                loaded_count += 1

            logger.info(f"Loaded {loaded_count} templates from {file_path}")
            return loaded_count

        except Exception as e:
            logger.error(f"Error loading templates from {file_path}: {e}")
            return 0

    def save_templates_to_file(self, file_path: Path) -> bool:
        """
        Save templates to a JSON file.

        Args:
            file_path: Path to save templates

        Returns:
            True if successful
        """
        try:
            data = {
                "templates": [
                    template.to_dict()
                    for template in self.templates.values()
                ]
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.templates)} templates to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving templates to {file_path}: {e}")
            return False

    def validate_template_variables(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate that all required variables are provided.

        Args:
            template_id: ID of the template
            variables: Variables to validate

        Returns:
            Tuple of (is_valid, missing_variables)
        """
        template = self.get_template(template_id)
        if not template:
            return False, ["Template not found"]

        missing = [
            var for var in template.variables
            if var not in variables
        ]

        return len(missing) == 0, missing


# Singleton instance
_prompt_manager_instance: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get the singleton prompt manager."""
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance

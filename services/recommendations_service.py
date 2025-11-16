"""
Code Recommendations Service

This service analyzes code against standards and generates improvement recommendations.

Author: Code Standards Auditor
Date: January 31, 2025
Version: 1.0.0
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import hashlib

from services.gemini_service import GeminiService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from services.standards_research_service import StandardsResearchService
from config.settings import settings

logger = logging.getLogger(__name__)


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"  # Security vulnerabilities, bugs
    HIGH = "high"         # Performance issues, bad practices
    MEDIUM = "medium"     # Code quality, maintainability
    LOW = "low"          # Style, minor improvements
    INFO = "info"        # Suggestions, alternatives


class RecommendationType(Enum):
    """Types of recommendations."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"


class RecommendationsService:
    """Service for generating code improvement recommendations."""
    
    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        neo4j_service: Optional[Neo4jService] = None,
        cache_service: Optional[CacheService] = None,
        research_service: Optional[StandardsResearchService] = None
    ):
        """Initialize the Recommendations Service."""
        self.gemini = gemini_service or GeminiService()
        self.neo4j = neo4j_service or Neo4jService()
        self.cache = cache_service or CacheService()
        self.research = research_service or StandardsResearchService()
    
    async def generate_recommendations(
        self,
        code: str,
        language: str,
        standards: Optional[List[Dict[str, Any]]] = None,
        focus_areas: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate recommendations for code improvement.
        
        Args:
            code: The code to analyze
            language: Programming language
            standards: Specific standards to check against
            focus_areas: Areas to focus on (security, performance, etc.)
            context: Additional context (project type, constraints, etc.)
            
        Returns:
            Dictionary containing recommendations
        """
        try:
            # Get applicable standards if not provided
            if not standards:
                standards = await self._get_applicable_standards(language, context)
            
            # Analyze code against standards
            analysis = await self._analyze_code(code, language, standards, focus_areas)
            
            # Generate recommendations
            recommendations = await self._generate_detailed_recommendations(
                code, analysis, language, context
            )
            
            # Prioritize and rank recommendations
            prioritized = self._prioritize_recommendations(recommendations)
            
            # Generate implementation examples
            with_examples = await self._add_implementation_examples(
                prioritized, code, language
            )
            
            # Store in Neo4j if enabled
            if settings.USE_NEO4J:
                await self._store_recommendations(with_examples)
            
            # Cache results
            cache_key = self._generate_cache_key(code, language, focus_areas)
            await self.cache.cache_audit_result(cache_key, with_examples)
            
            return with_examples
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise
    
    async def _get_applicable_standards(
        self,
        language: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get applicable standards for the given language and context."""
        standards = []
        
        # Get language-specific standards
        if settings.USE_NEO4J:
            graph_standards = await self.neo4j.get_standards_by_category(language)
            standards.extend(graph_standards)
        
        # Get general standards
        general_standards = await self.neo4j.get_standards_by_category("general")
        standards.extend(general_standards)
        
        # Filter by context if provided
        if context:
            standards = self._filter_standards_by_context(standards, context)
        
        return standards
    
    def _filter_standards_by_context(
        self,
        standards: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter standards based on context."""
        filtered = []
        
        for standard in standards:
            # Check if standard applies to context
            if self._standard_applies_to_context(standard, context):
                filtered.append(standard)
        
        return filtered
    
    def _standard_applies_to_context(
        self,
        standard: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if a standard applies to the given context."""
        # Check project type
        if "project_type" in context:
            if standard.get("applicable_to") and \
               context["project_type"] not in standard.get("applicable_to", []):
                return False
        
        # Check other context filters
        # This would be expanded based on actual standard structure
        
        return True
    
    async def _analyze_code(
        self,
        code: str,
        language: str,
        standards: List[Dict[str, Any]],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze code against standards."""
        prompt = f"""
        Analyze the following {language} code against coding standards.
        
        Focus Areas: {focus_areas or 'All aspects'}
        
        Code:
        ```{language}
        {code}
        ```
        
        Standards to check:
        {json.dumps(standards, indent=2)}
        
        Identify:
        1. Violations of standards
        2. Areas for improvement
        3. Security concerns
        4. Performance issues
        5. Maintainability problems
        6. Missing best practices
        7. Testing gaps
        8. Documentation needs
        
        For each issue found, provide:
        - Issue description
        - Line number(s) affected
        - Standard violated
        - Severity (critical/high/medium/low)
        - Category (security/performance/quality/etc.)
        """
        
        response = await self.gemini.generate_with_caching(
            prompt=prompt,
            context="Code analysis"
        )
        
        return self._parse_analysis_response(response)
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse analysis response from LLM."""
        # This would include sophisticated parsing
        # For now, return structured data
        return {
            "issues": [
                {
                    "id": "issue_001",
                    "description": "Potential SQL injection vulnerability",
                    "line_numbers": [42, 43],
                    "standard_violated": "OWASP Security Standards",
                    "severity": "critical",
                    "category": "security"
                }
                # More issues would be parsed
            ],
            "summary": {
                "total_issues": 1,
                "critical": 1,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "analysis_date": datetime.now().isoformat()
        }
    
    async def _generate_detailed_recommendations(
        self,
        code: str,
        analysis: Dict[str, Any],
        language: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate detailed recommendations based on analysis."""
        recommendations = []
        
        for issue in analysis["issues"]:
            prompt = f"""
            Generate a detailed recommendation for fixing this issue:
            
            Issue: {issue['description']}
            Lines affected: {issue['line_numbers']}
            Severity: {issue['severity']}
            Category: {issue['category']}
            
            Original code snippet:
            ```{language}
            {self._extract_code_snippet(code, issue['line_numbers'])}
            ```
            
            Provide:
            1. Detailed explanation of the problem
            2. Step-by-step fix instructions
            3. Corrected code example
            4. Alternative approaches
            5. Prevention strategies
            6. Testing recommendations
            7. Links to relevant documentation
            """
            
            response = await self.gemini.generate_with_caching(
                prompt=prompt,
                context=f"Recommendation for {issue['id']}"
            )
            
            recommendation = self._parse_recommendation_response(response, issue)
            recommendations.append(recommendation)
        
        return recommendations
    
    def _extract_code_snippet(
        self,
        code: str,
        line_numbers: List[int],
        context_lines: int = 3
    ) -> str:
        """Extract code snippet around specified line numbers."""
        lines = code.split('\n')
        
        if not line_numbers:
            return code[:500]  # Return first 500 chars if no line numbers
        
        min_line = max(0, min(line_numbers) - context_lines - 1)
        max_line = min(len(lines), max(line_numbers) + context_lines)
        
        return '\n'.join(lines[min_line:max_line])
    
    def _parse_recommendation_response(
        self,
        response: str,
        issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse recommendation response from LLM."""
        return {
            "id": f"rec_{issue['id']}",
            "issue_id": issue['id'],
            "title": f"Fix: {issue['description']}",
            "description": response,  # Would be parsed more specifically
            "priority": self._map_severity_to_priority(issue['severity']),
            "type": self._map_category_to_type(issue['category']),
            "estimated_effort": self._estimate_effort(issue),
            "automated_fix_available": False,  # Would check if we can auto-fix
            "created_at": datetime.now().isoformat()
        }
    
    def _map_severity_to_priority(self, severity: str) -> str:
        """Map issue severity to recommendation priority."""
        mapping = {
            "critical": RecommendationPriority.CRITICAL.value,
            "high": RecommendationPriority.HIGH.value,
            "medium": RecommendationPriority.MEDIUM.value,
            "low": RecommendationPriority.LOW.value,
            "info": RecommendationPriority.INFO.value
        }
        return mapping.get(severity, RecommendationPriority.MEDIUM.value)
    
    def _map_category_to_type(self, category: str) -> str:
        """Map issue category to recommendation type."""
        mapping = {
            "security": RecommendationType.SECURITY.value,
            "performance": RecommendationType.PERFORMANCE.value,
            "quality": RecommendationType.MAINTAINABILITY.value,
            "style": RecommendationType.READABILITY.value,
            "testing": RecommendationType.TESTING.value,
            "documentation": RecommendationType.DOCUMENTATION.value
        }
        return mapping.get(category, RecommendationType.REFACTORING.value)
    
    def _estimate_effort(self, issue: Dict[str, Any]) -> str:
        """Estimate effort required to fix the issue."""
        # Simple estimation based on severity and category
        if issue['severity'] == 'critical':
            return "high"
        elif issue['severity'] == 'high':
            return "medium"
        else:
            return "low"
    
    def _prioritize_recommendations(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prioritize and rank recommendations."""
        # Define priority order
        priority_order = {
            RecommendationPriority.CRITICAL.value: 0,
            RecommendationPriority.HIGH.value: 1,
            RecommendationPriority.MEDIUM.value: 2,
            RecommendationPriority.LOW.value: 3,
            RecommendationPriority.INFO.value: 4
        }
        
        # Sort by priority
        sorted_recs = sorted(
            recommendations,
            key=lambda x: (
                priority_order.get(x['priority'], 5),
                x.get('estimated_effort', 'medium')
            )
        )
        
        # Add ranking
        for i, rec in enumerate(sorted_recs, 1):
            rec['rank'] = i
        
        return sorted_recs
    
    async def _add_implementation_examples(
        self,
        recommendations: List[Dict[str, Any]],
        original_code: str,
        language: str
    ) -> Dict[str, Any]:
        """Add implementation examples to recommendations."""
        enhanced_recommendations = []
        
        for rec in recommendations[:5]:  # Limit to top 5 for performance
            if rec['priority'] in [
                RecommendationPriority.CRITICAL.value,
                RecommendationPriority.HIGH.value
            ]:
                # Generate implementation example
                example = await self._generate_implementation_example(
                    rec, original_code, language
                )
                rec['implementation_example'] = example
            
            enhanced_recommendations.append(rec)
        
        # Add remaining recommendations without examples
        enhanced_recommendations.extend(recommendations[5:])
        
        return {
            "recommendations": enhanced_recommendations,
            "summary": self._generate_summary(enhanced_recommendations),
            "metadata": {
                "total_recommendations": len(enhanced_recommendations),
                "language": language,
                "generated_at": datetime.now().isoformat(),
                "model": "gemini"
            }
        }
    
    async def _generate_implementation_example(
        self,
        recommendation: Dict[str, Any],
        original_code: str,
        language: str
    ) -> Dict[str, Any]:
        """Generate implementation example for a recommendation."""
        prompt = f"""
        Generate a complete implementation example for this recommendation:
        
        Recommendation: {recommendation['title']}
        Description: {recommendation['description'][:500]}
        
        Provide:
        1. Before code (problematic)
        2. After code (fixed)
        3. Step-by-step transformation
        4. Test cases to verify the fix
        
        Language: {language}
        Keep examples concise but complete.
        """
        
        response = await self.gemini.generate_with_caching(
            prompt=prompt,
            context="Implementation example"
        )
        
        return {
            "before": "// Original problematic code",
            "after": "// Fixed code following standards",
            "steps": ["Step 1", "Step 2"],  # Would be parsed from response
            "tests": "// Test cases",
            "explanation": response
        }
    
    def _generate_summary(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of recommendations."""
        priority_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        type_counts = {}
        
        for rec in recommendations:
            priority_counts[rec['priority']] = priority_counts.get(rec['priority'], 0) + 1
            rec_type = rec.get('type', 'other')
            type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
        
        return {
            "by_priority": priority_counts,
            "by_type": type_counts,
            "total": len(recommendations),
            "requires_immediate_action": priority_counts['critical'] > 0,
            "estimated_total_effort": self._calculate_total_effort(recommendations)
        }
    
    def _calculate_total_effort(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """Calculate total effort for all recommendations."""
        effort_scores = {"low": 1, "medium": 2, "high": 3}
        total_score = sum(
            effort_scores.get(rec.get('estimated_effort', 'medium'), 2)
            for rec in recommendations
        )
        
        if total_score < 5:
            return "low"
        elif total_score < 15:
            return "medium"
        else:
            return "high"
    
    async def _store_recommendations(self, recommendations_data: Dict[str, Any]) -> None:
        """Store recommendations in Neo4j."""
        try:
            # Store each recommendation as a node with relationships
            for rec in recommendations_data['recommendations']:
                await self.neo4j.track_violation(
                    file_path="analysis",
                    line_number=0,
                    violation_type=rec['type'],
                    severity=rec['priority'],
                    message=rec['title'],
                    standard_id=rec.get('issue_id', 'unknown'),
                    suggested_fix=rec.get('implementation_example', {}).get('after', '')
                )
        except Exception as e:
            logger.error(f"Error storing recommendations: {e}")
    
    def _generate_cache_key(
        self,
        code: str,
        language: str,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Generate cache key for recommendations."""
        key_data = f"{hashlib.md5(code.encode(), usedforsecurity=False).hexdigest()}:{language}"
        if focus_areas:
            key_data += f":{':'.join(sorted(focus_areas))}"
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()
    
    async def get_quick_fixes(
        self,
        code: str,
        language: str,
        issue_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get quick fixes for common issues.
        
        Args:
            code: The code with issues
            language: Programming language
            issue_type: Type of issue to fix
            
        Returns:
            List of quick fixes that can be applied
        """
        prompt = f"""
        Provide quick fixes for {issue_type} issues in this {language} code:
        
        ```{language}
        {code}
        ```
        
        For each fix provide:
        1. Issue location (line numbers)
        2. One-line description
        3. Fixed code snippet
        4. Can be automated (yes/no)
        
        Focus on fixes that can be applied immediately without major refactoring.
        """
        
        response = await self.gemini.generate_with_caching(
            prompt=prompt,
            context="Quick fixes"
        )
        
        return self._parse_quick_fixes(response)
    
    def _parse_quick_fixes(self, response: str) -> List[Dict[str, Any]]:
        """Parse quick fixes from LLM response."""
        # Would implement actual parsing
        return [
            {
                "id": "qf_001",
                "description": "Add input validation",
                "location": {"start": 10, "end": 15},
                "fix": "// Fixed code here",
                "automated": True
            }
        ]
    
    async def generate_refactoring_plan(
        self,
        code: str,
        language: str,
        goals: List[str]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive refactoring plan.
        
        Args:
            code: The code to refactor
            language: Programming language
            goals: Refactoring goals (e.g., improve testability, reduce complexity)
            
        Returns:
            Detailed refactoring plan
        """
        prompt = f"""
        Create a comprehensive refactoring plan for this {language} code.
        
        Refactoring Goals:
        {json.dumps(goals, indent=2)}
        
        Code:
        ```{language}
        {code}
        ```
        
        Provide:
        1. Current state analysis
        2. Target architecture
        3. Step-by-step refactoring phases
        4. Risk assessment for each phase
        5. Testing strategy
        6. Rollback plan
        7. Success metrics
        8. Estimated timeline
        """
        
        response = await self.gemini.generate_with_caching(
            prompt=prompt,
            context="Refactoring plan"
        )
        
        return {
            "plan": response,
            "phases": self._extract_refactoring_phases(response),
            "risks": self._assess_refactoring_risks(response),
            "metrics": self._define_success_metrics(goals),
            "created_at": datetime.now().isoformat()
        }
    
    def _extract_refactoring_phases(self, plan: str) -> List[Dict[str, Any]]:
        """Extract refactoring phases from plan."""
        # Would implement actual extraction
        return [
            {
                "phase": 1,
                "name": "Extract interfaces",
                "description": "Create interfaces for main components",
                "estimated_hours": 4,
                "dependencies": []
            }
        ]
    
    def _assess_refactoring_risks(self, plan: str) -> List[Dict[str, Any]]:
        """Assess risks in refactoring plan."""
        return [
            {
                "risk": "Breaking changes",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Comprehensive test coverage before refactoring"
            }
        ]
    
    def _define_success_metrics(self, goals: List[str]) -> Dict[str, Any]:
        """Define success metrics based on goals."""
        metrics = {
            "code_coverage": {"target": 80, "current": 0},
            "cyclomatic_complexity": {"target": 10, "current": 0},
            "technical_debt": {"target": "reduced by 50%", "current": "baseline"}
        }
        
        # Add goal-specific metrics
        for goal in goals:
            if "performance" in goal.lower():
                metrics["response_time"] = {"target": "< 100ms", "current": "unknown"}
            elif "security" in goal.lower():
                metrics["vulnerabilities"] = {"target": 0, "current": "unknown"}
        
        return metrics

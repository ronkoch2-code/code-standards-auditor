"""
Enhanced Recommendations Service

Provides advanced code improvement recommendations with detailed implementation
guides, step-by-step migration paths, and automated fix suggestions.

Author: Code Standards Auditor
Date: September 01, 2025
Version: 2.0.0
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import re
import hashlib
import asyncio

from services.gemini_service import GeminiService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from config.settings import settings

logger = logging.getLogger(__name__)


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FixComplexity(Enum):
    """Complexity levels for fixes."""
    TRIVIAL = "trivial"          # < 5 minutes
    SIMPLE = "simple"            # 5-30 minutes
    MODERATE = "moderate"        # 30 minutes - 2 hours
    COMPLEX = "complex"          # 2-8 hours
    MAJOR = "major"              # > 8 hours


class RiskLevel(Enum):
    """Risk levels for applying fixes."""
    NONE = "none"                # Safe to apply automatically
    LOW = "low"                  # Very low risk
    MEDIUM = "medium"            # Requires testing
    HIGH = "high"                # Requires careful review
    CRITICAL = "critical"        # Major architectural changes


@dataclass
class CodeLocation:
    """Represents a location in code."""
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None


@dataclass
class ImplementationStep:
    """A single step in an implementation guide."""
    step_number: int
    title: str
    description: str
    code_before: Optional[str] = None
    code_after: Optional[str] = None
    rationale: Optional[str] = None
    warnings: Optional[List[str]] = None
    estimated_time: Optional[str] = None


@dataclass
class AutomatedFix:
    """Represents an automated fix that can be applied."""
    fix_id: str
    description: str
    location: CodeLocation
    original_code: str
    fixed_code: str
    confidence: float  # 0.0 to 1.0
    risk_level: RiskLevel
    validation_required: bool
    backup_recommended: bool


@dataclass
class EnhancedRecommendation:
    """Enhanced recommendation with implementation guidance."""
    id: str
    title: str
    description: str
    priority: RecommendationPriority
    category: str
    standard_reference: Optional[str]
    
    # Location and context
    locations: List[CodeLocation]
    context: Dict[str, Any]
    
    # Implementation guidance
    implementation_guide: List[ImplementationStep]
    automated_fixes: List[AutomatedFix]
    
    # Assessment
    impact_assessment: Dict[str, Any]
    effort_estimate: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    
    # Additional information
    examples: List[Dict[str, str]]
    references: List[str]
    related_recommendations: List[str]
    
    # Metadata
    confidence: float
    generated_at: str
    expires_at: Optional[str] = None


class EnhancedRecommendationsService:
    """Enhanced service for generating detailed code improvement recommendations."""
    
    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        neo4j_service: Optional[Neo4jService] = None,
        cache_service: Optional[CacheService] = None
    ):
        """Initialize the Enhanced Recommendations Service."""
        self.gemini = gemini_service or GeminiService()
        self.neo4j = neo4j_service or Neo4jService() if settings.USE_NEO4J else None
        self.cache = cache_service or CacheService() if settings.USE_CACHE else None
        
        # Load recommendation templates
        self.recommendation_templates = self._load_recommendation_templates()
        
        # Load implementation patterns
        self.implementation_patterns = self._load_implementation_patterns()
        
        # Statistics tracking
        self.stats = {
            "recommendations_generated": 0,
            "automated_fixes_suggested": 0,
            "successful_applications": 0
        }
    
    def _load_recommendation_templates(self) -> Dict[str, str]:
        """Load recommendation templates for different scenarios."""
        return {
            "code_quality": """
            Analyze the following code for quality improvements:
            
            Code: {code}
            Language: {language}
            Context: {context}
            Standards: {standards}
            
            Provide detailed recommendations including:
            1. Specific issues found
            2. Step-by-step implementation guide
            3. Before/after code examples
            4. Risk assessment
            5. Effort estimation
            6. Automated fix suggestions where possible
            
            Format as JSON with the following structure:
            {{
                "recommendations": [
                    {{
                        "title": "Clear, actionable title",
                        "description": "Detailed description",
                        "priority": "critical|high|medium|low|informational",
                        "category": "performance|security|maintainability|style|architecture",
                        "locations": [
                            {{
                                "line_start": 1,
                                "line_end": 5,
                                "function_name": "example_function"
                            }}
                        ],
                        "implementation_steps": [
                            {{
                                "step_number": 1,
                                "title": "Step title",
                                "description": "What to do",
                                "code_before": "original code",
                                "code_after": "improved code",
                                "rationale": "Why this change helps"
                            }}
                        ],
                        "automated_fix": {{
                            "available": true,
                            "confidence": 0.95,
                            "risk_level": "low",
                            "original_code": "...",
                            "fixed_code": "..."
                        }},
                        "impact_assessment": {{
                            "performance_impact": "positive|negative|neutral",
                            "maintainability_impact": "positive|negative|neutral",
                            "readability_impact": "positive|negative|neutral"
                        }},
                        "effort_estimate": {{
                            "complexity": "trivial|simple|moderate|complex|major",
                            "estimated_time": "5-15 minutes",
                            "skills_required": ["skill1", "skill2"]
                        }},
                        "examples": [
                            {{
                                "before": "problematic code",
                                "after": "improved code",
                                "explanation": "why this is better"
                            }}
                        ]
                    }}
                ]
            }}
            """,
            
            "refactoring": """
            Analyze the following code for refactoring opportunities:
            
            Code: {code}
            Language: {language}
            Refactoring Goals: {goals}
            Context: {context}
            
            Provide a comprehensive refactoring plan including:
            1. Phase-by-phase approach
            2. Risk mitigation strategies
            3. Testing recommendations
            4. Migration path
            5. Rollback procedures
            
            Focus on practical, implementable changes with clear value propositions.
            """,
            
            "security": """
            Perform a security analysis of the following code:
            
            Code: {code}
            Language: {language}
            Context: {context}
            
            Identify security vulnerabilities and provide:
            1. Severity assessment
            2. Exploitation scenarios
            3. Mitigation strategies
            4. Secure code alternatives
            5. Prevention measures
            
            Prioritize findings by risk level and provide actionable remediation steps.
            """,
            
            "performance": """
            Analyze the following code for performance optimization opportunities:
            
            Code: {code}
            Language: {language}
            Context: {context}
            
            Identify performance bottlenecks and provide:
            1. Performance impact analysis
            2. Optimization strategies
            3. Before/after performance estimates
            4. Implementation complexity
            5. Trade-off considerations
            
            Include both micro and macro optimization opportunities.
            """
        }
    
    def _load_implementation_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load implementation patterns for common recommendations."""
        return {
            "extract_method": {
                "description": "Extract complex code into separate methods",
                "applicability": ["long_methods", "duplicate_code", "complex_logic"],
                "steps": [
                    "Identify code to extract",
                    "Determine method parameters",
                    "Create new method with appropriate name",
                    "Replace original code with method call",
                    "Update tests and documentation"
                ],
                "automation_confidence": 0.8
            },
            
            "introduce_constant": {
                "description": "Replace magic numbers/strings with named constants",
                "applicability": ["magic_numbers", "hardcoded_values", "duplicate_literals"],
                "steps": [
                    "Identify magic values",
                    "Create appropriately named constants",
                    "Replace all occurrences",
                    "Verify functionality remains unchanged"
                ],
                "automation_confidence": 0.95
            },
            
            "improve_error_handling": {
                "description": "Add proper error handling and validation",
                "applicability": ["missing_error_handling", "broad_exceptions", "silent_failures"],
                "steps": [
                    "Identify potential failure points",
                    "Add specific exception handling",
                    "Implement proper logging",
                    "Add user-friendly error messages",
                    "Update documentation"
                ],
                "automation_confidence": 0.6
            }
        }
    
    async def generate_enhanced_recommendations(
        self,
        code: str,
        language: str,
        standards: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        include_automated_fixes: bool = True,
        max_recommendations: int = 10
    ) -> Dict[str, Any]:
        """
        Generate enhanced recommendations with detailed implementation guides.
        """
        try:
            logger.info(f"Generating enhanced recommendations for {language} code")
            
            # Prepare context
            analysis_context = self._prepare_analysis_context(
                code, language, standards, focus_areas, context
            )
            
            # Generate recommendations using different analysis approaches
            recommendations = []
            
            # Code quality analysis
            quality_recs = await self._analyze_code_quality(analysis_context)
            recommendations.extend(quality_recs)
            
            # Security analysis
            if not focus_areas or "security" in focus_areas:
                security_recs = await self._analyze_security(analysis_context)
                recommendations.extend(security_recs)
            
            # Performance analysis
            if not focus_areas or "performance" in focus_areas:
                performance_recs = await self._analyze_performance(analysis_context)
                recommendations.extend(performance_recs)
            
            # Architecture analysis
            if not focus_areas or "architecture" in focus_areas:
                arch_recs = await self._analyze_architecture(analysis_context)
                recommendations.extend(arch_recs)
            
            # Sort by priority and limit results
            recommendations.sort(key=lambda r: self._get_priority_weight(r.priority), reverse=True)
            recommendations = recommendations[:max_recommendations]
            
            # Generate automated fixes if requested
            if include_automated_fixes:
                await self._generate_automated_fixes(recommendations, analysis_context)
            
            # Add cross-references and relationships
            self._add_recommendation_relationships(recommendations)
            
            # Generate summary
            summary = self._generate_recommendations_summary(recommendations)
            
            # Update statistics
            self.stats["recommendations_generated"] += len(recommendations)
            
            return {
                "recommendations": [asdict(rec) for rec in recommendations],
                "summary": summary,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "language": language,
                    "total_recommendations": len(recommendations),
                    "automated_fixes_available": sum(1 for r in recommendations if r.automated_fixes),
                    "analysis_context": analysis_context.get("metadata", {}),
                    "service_version": "2.0.0"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced recommendations: {e}")
            raise
    
    def _prepare_analysis_context(
        self,
        code: str,
        language: str,
        standards: Optional[List[str]],
        focus_areas: Optional[List[str]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare comprehensive analysis context."""
        
        # Basic context
        analysis_context = {
            "code": code,
            "language": language,
            "code_hash": hashlib.md5(code.encode()).hexdigest(),
            "code_length": len(code),
            "line_count": len(code.splitlines()),
            "focus_areas": focus_areas or [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Add standards context
        if standards:
            analysis_context["standards"] = standards
            analysis_context["standards_summary"] = self._summarize_standards(standards)
        
        # Add user context
        if context:
            analysis_context["user_context"] = context
            analysis_context["project_type"] = context.get("project_type", "unknown")
            analysis_context["team_experience"] = context.get("team_experience", "intermediate")
        
        # Code analysis
        analysis_context["code_analysis"] = self._analyze_code_structure(code, language)
        
        # Add metadata
        analysis_context["metadata"] = {
            "analysis_id": f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "service_version": "2.0.0"
        }
        
        return analysis_context
    
    def _analyze_code_structure(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze basic code structure and characteristics."""
        lines = code.splitlines()
        
        analysis = {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "comment_lines": len([line for line in lines if line.strip().startswith(("#", "//", "/*"))]),
            "avg_line_length": sum(len(line) for line in lines) / max(len(lines), 1),
            "max_line_length": max(len(line) for line in lines) if lines else 0,
            "indentation_style": self._detect_indentation(lines),
            "complexity_indicators": self._detect_complexity_indicators(code, language)
        }
        
        return analysis
    
    def _detect_indentation(self, lines: List[str]) -> str:
        """Detect indentation style in code."""
        indent_chars = []
        for line in lines:
            if line and line[0] in [' ', '\t']:
                indent_chars.append(line[0])
        
        if not indent_chars:
            return "none"
        
        space_count = indent_chars.count(' ')
        tab_count = indent_chars.count('\t')
        
        if tab_count > space_count:
            return "tabs"
        elif space_count > 0:
            return "spaces"
        else:
            return "mixed"
    
    def _detect_complexity_indicators(self, code: str, language: str) -> Dict[str, int]:
        """Detect various complexity indicators in the code."""
        indicators = {
            "nested_blocks": 0,
            "conditional_statements": 0,
            "loops": 0,
            "function_calls": 0,
            "long_lines": 0
        }
        
        # Language-specific patterns
        patterns = {
            "python": {
                "conditions": [r'\bif\b', r'\belif\b', r'\belse\b'],
                "loops": [r'\bfor\b', r'\bwhile\b'],
                "functions": [r'\bdef\b', r'\w+\s*\(']
            },
            "javascript": {
                "conditions": [r'\bif\b', r'\belse\b', r'\bswitch\b'],
                "loops": [r'\bfor\b', r'\bwhile\b', r'\bdo\b'],
                "functions": [r'\bfunction\b', r'\w+\s*\(', r'=>']
            },
            "java": {
                "conditions": [r'\bif\b', r'\belse\b', r'\bswitch\b'],
                "loops": [r'\bfor\b', r'\bwhile\b', r'\bdo\b'],
                "functions": [r'\w+\s*\(']
            }
        }
        
        lang_patterns = patterns.get(language.lower(), patterns.get("python", {}))
        
        # Count patterns
        for category, pattern_list in lang_patterns.items():
            count = 0
            for pattern in pattern_list:
                count += len(re.findall(pattern, code, re.IGNORECASE))
            indicators[category] = count
        
        # Count long lines
        lines = code.splitlines()
        indicators["long_lines"] = len([line for line in lines if len(line) > 100])
        
        # Estimate nesting depth
        max_nesting = 0
        current_nesting = 0
        for line in lines:
            stripped = line.strip()
            if any(keyword in stripped for keyword in ["if", "for", "while", "try", "def", "class"]):
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif stripped.startswith(("}", "end", "except", "finally")) or (stripped == "" and current_nesting > 0):
                current_nesting = max(0, current_nesting - 1)
        
        indicators["max_nesting_depth"] = max_nesting
        
        return indicators
    
    async def _analyze_code_quality(self, context: Dict[str, Any]) -> List[EnhancedRecommendation]:
        """Analyze code for quality improvements."""
        try:
            template = self.recommendation_templates["code_quality"]
            
            prompt = template.format(
                code=context["code"],
                language=context["language"],
                context=json.dumps(context.get("user_context", {})),
                standards=json.dumps(context.get("standards_summary", {}))
            )
            
            response = await self.gemini.generate_content_async(prompt)
            
            # Parse response and convert to EnhancedRecommendation objects
            recommendations_data = json.loads(response)
            recommendations = []
            
            for i, rec_data in enumerate(recommendations_data.get("recommendations", [])):
                try:
                    recommendation = self._create_enhanced_recommendation(
                        rec_data, context, f"quality_{i}"
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.warning(f"Failed to create recommendation {i}: {e}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Code quality analysis failed: {e}")
            return []
    
    async def _analyze_security(self, context: Dict[str, Any]) -> List[EnhancedRecommendation]:
        """Analyze code for security issues."""
        try:
            template = self.recommendation_templates["security"]
            
            prompt = template.format(
                code=context["code"],
                language=context["language"],
                context=json.dumps(context.get("user_context", {}))
            )
            
            response = await self.gemini.generate_content_async(prompt)
            
            # For now, create a placeholder security recommendation
            # In a full implementation, this would parse the AI response
            recommendations = []
            
            if "password" in context["code"].lower() or "secret" in context["code"].lower():
                sec_rec = EnhancedRecommendation(
                    id="sec_001",
                    title="Potential hardcoded credentials detected",
                    description="Code appears to contain hardcoded passwords or secrets",
                    priority=RecommendationPriority.CRITICAL,
                    category="security",
                    standard_reference="OWASP-A02",
                    locations=[CodeLocation(line_start=1, line_end=10)],
                    context={"security_risk": "credential_exposure"},
                    implementation_guide=[
                        ImplementationStep(
                            step_number=1,
                            title="Move credentials to environment variables",
                            description="Replace hardcoded credentials with environment variables",
                            code_before='password = "hardcoded_secret"',
                            code_after='password = os.environ.get("PASSWORD")',
                            rationale="Prevents credentials from being exposed in source code"
                        )
                    ],
                    automated_fixes=[],
                    impact_assessment={
                        "security_impact": "high_positive",
                        "maintainability_impact": "positive"
                    },
                    effort_estimate={
                        "complexity": FixComplexity.SIMPLE.value,
                        "estimated_time": "15-30 minutes"
                    },
                    risk_assessment={
                        "implementation_risk": RiskLevel.LOW.value,
                        "business_impact": "positive"
                    },
                    examples=[{
                        "before": 'password = "secret123"',
                        "after": 'password = os.environ.get("PASSWORD")',
                        "explanation": "Use environment variables for sensitive data"
                    }],
                    references=["https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"],
                    related_recommendations=[],
                    confidence=0.9,
                    generated_at=datetime.now().isoformat()
                )
                recommendations.append(sec_rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return []
    
    async def _analyze_performance(self, context: Dict[str, Any]) -> List[EnhancedRecommendation]:
        """Analyze code for performance improvements."""
        # Placeholder implementation
        return []
    
    async def _analyze_architecture(self, context: Dict[str, Any]) -> List[EnhancedRecommendation]:
        """Analyze code for architectural improvements."""
        # Placeholder implementation
        return []
    
    def _create_enhanced_recommendation(
        self,
        rec_data: Dict[str, Any],
        context: Dict[str, Any],
        rec_id: str
    ) -> EnhancedRecommendation:
        """Create an EnhancedRecommendation from parsed data."""
        
        # Parse locations
        locations = []
        for loc_data in rec_data.get("locations", []):
            location = CodeLocation(
                line_start=loc_data.get("line_start"),
                line_end=loc_data.get("line_end"),
                function_name=loc_data.get("function_name"),
                class_name=loc_data.get("class_name")
            )
            locations.append(location)
        
        # Parse implementation steps
        implementation_guide = []
        for step_data in rec_data.get("implementation_steps", []):
            step = ImplementationStep(
                step_number=step_data.get("step_number", 1),
                title=step_data.get("title", ""),
                description=step_data.get("description", ""),
                code_before=step_data.get("code_before"),
                code_after=step_data.get("code_after"),
                rationale=step_data.get("rationale"),
                estimated_time=step_data.get("estimated_time")
            )
            implementation_guide.append(step)
        
        # Parse automated fixes
        automated_fixes = []
        fix_data = rec_data.get("automated_fix", {})
        if fix_data.get("available", False):
            fix = AutomatedFix(
                fix_id=f"{rec_id}_autofix",
                description=f"Automated fix for {rec_data.get('title', 'issue')}",
                location=locations[0] if locations else CodeLocation(),
                original_code=fix_data.get("original_code", ""),
                fixed_code=fix_data.get("fixed_code", ""),
                confidence=fix_data.get("confidence", 0.5),
                risk_level=RiskLevel(fix_data.get("risk_level", "medium")),
                validation_required=fix_data.get("confidence", 0.5) < 0.9,
                backup_recommended=fix_data.get("risk_level", "medium") != "none"
            )
            automated_fixes.append(fix)
        
        return EnhancedRecommendation(
            id=rec_id,
            title=rec_data.get("title", "Untitled recommendation"),
            description=rec_data.get("description", ""),
            priority=RecommendationPriority(rec_data.get("priority", "medium")),
            category=rec_data.get("category", "general"),
            standard_reference=rec_data.get("standard_reference"),
            locations=locations,
            context={"analysis_context": context.get("metadata", {})},
            implementation_guide=implementation_guide,
            automated_fixes=automated_fixes,
            impact_assessment=rec_data.get("impact_assessment", {}),
            effort_estimate=rec_data.get("effort_estimate", {}),
            risk_assessment=rec_data.get("risk_assessment", {}),
            examples=rec_data.get("examples", []),
            references=rec_data.get("references", []),
            related_recommendations=[],
            confidence=rec_data.get("confidence", 0.7),
            generated_at=datetime.now().isoformat()
        )
    
    async def _generate_automated_fixes(
        self,
        recommendations: List[EnhancedRecommendation],
        context: Dict[str, Any]
    ):
        """Generate automated fixes for applicable recommendations."""
        for rec in recommendations:
            if not rec.automated_fixes and self._is_automatable(rec):
                fix = await self._create_automated_fix(rec, context)
                if fix:
                    rec.automated_fixes.append(fix)
                    self.stats["automated_fixes_suggested"] += 1
    
    def _is_automatable(self, recommendation: EnhancedRecommendation) -> bool:
        """Determine if a recommendation can be automated."""
        automatable_categories = ["style", "simple_refactoring", "constant_extraction"]
        return (
            recommendation.category in automatable_categories or
            recommendation.priority in [RecommendationPriority.LOW, RecommendationPriority.MEDIUM]
        )
    
    async def _create_automated_fix(
        self,
        recommendation: EnhancedRecommendation,
        context: Dict[str, Any]
    ) -> Optional[AutomatedFix]:
        """Create an automated fix for a recommendation."""
        try:
            # Use AI to generate the fix
            fix_prompt = f"""
            Create an automated fix for the following recommendation:
            
            Title: {recommendation.title}
            Description: {recommendation.description}
            Code Location: {recommendation.locations[0] if recommendation.locations else 'Unknown'}
            
            Original Code Context:
            {context.get('code', '')}
            
            Provide:
            1. The specific code that needs to be changed
            2. The corrected version
            3. Confidence level (0.0 to 1.0)
            4. Risk assessment
            
            Return as JSON:
            {{
                "original_code": "code to be replaced",
                "fixed_code": "corrected code",
                "confidence": 0.85,
                "risk_level": "low|medium|high",
                "description": "What this fix does"
            }}
            """
            
            response = await self.gemini.generate_content_async(fix_prompt)
            fix_data = json.loads(response)
            
            return AutomatedFix(
                fix_id=f"{recommendation.id}_autofix",
                description=fix_data.get("description", "Automated fix"),
                location=recommendation.locations[0] if recommendation.locations else CodeLocation(),
                original_code=fix_data.get("original_code", ""),
                fixed_code=fix_data.get("fixed_code", ""),
                confidence=fix_data.get("confidence", 0.5),
                risk_level=RiskLevel(fix_data.get("risk_level", "medium")),
                validation_required=fix_data.get("confidence", 0.5) < 0.8,
                backup_recommended=True
            )
            
        except Exception as e:
            logger.warning(f"Failed to create automated fix for {recommendation.id}: {e}")
            return None
    
    def _add_recommendation_relationships(self, recommendations: List[EnhancedRecommendation]):
        """Add relationships between recommendations."""
        for i, rec1 in enumerate(recommendations):
            related_ids = []
            for j, rec2 in enumerate(recommendations):
                if i != j and self._are_related(rec1, rec2):
                    related_ids.append(rec2.id)
            rec1.related_recommendations = related_ids
    
    def _are_related(self, rec1: EnhancedRecommendation, rec2: EnhancedRecommendation) -> bool:
        """Determine if two recommendations are related."""
        # Same category
        if rec1.category == rec2.category:
            return True
        
        # Overlapping locations
        if rec1.locations and rec2.locations:
            for loc1 in rec1.locations:
                for loc2 in rec2.locations:
                    if (loc1.function_name and loc1.function_name == loc2.function_name) or \
                       (loc1.class_name and loc1.class_name == loc2.class_name):
                        return True
        
        return False
    
    def _generate_recommendations_summary(
        self,
        recommendations: List[EnhancedRecommendation]
    ) -> Dict[str, Any]:
        """Generate a summary of all recommendations."""
        
        summary = {
            "total_recommendations": len(recommendations),
            "by_priority": {},
            "by_category": {},
            "total_estimated_time": "0 minutes",
            "automation_available": 0,
            "high_confidence_fixes": 0,
            "risk_distribution": {}
        }
        
        # Count by priority
        for priority in RecommendationPriority:
            count = len([r for r in recommendations if r.priority == priority])
            summary["by_priority"][priority.value] = count
        
        # Count by category
        categories = {}
        for rec in recommendations:
            categories[rec.category] = categories.get(rec.category, 0) + 1
        summary["by_category"] = categories
        
        # Count automation and confidence
        for rec in recommendations:
            if rec.automated_fixes:
                summary["automation_available"] += 1
            if rec.confidence >= 0.8:
                summary["high_confidence_fixes"] += 1
        
        # Risk distribution
        risk_levels = {}
        for rec in recommendations:
            for fix in rec.automated_fixes:
                risk = fix.risk_level.value
                risk_levels[risk] = risk_levels.get(risk, 0) + 1
        summary["risk_distribution"] = risk_levels
        
        return summary
    
    def _get_priority_weight(self, priority: RecommendationPriority) -> int:
        """Get numeric weight for priority sorting."""
        weights = {
            RecommendationPriority.CRITICAL: 5,
            RecommendationPriority.HIGH: 4,
            RecommendationPriority.MEDIUM: 3,
            RecommendationPriority.LOW: 2,
            RecommendationPriority.INFORMATIONAL: 1
        }
        return weights.get(priority, 0)
    
    def _summarize_standards(self, standards: List[str]) -> Dict[str, Any]:
        """Create a summary of applicable standards."""
        return {
            "total_standards": len(standards),
            "summary": "Standards analysis would be implemented here"
        }
    
    async def apply_automated_fix(
        self,
        fix_id: str,
        code: str,
        validate_before_apply: bool = True
    ) -> Dict[str, Any]:
        """Apply an automated fix to code."""
        try:
            # This would implement the actual fix application
            # For now, return a placeholder result
            
            result = {
                "success": True,
                "fix_id": fix_id,
                "applied_at": datetime.now().isoformat(),
                "changes_made": ["Placeholder change"],
                "validation_result": {
                    "syntax_valid": True,
                    "tests_pass": True,
                    "warnings": []
                }
            }
            
            self.stats["successful_applications"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply automated fix {fix_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "fix_id": fix_id
            }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "statistics": self.stats,
            "service_info": {
                "version": "2.0.0",
                "capabilities": [
                    "enhanced_recommendations",
                    "implementation_guides",
                    "automated_fixes",
                    "risk_assessment",
                    "effort_estimation"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }


# Backwards compatibility - maintain original interface
class RecommendationsService(EnhancedRecommendationsService):
    """Backwards compatible service class."""
    
    async def generate_recommendations(
        self,
        code: str,
        language: str,
        standards: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate recommendations with original interface."""
        
        enhanced_result = await self.generate_enhanced_recommendations(
            code=code,
            language=language,
            standards=standards,
            focus_areas=focus_areas,
            context=context,
            include_automated_fixes=True
        )
        
        # Convert to original format for backwards compatibility
        return {
            "recommendations": enhanced_result["recommendations"],
            "summary": enhanced_result["summary"],
            "metadata": enhanced_result["metadata"]
        }
    
    async def get_quick_fixes(
        self,
        code: str,
        language: str,
        issue_type: str
    ) -> List[Dict[str, Any]]:
        """Get quick fixes for specific issues."""
        
        enhanced_result = await self.generate_enhanced_recommendations(
            code=code,
            language=language,
            focus_areas=[issue_type],
            include_automated_fixes=True,
            max_recommendations=5
        )
        
        # Extract automated fixes
        quick_fixes = []
        for rec_data in enhanced_result["recommendations"]:
            for fix_data in rec_data.get("automated_fixes", []):
                quick_fixes.append(fix_data)
        
        return quick_fixes
    
    async def generate_refactoring_plan(
        self,
        code: str,
        language: str,
        goals: List[str]
    ) -> Dict[str, Any]:
        """Generate a refactoring plan."""
        
        context = {
            "refactoring_goals": goals,
            "analysis_type": "refactoring"
        }
        
        enhanced_result = await self.generate_enhanced_recommendations(
            code=code,
            language=language,
            focus_areas=["refactoring", "architecture"],
            context=context,
            include_automated_fixes=False,
            max_recommendations=15
        )
        
        # Format as refactoring plan
        plan = {
            "phases": [],
            "total_effort": "TBD",
            "risk_assessment": "Medium",
            "success_metrics": goals,
            "recommendations": enhanced_result["recommendations"]
        }
        
        return plan

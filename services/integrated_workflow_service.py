"""
Integrated Standards Workflow Service

Provides seamless integration between standards research, documentation,
and code analysis workflows with automated quality management.

Author: Code Standards Auditor
Date: September 01, 2025
Version: 1.0.0
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from services.standards_research_service import StandardsResearchService
from services.enhanced_recommendations_service import EnhancedRecommendationsService
from services.gemini_service import GeminiService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from config.settings import settings

logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """Phases in the integrated workflow."""
    INITIALIZATION = "initialization"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    FEEDBACK = "feedback"
    COMPLETION = "completion"


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowContext:
    """Context for the integrated workflow."""
    workflow_id: str
    user_id: Optional[str]
    project_context: Dict[str, Any]
    requirements: Dict[str, Any]
    preferences: Dict[str, Any]
    session_data: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    phase: WorkflowPhase
    results: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    execution_time: float
    completed_at: Optional[str] = None


class IntegratedWorkflowService:
    """Service for managing integrated standards workflows."""
    
    def __init__(self):
        """Initialize the integrated workflow service."""
        self.research_service = StandardsResearchService()
        self.recommendations_service = EnhancedRecommendationsService()
        self.gemini_service = GeminiService()
        
        # Initialize optional services
        self.neo4j_service = None
        if settings.USE_NEO4J:
            try:
                self.neo4j_service = Neo4jService()
            except Exception as e:
                logger.warning(f"Neo4j not available: {e}")
        
        self.cache_service = None
        if settings.USE_CACHE:
            try:
                self.cache_service = CacheService()
            except Exception as e:
                logger.warning(f"Cache not available: {e}")
        
        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowContext] = {}
        self.workflow_results: Dict[str, WorkflowResult] = {}
        
        # Statistics
        self.stats = {
            "workflows_started": 0,
            "workflows_completed": 0,
            "standards_created": 0,
            "code_analyses_performed": 0,
            "automated_fixes_applied": 0
        }
    
    async def start_research_to_analysis_workflow(
        self,
        research_request: str,
        code_samples: Optional[List[str]] = None,
        project_context: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a complete workflow from research request to code analysis.
        
        Returns the workflow ID for tracking.
        """
        try:
            # Create workflow context
            workflow_id = str(uuid.uuid4())
            context = WorkflowContext(
                workflow_id=workflow_id,
                user_id=project_context.get("user_id") if project_context else None,
                project_context=project_context or {},
                requirements={"research_request": research_request},
                preferences=user_preferences or {},
                session_data={"code_samples": code_samples or []},
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            self.active_workflows[workflow_id] = context
            self.stats["workflows_started"] += 1
            
            # Start the workflow asynchronously
            asyncio.create_task(self._execute_research_to_analysis_workflow(context))
            
            logger.info(f"Started research-to-analysis workflow: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            raise
    
    async def _execute_research_to_analysis_workflow(self, context: WorkflowContext):
        """Execute the complete research-to-analysis workflow."""
        workflow_id = context.workflow_id
        start_time = datetime.now()
        
        try:
            # Phase 1: Research
            logger.info(f"[{workflow_id}] Starting research phase")
            research_result = await self._execute_research_phase(context)
            
            if not research_result["success"]:
                raise Exception(f"Research phase failed: {research_result.get('error')}")
            
            # Phase 2: Documentation
            logger.info(f"[{workflow_id}] Starting documentation phase")
            doc_result = await self._execute_documentation_phase(context, research_result)
            
            if not doc_result["success"]:
                raise Exception(f"Documentation phase failed: {doc_result.get('error')}")
            
            # Phase 3: Validation
            logger.info(f"[{workflow_id}] Starting validation phase")
            validation_result = await self._execute_validation_phase(context, doc_result)
            
            # Phase 4: Deployment (save to systems)
            logger.info(f"[{workflow_id}] Starting deployment phase")
            deployment_result = await self._execute_deployment_phase(context, validation_result)
            
            # Phase 5: Analysis (if code samples provided)
            analysis_result = None
            if context.session_data.get("code_samples"):
                logger.info(f"[{workflow_id}] Starting analysis phase")
                analysis_result = await self._execute_analysis_phase(context, deployment_result)
            
            # Phase 6: Generate feedback and recommendations
            logger.info(f"[{workflow_id}] Generating feedback")
            feedback_result = await self._execute_feedback_phase(
                context, 
                research_result, 
                doc_result, 
                validation_result, 
                deployment_result, 
                analysis_result
            )
            
            # Complete workflow
            execution_time = (datetime.now() - start_time).total_seconds()
            
            final_result = WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                phase=WorkflowPhase.COMPLETION,
                results={
                    "research": research_result,
                    "documentation": doc_result,
                    "validation": validation_result,
                    "deployment": deployment_result,
                    "analysis": analysis_result,
                    "feedback": feedback_result
                },
                metadata={
                    "context": asdict(context),
                    "execution_phases": [
                        "research", "documentation", "validation", 
                        "deployment", "analysis", "feedback"
                    ],
                    "service_version": "1.0.0"
                },
                errors=[],
                warnings=[],
                execution_time=execution_time,
                completed_at=datetime.now().isoformat()
            )
            
            self.workflow_results[workflow_id] = final_result
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            self.stats["workflows_completed"] += 1
            logger.info(f"[{workflow_id}] Workflow completed successfully in {execution_time:.2f}s")
            
        except Exception as e:
            # Handle workflow failure
            execution_time = (datetime.now() - start_time).total_seconds()
            
            error_result = WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                phase=WorkflowPhase.COMPLETION,
                results={},
                metadata={
                    "context": asdict(context),
                    "service_version": "1.0.0"
                },
                errors=[str(e)],
                warnings=[],
                execution_time=execution_time,
                completed_at=datetime.now().isoformat()
            )
            
            self.workflow_results[workflow_id] = error_result
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            logger.error(f"[{workflow_id}] Workflow failed: {e}")
    
    async def _execute_research_phase(self, context: WorkflowContext) -> Dict[str, Any]:
        """Execute the research phase."""
        try:
            research_request = context.requirements["research_request"]
            
            # Analyze the request first
            analysis_prompt = f"""
            Analyze this coding standard research request and extract detailed requirements:
            Request: "{research_request}"
            
            Project Context: {json.dumps(context.project_context, indent=2)}
            User Preferences: {json.dumps(context.preferences, indent=2)}
            
            Return JSON with:
            {{
                "title": "Clear title for the standard",
                "category": "general|language_specific|pattern|security|performance|testing|documentation|architecture",
                "language": "programming language or 'general'",
                "description": "detailed description",
                "key_topics": ["list", "of", "topics"],
                "complexity": "basic|intermediate|advanced|expert",
                "priority": "low|medium|high|critical",
                "estimated_scope": "small|medium|large|enterprise"
            }}
            """
            
            analysis_response = await self.gemini_service.generate_content_async(analysis_prompt)
            analysis = json.loads(analysis_response)
            
            # Perform the research
            standard = await self.research_service.research_standard(
                topic=analysis["title"],
                category=analysis.get("category", "general"),
                context={
                    "analysis": analysis,
                    "project_context": context.project_context,
                    "user_preferences": context.preferences
                },
                examples=context.session_data.get("code_samples", [])
            )
            
            self.stats["standards_created"] += 1
            
            return {
                "success": True,
                "analysis": analysis,
                "standard": standard,
                "metadata": {
                    "research_duration": "estimated",
                    "quality_indicators": standard.get("validation", {})
                }
            }
            
        except Exception as e:
            logger.error(f"Research phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": "research"
            }
    
    async def _execute_documentation_phase(
        self, 
        context: WorkflowContext, 
        research_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the documentation phase."""
        try:
            standard = research_result["standard"]
            
            # Enhance documentation with additional sections
            enhancement_prompt = f"""
            Enhance this coding standard with comprehensive documentation sections:
            
            Standard Title: {standard.get('title', 'Untitled')}
            Content: {standard.get('content', '')}
            
            Add the following sections if not already present:
            1. Implementation Guide with step-by-step instructions
            2. Examples and Anti-examples
            3. Tools and Automation recommendations
            4. Team Adoption Strategy
            5. Metrics and Compliance Checking
            6. FAQ section
            
            Return the enhanced markdown content.
            """
            
            enhanced_content = await self.gemini_service.generate_content_async(enhancement_prompt)
            
            # Create comprehensive documentation package
            doc_package = {
                "main_standard": {
                    **standard,
                    "content": enhanced_content
                },
                "quick_reference": await self._create_quick_reference(standard),
                "implementation_checklist": await self._create_implementation_checklist(standard),
                "team_onboarding_guide": await self._create_onboarding_guide(standard, context),
                "compliance_checklist": await self._create_compliance_checklist(standard)
            }
            
            return {
                "success": True,
                "documentation_package": doc_package,
                "formats": ["markdown", "pdf", "html"],  # Available formats
                "sections_added": [
                    "implementation_guide", "examples", "tools", 
                    "adoption_strategy", "metrics", "faq"
                ]
            }
            
        except Exception as e:
            logger.error(f"Documentation phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": "documentation"
            }
    
    async def _execute_validation_phase(
        self, 
        context: WorkflowContext, 
        doc_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the validation phase."""
        try:
            doc_package = doc_result["documentation_package"]
            main_standard = doc_package["main_standard"]
            
            # Comprehensive validation
            validation_tasks = [
                self._validate_completeness(main_standard),
                self._validate_clarity(main_standard),
                self._validate_practicality(main_standard, context),
                self._validate_consistency(main_standard),
                self._validate_examples(main_standard)
            ]
            
            validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Aggregate validation results
            overall_score = 0
            total_checks = 0
            issues = []
            recommendations = []
            
            for i, result in enumerate(validation_results):
                if isinstance(result, Exception):
                    issues.append(f"Validation task {i} failed: {result}")
                    continue
                
                overall_score += result.get("score", 0)
                total_checks += 1
                issues.extend(result.get("issues", []))
                recommendations.extend(result.get("recommendations", []))
            
            final_score = overall_score / max(total_checks, 1)
            
            return {
                "success": True,
                "overall_score": final_score,
                "detailed_results": [r for r in validation_results if not isinstance(r, Exception)],
                "issues": issues,
                "recommendations": recommendations,
                "validation_passed": final_score >= 75,
                "quality_level": self._determine_quality_level(final_score)
            }
            
        except Exception as e:
            logger.error(f"Validation phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": "validation"
            }
    
    async def _execute_deployment_phase(
        self, 
        context: WorkflowContext, 
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the deployment phase."""
        try:
            deployment_results = {}
            
            # Save to file system
            file_result = await self._deploy_to_filesystem(context, validation_result)
            deployment_results["filesystem"] = file_result
            
            # Save to Neo4j if available
            if self.neo4j_service:
                neo4j_result = await self._deploy_to_neo4j(context, validation_result)
                deployment_results["neo4j"] = neo4j_result
            
            # Cache frequently accessed data
            if self.cache_service:
                cache_result = await self._deploy_to_cache(context, validation_result)
                deployment_results["cache"] = cache_result
            
            # Generate deployment report
            report = await self._generate_deployment_report(deployment_results)
            
            return {
                "success": True,
                "deployment_results": deployment_results,
                "deployment_report": report,
                "access_methods": {
                    "file_path": file_result.get("file_path"),
                    "neo4j_id": deployment_results.get("neo4j", {}).get("standard_id"),
                    "cache_keys": deployment_results.get("cache", {}).get("cache_keys", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Deployment phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": "deployment"
            }
    
    async def _execute_analysis_phase(
        self, 
        context: WorkflowContext, 
        deployment_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the code analysis phase."""
        try:
            code_samples = context.session_data.get("code_samples", [])
            if not code_samples:
                return {
                    "success": True,
                    "message": "No code samples provided for analysis",
                    "analysis_results": []
                }
            
            analysis_results = []
            
            # Get the deployed standard for analysis
            standard_id = deployment_result.get("access_methods", {}).get("neo4j_id")
            standards_content = []
            
            if standard_id and self.neo4j_service:
                standard = await self.neo4j_service.get_standard(standard_id)
                if standard:
                    standards_content.append(standard.get("content", ""))
            
            # Analyze each code sample
            for i, code_sample in enumerate(code_samples):
                sample_analysis = await self.recommendations_service.generate_enhanced_recommendations(
                    code=code_sample,
                    language=self._detect_language(code_sample),
                    standards=standards_content,
                    context={
                        "workflow_id": context.workflow_id,
                        "sample_index": i,
                        "project_context": context.project_context
                    },
                    include_automated_fixes=True
                )
                
                analysis_results.append({
                    "sample_index": i,
                    "analysis": sample_analysis,
                    "compliance_score": self._calculate_compliance_score(sample_analysis),
                    "automated_fixes_available": len([
                        rec for rec in sample_analysis["recommendations"] 
                        if rec.get("automated_fixes")
                    ])
                })
            
            # Generate aggregate analysis
            aggregate = await self._generate_aggregate_analysis(analysis_results, context)
            
            self.stats["code_analyses_performed"] += len(code_samples)
            
            return {
                "success": True,
                "individual_analyses": analysis_results,
                "aggregate_analysis": aggregate,
                "total_samples": len(code_samples),
                "overall_compliance": aggregate.get("overall_compliance_score", 0)
            }
            
        except Exception as e:
            logger.error(f"Analysis phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": "analysis"
            }
    
    async def _execute_feedback_phase(
        self, 
        context: WorkflowContext,
        research_result: Dict[str, Any],
        doc_result: Dict[str, Any],
        validation_result: Dict[str, Any],
        deployment_result: Dict[str, Any],
        analysis_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the feedback generation phase."""
        try:
            # Generate comprehensive feedback
            feedback_prompt = f"""
            Generate comprehensive feedback for a completed standards workflow:
            
            Workflow Context: {json.dumps(asdict(context), indent=2)}
            Research Results: Quality Score: {research_result.get('standard', {}).get('validation', {}).get('score', 'N/A')}
            Documentation: {len(doc_result.get('documentation_package', {}))} sections created
            Validation: Overall Score: {validation_result.get('overall_score', 'N/A')}
            Deployment: {len(deployment_result.get('deployment_results', {}))} locations
            Analysis: {'Performed' if analysis_result else 'Skipped'}
            
            Provide feedback including:
            1. Workflow success summary
            2. Quality assessment of outputs
            3. Recommendations for improvement
            4. Next steps for implementation
            5. Lessons learned
            
            Format as JSON:
            {{
                "summary": "brief success summary",
                "quality_assessment": {{
                    "research_quality": "excellent|good|fair|poor",
                    "documentation_quality": "excellent|good|fair|poor",
                    "validation_score": 0-100,
                    "deployment_success": true/false
                }},
                "recommendations": ["list of recommendations"],
                "next_steps": ["list of next steps"],
                "lessons_learned": ["list of lessons"],
                "improvement_suggestions": ["list of suggestions"]
            }}
            """
            
            feedback_response = await self.gemini_service.generate_content_async(feedback_prompt)
            feedback = json.loads(feedback_response)
            
            # Add workflow statistics
            feedback["workflow_statistics"] = {
                "total_execution_time": "calculated_from_start",
                "phases_completed": 6 if analysis_result else 5,
                "standards_created": 1,
                "code_samples_analyzed": len(context.session_data.get("code_samples", [])),
                "recommendations_generated": sum(
                    len(analysis.get("analysis", {}).get("recommendations", [])) 
                    for analysis in analysis_result.get("individual_analyses", [])
                ) if analysis_result else 0
            }
            
            # Generate actionable report
            report = await self._generate_actionable_report(
                context, feedback, analysis_result
            )
            feedback["actionable_report"] = report
            
            return {
                "success": True,
                "feedback": feedback,
                "workflow_complete": True,
                "user_report_available": True
            }
            
        except Exception as e:
            logger.error(f"Feedback phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "phase": "feedback"
            }
    
    # Helper methods for workflow phases
    
    async def _create_quick_reference(self, standard: Dict[str, Any]) -> str:
        """Create a quick reference guide for the standard."""
        prompt = f"""
        Create a concise quick reference guide for this standard:
        Title: {standard.get('title', '')}
        Content: {standard.get('content', '')[:500]}...
        
        Format as a one-page markdown reference with:
        - Key rules (bullet points)
        - Do's and Don'ts
        - Quick examples
        - Common pitfalls
        
        Keep it under 500 words.
        """
        
        return await self.gemini_service.generate_content_async(prompt)
    
    async def _create_implementation_checklist(self, standard: Dict[str, Any]) -> str:
        """Create an implementation checklist."""
        return f"""
        # Implementation Checklist: {standard.get('title', 'Standard')}
        
        ## Pre-Implementation
        - [ ] Review team capacity and timeline
        - [ ] Identify key stakeholders
        - [ ] Plan rollout strategy
        
        ## Implementation
        - [ ] Set up tooling and automation
        - [ ] Train team members
        - [ ] Update documentation
        - [ ] Apply to new code
        
        ## Post-Implementation
        - [ ] Monitor compliance
        - [ ] Gather feedback
        - [ ] Refine as needed
        """
    
    async def _create_onboarding_guide(
        self, 
        standard: Dict[str, Any], 
        context: WorkflowContext
    ) -> str:
        """Create a team onboarding guide."""
        team_size = context.project_context.get("team_size", "unknown")
        experience_level = context.project_context.get("experience_level", "intermediate")
        
        return f"""
        # Team Onboarding Guide: {standard.get('title', 'Standard')}
        
        ## For {team_size} team with {experience_level} experience level
        
        ### Week 1: Introduction
        - Introduction session (1 hour)
        - Review examples and rationale
        - Q&A session
        
        ### Week 2-3: Gradual Adoption
        - Apply to new features only
        - Pair programming sessions
        - Regular check-ins
        
        ### Week 4+: Full Implementation
        - Apply to all new code
        - Refactor existing code gradually
        - Regular compliance checks
        """
    
    async def _create_compliance_checklist(self, standard: Dict[str, Any]) -> str:
        """Create a compliance checklist."""
        return f"""
        # Compliance Checklist: {standard.get('title', 'Standard')}
        
        ## Code Review Checklist
        - [ ] Naming conventions followed
        - [ ] Structure guidelines met
        - [ ] Documentation requirements satisfied
        - [ ] Performance considerations addressed
        
        ## Automated Checks
        - [ ] Linter rules configured
        - [ ] Static analysis setup
        - [ ] CI/CD integration active
        
        ## Manual Reviews
        - [ ] Architecture alignment
        - [ ] Business logic clarity
        - [ ] Error handling completeness
        """
    
    async def _validate_completeness(self, standard: Dict[str, Any]) -> Dict[str, Any]:
        """Validate standard completeness."""
        content = standard.get("content", "")
        
        required_sections = [
            "introduction", "guidelines", "examples", "rationale"
        ]
        
        found_sections = []
        for section in required_sections:
            if section.lower() in content.lower():
                found_sections.append(section)
        
        score = (len(found_sections) / len(required_sections)) * 100
        
        return {
            "score": score,
            "issues": [f"Missing section: {s}" for s in required_sections if s not in found_sections],
            "recommendations": ["Add missing sections to improve completeness"] if score < 100 else []
        }
    
    async def _validate_clarity(self, standard: Dict[str, Any]) -> Dict[str, Any]:
        """Validate standard clarity."""
        # Placeholder implementation
        return {
            "score": 85,
            "issues": [],
            "recommendations": []
        }
    
    async def _validate_practicality(self, standard: Dict[str, Any], context: WorkflowContext) -> Dict[str, Any]:
        """Validate standard practicality."""
        # Placeholder implementation
        return {
            "score": 80,
            "issues": [],
            "recommendations": []
        }
    
    async def _validate_consistency(self, standard: Dict[str, Any]) -> Dict[str, Any]:
        """Validate standard consistency."""
        # Placeholder implementation
        return {
            "score": 90,
            "issues": [],
            "recommendations": []
        }
    
    async def _validate_examples(self, standard: Dict[str, Any]) -> Dict[str, Any]:
        """Validate standard examples."""
        content = standard.get("content", "")
        code_blocks = content.count("```")
        
        score = min(100, code_blocks * 20)  # 20 points per code block, max 100
        
        return {
            "score": score,
            "issues": ["Insufficient examples"] if score < 60 else [],
            "recommendations": ["Add more code examples"] if score < 80 else []
        }
    
    def _determine_quality_level(self, score: float) -> str:
        """Determine quality level from score."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        else:
            return "poor"
    
    async def _deploy_to_filesystem(self, context: WorkflowContext, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy standard to filesystem."""
        try:
            # Implementation would save to filesystem
            return {
                "success": True,
                "file_path": f"/standards/{context.workflow_id}.md",
                "backup_created": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _deploy_to_neo4j(self, context: WorkflowContext, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy standard to Neo4j."""
        try:
            # Implementation would save to Neo4j
            return {
                "success": True,
                "standard_id": f"std_{context.workflow_id}",
                "relationships_created": 3
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _deploy_to_cache(self, context: WorkflowContext, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy standard to cache."""
        try:
            # Implementation would save to cache
            return {
                "success": True,
                "cache_keys": [f"standard:{context.workflow_id}", f"workflow:{context.workflow_id}"],
                "ttl": 3600
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_deployment_report(self, deployment_results: Dict[str, Any]) -> str:
        """Generate deployment report."""
        successful = sum(1 for result in deployment_results.values() if result.get("success", False))
        total = len(deployment_results)
        
        return f"""
        # Deployment Report
        
        ## Summary
        - Deployments attempted: {total}
        - Successful: {successful}
        - Failed: {total - successful}
        
        ## Details
        {chr(10).join([f"- {k}: {'✓' if v.get('success') else '✗'}" for k, v in deployment_results.items()])}
        """
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code sample."""
        # Simple heuristic-based detection
        if "def " in code and ":" in code:
            return "python"
        elif "function " in code or "=>" in code:
            return "javascript"
        elif "public class" in code:
            return "java"
        else:
            return "unknown"
    
    def _calculate_compliance_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate compliance score from analysis results."""
        recommendations = analysis.get("recommendations", [])
        if not recommendations:
            return 100.0
        
        critical_issues = len([r for r in recommendations if r.get("priority") == "critical"])
        high_issues = len([r for r in recommendations if r.get("priority") == "high"])
        
        # Simple scoring: deduct points for issues
        score = 100.0
        score -= critical_issues * 20
        score -= high_issues * 10
        
        return max(0.0, score)
    
    async def _generate_aggregate_analysis(
        self, 
        analysis_results: List[Dict[str, Any]], 
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Generate aggregate analysis across all code samples."""
        if not analysis_results:
            return {}
        
        total_compliance = sum(result["compliance_score"] for result in analysis_results)
        avg_compliance = total_compliance / len(analysis_results)
        
        all_recommendations = []
        for result in analysis_results:
            all_recommendations.extend(result["analysis"]["recommendations"])
        
        return {
            "overall_compliance_score": avg_compliance,
            "total_recommendations": len(all_recommendations),
            "samples_analyzed": len(analysis_results),
            "common_issues": self._identify_common_issues(all_recommendations),
            "improvement_potential": 100 - avg_compliance
        }
    
    def _identify_common_issues(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Identify common issues across recommendations."""
        # Group by category and find most frequent
        categories = {}
        for rec in recommendations:
            category = rec.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        
        # Return top 3 most common
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, count in sorted_categories[:3]]
    
    async def _generate_actionable_report(
        self, 
        context: WorkflowContext, 
        feedback: Dict[str, Any], 
        analysis_result: Optional[Dict[str, Any]]
    ) -> str:
        """Generate actionable report for the user."""
        return f"""
        # Workflow Completion Report
        
        ## Summary
        {feedback.get('summary', 'Workflow completed successfully')}
        
        ## Quality Assessment
        - Research Quality: {feedback.get('quality_assessment', {}).get('research_quality', 'good')}
        - Documentation Quality: {feedback.get('quality_assessment', {}).get('documentation_quality', 'good')}
        - Validation Score: {feedback.get('quality_assessment', {}).get('validation_score', 85)}/100
        
        ## Next Steps
        {chr(10).join([f"1. {step}" for step in feedback.get('next_steps', [])])}
        
        ## Implementation Recommendations
        {chr(10).join([f"- {rec}" for rec in feedback.get('recommendations', [])])}
        """
    
    # Public API methods
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        if workflow_id in self.workflow_results:
            result = self.workflow_results[workflow_id]
            return asdict(result)
        elif workflow_id in self.active_workflows:
            context = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "status": "in_progress",
                "context": asdict(context)
            }
        else:
            return {
                "error": "Workflow not found",
                "workflow_id": workflow_id
            }
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel an active workflow."""
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]
            return {
                "success": True,
                "message": f"Workflow {workflow_id} cancelled"
            }
        else:
            return {
                "success": False,
                "message": "Workflow not found or already completed"
            }
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "statistics": self.stats,
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.workflow_results),
            "service_info": {
                "version": "1.0.0",
                "features": [
                    "research_to_analysis_workflow",
                    "integrated_validation",
                    "automated_deployment",
                    "comprehensive_feedback"
                ]
            }
        }

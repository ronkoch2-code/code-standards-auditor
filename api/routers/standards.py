"""
Standards API Router

Handles endpoints for standards research, management, and recommendations.

Author: Code Standards Auditor
Date: January 31, 2025
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, Query, Body, BackgroundTasks, Request
from pydantic import BaseModel, Field

from services.standards_research_service import StandardsResearchService
from services.recommendations_service import RecommendationsService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from config.settings import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/standards",
    tags=["standards"],
    responses={404: {"description": "Not found"}}
)


# Dependency injection functions
def get_research_service(request: Request) -> StandardsResearchService:
    """Get or create research service from app state"""
    if not hasattr(request.app.state, 'research_service'):
        request.app.state.research_service = StandardsResearchService()
    return request.app.state.research_service


def get_recommendations_service(request: Request) -> RecommendationsService:
    """Get or create recommendations service from app state"""
    if not hasattr(request.app.state, 'recommendations_service'):
        request.app.state.recommendations_service = RecommendationsService()
    return request.app.state.recommendations_service


def get_neo4j_service(request: Request) -> Optional[Neo4jService]:
    """Get Neo4j service from app state (may be None if not configured)"""
    return getattr(request.app.state, 'neo4j', None)


def get_cache_service(request: Request) -> Optional[CacheService]:
    """Get cache service from app state (may be None if not configured)"""
    return getattr(request.app.state, 'cache', None)


# Pydantic models for request/response
class StandardResearchRequest(BaseModel):
    """Request model for researching a new standard."""
    topic: str = Field(..., description="Topic to research")
    category: str = Field(default="general", description="Category of research")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    examples: Optional[List[str]] = Field(default=None, description="Code examples to analyze")
    auto_approve: bool = Field(default=False, description="Auto-approve the standard")


class StandardResearchResponse(BaseModel):
    """Response model for standard research."""
    id: str
    title: str
    category: str
    version: str
    content: str
    status: str
    created_at: str
    metadata: Dict[str, Any]


class RecommendationsRequest(BaseModel):
    """Request model for code recommendations."""
    code: str = Field(..., description="Code to analyze")
    language: str = Field(..., description="Programming language")
    standards_ids: Optional[List[str]] = Field(default=None, description="Specific standard IDs to check")
    focus_areas: Optional[List[str]] = Field(default=None, description="Areas to focus on")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class RecommendationsResponse(BaseModel):
    """Response model for recommendations."""
    recommendations: List[Dict[str, Any]]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]


class PatternDiscoveryRequest(BaseModel):
    """Request model for pattern discovery."""
    code_samples: List[str] = Field(..., description="Code samples to analyze")
    language: str = Field(default="auto", description="Programming language")
    min_frequency: int = Field(default=2, description="Minimum frequency for pattern")


class QuickFixRequest(BaseModel):
    """Request model for quick fixes."""
    code: str = Field(..., description="Code with issues")
    language: str = Field(..., description="Programming language")
    issue_type: str = Field(..., description="Type of issue to fix")


class RefactoringPlanRequest(BaseModel):
    """Request model for refactoring plan."""
    code: str = Field(..., description="Code to refactor")
    language: str = Field(..., description="Programming language")
    goals: List[str] = Field(..., description="Refactoring goals")


class StandardValidationRequest(BaseModel):
    """Request model for standard validation."""
    content: str = Field(..., description="Standard content to validate")
    category: str = Field(..., description="Category of the standard")


class StandardUpdateRequest(BaseModel):
    """Request model for updating a standard."""
    standard_id: str = Field(..., description="ID of the standard to update")
    content: Optional[str] = Field(default=None, description="New content")
    version: Optional[str] = Field(default=None, description="New version")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Updated metadata")


# Endpoints

@router.post("/research", response_model=StandardResearchResponse)
async def research_standard(
    request: StandardResearchRequest,
    background_tasks: BackgroundTasks,
    research_service: StandardsResearchService = Depends(get_research_service)
):
    """
    Research and generate a new coding standard.

    This endpoint uses AI to research and create comprehensive coding standards
    based on the provided topic and context.
    """
    try:
        logger.info(f"Researching standard for topic: {request.topic}")

        # Perform research
        standard = await research_service.research_standard(
            topic=request.topic,
            category=request.category,
            context=request.context,
            examples=request.examples
        )
        
        # Auto-approve if requested
        if request.auto_approve:
            standard["status"] = "approved"
            standard["metadata"]["approved"] = True
            standard["metadata"]["approved_at"] = datetime.now().isoformat()
        
        # Schedule background task for validation
        background_tasks.add_task(
            validate_standard_background,
            standard["content"],
            standard["category"],
            standard["id"]
        )
        
        return StandardResearchResponse(**standard)
        
    except Exception as e:
        logger.error(f"Error researching standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    request: RecommendationsRequest,
    recommendations_service: RecommendationsService = Depends(get_recommendations_service),
    neo4j_service: Optional[Neo4jService] = Depends(get_neo4j_service)
):
    """
    Generate improvement recommendations for code.

    Analyzes the provided code against standards and generates
    prioritized recommendations for improvements.
    """
    try:
        logger.info(f"Generating recommendations for {request.language} code")

        # Get standards if specific IDs provided
        standards = None
        if request.standards_ids and neo4j_service:
            standards = []
            for std_id in request.standards_ids:
                std = await neo4j_service.get_standard(std_id)
                if std:
                    standards.append(std)

        # Generate recommendations
        result = await recommendations_service.generate_recommendations(
            code=request.code,
            language=request.language,
            standards=standards,
            focus_areas=request.focus_areas,
            context=request.context
        )
        
        return RecommendationsResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discover-patterns")
async def discover_patterns(
    request: PatternDiscoveryRequest,
    research_service: StandardsResearchService = Depends(get_research_service)
):
    """
    Discover patterns from code samples that could become standards.

    Analyzes multiple code samples to identify common patterns,
    anti-patterns, and opportunities for standardization.
    """
    try:
        logger.info(f"Discovering patterns from {len(request.code_samples)} samples")

        patterns = await research_service.discover_patterns(
            code_samples=request.code_samples,
            language=request.language
        )
        
        # Filter by minimum frequency
        filtered = [
            p for p in patterns
            if int(p.get("frequency", 0)) >= request.min_frequency
        ]
        
        return {
            "patterns": filtered,
            "total_discovered": len(patterns),
            "above_threshold": len(filtered),
            "discovery_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error discovering patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-fixes")
async def get_quick_fixes(
    request: QuickFixRequest,
    recommendations_service: RecommendationsService = Depends(get_recommendations_service)
):
    """
    Get quick fixes for common issues in code.

    Provides immediate, actionable fixes that can be applied
    without major refactoring.
    """
    try:
        fixes = await recommendations_service.get_quick_fixes(
            code=request.code,
            language=request.language,
            issue_type=request.issue_type
        )
        
        return {
            "fixes": fixes,
            "total": len(fixes),
            "automated_available": sum(1 for f in fixes if f.get("automated"))
        }
        
    except Exception as e:
        logger.error(f"Error getting quick fixes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refactoring-plan")
async def create_refactoring_plan(
    request: RefactoringPlanRequest,
    recommendations_service: RecommendationsService = Depends(get_recommendations_service)
):
    """
    Generate a comprehensive refactoring plan for code.

    Creates a detailed, phased plan for refactoring code
    to meet specific goals and standards.
    """
    try:
        plan = await recommendations_service.generate_refactoring_plan(
            code=request.code,
            language=request.language,
            goals=request.goals
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Error creating refactoring plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_standard(
    request: StandardValidationRequest,
    research_service: StandardsResearchService = Depends(get_research_service)
):
    """
    Validate a proposed standard for quality and completeness.

    Evaluates the standard against quality criteria and provides
    improvement suggestions.
    """
    try:
        validation = await research_service.validate_standard(
            standard_content=request.content,
            category=request.category
        )
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_standards(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    neo4j_service: Optional[Neo4jService] = Depends(get_neo4j_service)
):
    """
    List available coding standards.

    Returns a paginated list of standards with optional filtering.
    """
    try:
        if not neo4j_service:
            return {
                "standards": [],
                "total": 0,
                "message": "Neo4j not configured"
            }
        
        # Get standards from Neo4j
        if category:
            standards = await neo4j_service.get_standards_by_category(category)
        else:
            # Get all standards (would need to implement this method)
            standards = await neo4j_service.get_all_standards(limit=limit, offset=offset)
        
        # Filter by status if provided
        if status:
            standards = [s for s in standards if s.get("status") == status]
        
        return {
            "standards": standards[offset:offset+limit],
            "total": len(standards),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing standards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{standard_id}")
async def get_standard(
    standard_id: str,
    neo4j_service: Optional[Neo4jService] = Depends(get_neo4j_service)
):
    """
    Get a specific standard by ID.

    Returns the full details of a coding standard.
    """
    try:
        if not neo4j_service:
            raise HTTPException(status_code=503, detail="Neo4j not configured")
        
        standard = await neo4j_service.get_standard(standard_id)
        
        if not standard:
            raise HTTPException(status_code=404, detail="Standard not found")
        
        return standard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{standard_id}")
async def update_standard(
    standard_id: str,
    request: StandardUpdateRequest,
    neo4j_service: Optional[Neo4jService] = Depends(get_neo4j_service),
    cache_service: Optional[CacheService] = Depends(get_cache_service)
):
    """
    Update an existing standard.

    Allows updating content, version, and metadata of a standard.
    """
    try:
        if not neo4j_service:
            raise HTTPException(status_code=503, detail="Neo4j not configured")
        
        # Get existing standard
        existing = await neo4j_service.get_standard(standard_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Standard not found")
        
        # Update fields
        if request.content:
            existing["content"] = request.content
        if request.version:
            existing["version"] = request.version
        if request.metadata:
            existing["metadata"].update(request.metadata)
        
        existing["updated_at"] = datetime.now().isoformat()
        
        # Update in Neo4j
        await neo4j_service.update_standard(standard_id, existing)
        
        # Invalidate cache
        if cache_service:
            await cache_service.invalidate_pattern(f"standard:{standard_id}*")
        
        return {
            "message": "Standard updated successfully",
            "standard": existing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{standard_id}")
async def delete_standard(
    standard_id: str,
    neo4j_service: Optional[Neo4jService] = Depends(get_neo4j_service),
    cache_service: Optional[CacheService] = Depends(get_cache_service)
):
    """
    Delete a standard.

    Marks a standard as deleted (soft delete).
    """
    try:
        if not neo4j_service:
            raise HTTPException(status_code=503, detail="Neo4j not configured")
        
        # Soft delete by updating status
        await neo4j_service.update_standard(
            standard_id,
            {"status": "deleted", "deleted_at": datetime.now().isoformat()}
        )
        
        # Invalidate cache
        if cache_service:
            await cache_service.invalidate_pattern(f"standard:{standard_id}*")
        
        return {"message": "Standard deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/query")
async def query_standards_for_agent(
    query: str = Query(..., description="Query string"),
    language: Optional[str] = Query(None, description="Programming language"),
    category: Optional[str] = Query(None, description="Category filter"),
    limit: int = Query(10, description="Maximum results"),
    neo4j_service: Optional[Neo4jService] = Depends(get_neo4j_service),
    cache_service: Optional[CacheService] = Depends(get_cache_service)
):
    """
    Query standards for AI agent consumption.

    Provides a simplified interface for AI agents to query
    and retrieve relevant standards.
    """
    try:
        # Use cache if available
        cache_key = f"agent_query:{query}:{language}:{category}"
        if cache_service:
            cached = await cache_service.get(cache_key)
            if cached:
                return cached
        
        # Search standards (would need to implement search in Neo4j service)
        results = []
        
        if neo4j_service:
            # Simple implementation - would be enhanced with actual search
            all_standards = await neo4j_service.get_standards_by_category(
                category or "general"
            )
            
            # Filter by query (simple text match - would use better search)
            for std in all_standards:
                if query.lower() in std.get("title", "").lower() or \
                   query.lower() in std.get("content", "").lower():
                    results.append({
                        "id": std.get("id"),
                        "title": std.get("title"),
                        "relevance": 0.8,  # Would calculate actual relevance
                        "summary": std.get("content", "")[:500],
                        "category": std.get("category"),
                        "version": std.get("version")
                    })
            
            results = results[:limit]
        
        response = {
            "query": query,
            "results": results,
            "total": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache the response
        if cache_service:
            await cache_service.set(cache_key, response, ttl=3600)
        
        return response
        
    except Exception as e:
        logger.error(f"Error querying standards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background tasks
async def validate_standard_background(content: str, category: str, standard_id: str):
    """Background task to validate a standard after creation."""
    try:
        # Get services from factory for background task
        from utils.service_factory import get_research_service, get_neo4j_service

        research_svc = get_research_service()
        neo4j_svc = get_neo4j_service()

        validation = await research_svc.validate_standard(content, category)

        # Store validation results
        if neo4j_svc:
            await neo4j_svc.update_standard(
                standard_id,
                {"validation": validation, "validated_at": datetime.now().isoformat()}
            )

        logger.info(f"Standard {standard_id} validated with score: {validation.get('score')}")

    except Exception as e:
        logger.error(f"Error validating standard {standard_id}: {e}")


# Health check
@router.get("/health")
async def health_check():
    """Check health of standards service."""
    return {
        "status": "healthy",
        "services": {
            "research": "active",
            "recommendations": "active",
            "neo4j": "active" if neo4j_service else "disabled",
            "cache": "active" if cache_service else "disabled"
        },
        "timestamp": datetime.now().isoformat()
    }

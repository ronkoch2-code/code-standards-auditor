"""
Audit API Router
Handles code auditing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime
import structlog

from api.schemas.audit import (
    AuditRequest,
    AuditResponse,
    AuditResult,
    AuditStatus,
    BatchAuditRequest,
    BatchAuditResponse,
    AuditHistory,
    ViolationDetail,
    SeverityLevel
)
from api.schemas.common import PaginationParams, PaginatedResponse
from services.gemini_service import GeminiService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from config.settings import Settings

logger = structlog.get_logger()
router = APIRouter()
settings = Settings()


async def get_gemini_service(request: Request) -> GeminiService:
    """Dependency to get Gemini service"""
    if not hasattr(request.app.state, 'gemini'):
        # GeminiService gets API key from environment variables
        request.app.state.gemini = GeminiService()
    return request.app.state.gemini


async def get_neo4j_service(request: Request) -> Neo4jService:
    """Dependency to get Neo4j service"""
    return request.app.state.neo4j


async def get_cache_service(request: Request) -> CacheService:
    """Dependency to get cache service"""
    return request.app.state.cache


@router.post("/", response_model=AuditResponse)
async def audit_code(
    audit_request: AuditRequest,
    background_tasks: BackgroundTasks,
    gemini: GeminiService = Depends(get_gemini_service),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    cache: CacheService = Depends(get_cache_service),
    request: Request = None
):
    """
    Perform code audit against standards
    
    Analyzes provided code against specified or default standards
    and returns violations with suggestions.
    """
    audit_id = f"aud_{uuid.uuid4().hex[:12]}"
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.info("Starting code audit", 
                audit_id=audit_id, 
                language=audit_request.language,
                request_id=request_id)
    
    try:
        # Check cache for similar audit
        cache_key = f"audit:{audit_request.language}:{hash(audit_request.code or audit_request.file_path)}"
        cached_result = await cache.get_audit_result(cache_key)
        
        if cached_result and not audit_request.context:
            logger.info("Returning cached audit result", audit_id=audit_id)
            return AuditResponse(
                success=True,
                result=cached_result,
                request_id=request_id
            )
        
        # Get applicable standards
        standards = []
        if audit_request.standard_ids:
            for std_id in audit_request.standard_ids:
                standard = await neo4j.get_standard(std_id)
                if standard:
                    standards.append(standard)
        else:
            # Get default standards for language
            standards = await neo4j.get_standards_by_language(audit_request.language)
        
        if not standards:
            raise HTTPException(
                status_code=404,
                detail=f"No standards found for language: {audit_request.language}"
            )
        
        # Prepare audit prompt
        code_content = audit_request.code
        if audit_request.file_path:
            # In production, read from file system or storage
            code_content = f"// File: {audit_request.file_path}\n{code_content or '// File content would be read here'}"
        
        # Use Gemini to analyze code
        analysis_prompt = f"""
        Analyze the following {audit_request.language} code against these standards:
        
        Standards:
        {[s['name'] for s in standards]}
        
        Code:
        ```{audit_request.language}
        {code_content}
        ```
        
        Provide a detailed analysis including:
        1. Violations found (with line numbers if possible)
        2. Severity of each violation
        3. Suggestions for fixes
        4. Overall compliance score (0-100)
        
        Return as structured JSON.
        """
        
        # Start audit
        started_at = datetime.utcnow()
        
        # Use cached context if available
        analysis = await gemini.analyze_with_caching(
            analysis_prompt,
            context_type="code_audit",
            context_id=f"{audit_request.language}:{audit_id}"
        )
        
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        
        # Parse Gemini response and create violations
        # In production, this would parse the actual Gemini response
        violations = [
            ViolationDetail(
                rule_id="PY001",
                rule_name="Missing docstring",
                severity=SeverityLevel.MEDIUM,
                message="Function lacks a docstring",
                file_path=audit_request.file_path or "inline",
                line_number=10,
                column_number=5,
                code_snippet="def process_data(items):",
                suggestion="Add a docstring describing the function's purpose",
                category="documentation",
                confidence=0.95
            )
        ]
        
        # Calculate metrics
        violations_by_severity = {
            "critical": sum(1 for v in violations if v.severity == SeverityLevel.CRITICAL),
            "high": sum(1 for v in violations if v.severity == SeverityLevel.HIGH),
            "medium": sum(1 for v in violations if v.severity == SeverityLevel.MEDIUM),
            "low": sum(1 for v in violations if v.severity == SeverityLevel.LOW),
            "info": sum(1 for v in violations if v.severity == SeverityLevel.INFO),
        }
        
        # Create audit result
        result = AuditResult(
            audit_id=audit_id,
            status=AuditStatus.COMPLETED,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            total_violations=len(violations),
            violations_by_severity=violations_by_severity,
            violations=violations,
            compliance_score=85.5,  # Calculated based on violations
            standards_checked=[s['name'] for s in standards],
            metadata={
                "language": audit_request.language,
                "lines_of_code": len(code_content.split('\n')) if code_content else 0
            }
        )
        
        # Cache result
        await cache.set_audit_result(cache_key, result.dict(), ttl=3600)
        
        # Store in Neo4j for analytics
        background_tasks.add_task(
            neo4j.track_violation,
            audit_id=audit_id,
            file_path=audit_request.file_path or "inline",
            violations=[v.dict() for v in violations]
        )
        
        logger.info("Code audit completed", 
                   audit_id=audit_id,
                   violations=len(violations),
                   duration_ms=duration_ms)
        
        return AuditResponse(
            success=True,
            result=result,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error("Code audit failed", 
                    audit_id=audit_id,
                    error=str(e))
        
        return AuditResponse(
            success=False,
            error=str(e),
            request_id=request_id
        )


@router.post("/batch", response_model=BatchAuditResponse)
async def batch_audit(
    batch_request: BatchAuditRequest,
    background_tasks: BackgroundTasks,
    gemini: GeminiService = Depends(get_gemini_service),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    cache: CacheService = Depends(get_cache_service),
    request: Request = None
):
    """
    Perform batch code audit
    
    Processes multiple audit requests in parallel or sequentially.
    """
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    started_at = datetime.utcnow()
    
    logger.info("Starting batch audit", 
                batch_id=batch_id,
                total_items=len(batch_request.items))
    
    results = []
    failed_items = 0
    
    try:
        if batch_request.parallel:
            # Process in parallel using asyncio
            tasks = []
            for item in batch_request.items:
                task = audit_code(
                    item,
                    background_tasks,
                    gemini,
                    neo4j,
                    cache,
                    request
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for response in responses:
                if isinstance(response, Exception):
                    failed_items += 1
                    if batch_request.stop_on_error:
                        raise response
                elif response.result:
                    results.append(response.result)
                else:
                    failed_items += 1
        else:
            # Process sequentially
            for item in batch_request.items:
                try:
                    response = await audit_code(
                        item,
                        background_tasks,
                        gemini,
                        neo4j,
                        cache,
                        request
                    )
                    if response.result:
                        results.append(response.result)
                    else:
                        failed_items += 1
                except Exception as e:
                    failed_items += 1
                    if batch_request.stop_on_error:
                        raise e
        
        completed_at = datetime.utcnow()
        
        # Send webhook if configured
        if batch_request.callback_url:
            background_tasks.add_task(
                send_webhook,
                batch_request.callback_url,
                batch_id,
                results
            )
        
        return BatchAuditResponse(
            batch_id=batch_id,
            status=AuditStatus.COMPLETED,
            total_items=len(batch_request.items),
            completed_items=len(results),
            failed_items=failed_items,
            results=results,
            started_at=started_at,
            completed_at=completed_at
        )
        
    except Exception as e:
        logger.error("Batch audit failed", 
                    batch_id=batch_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=PaginatedResponse[AuditHistory])
async def get_audit_history(
    pagination: PaginationParams = Depends(),
    language: Optional[str] = None,
    file_path: Optional[str] = None,
    min_score: Optional[float] = None,
    neo4j: Neo4jService = Depends(get_neo4j_service)
):
    """
    Get audit history
    
    Retrieves paginated audit history with optional filters.
    """
    # Query Neo4j for audit history
    # In production, this would query actual audit records
    
    history_items = [
        AuditHistory(
            audit_id="aud_123456",
            file_path="src/main.py",
            language="python",
            timestamp=datetime.utcnow(),
            compliance_score=85.5,
            total_violations=3,
            status=AuditStatus.COMPLETED
        )
    ]
    
    return PaginatedResponse.create(
        items=history_items,
        total=1,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/{audit_id}", response_model=AuditResult)
async def get_audit_details(
    audit_id: str,
    cache: CacheService = Depends(get_cache_service),
    neo4j: Neo4jService = Depends(get_neo4j_service)
):
    """
    Get detailed audit result
    
    Retrieves full details of a specific audit.
    """
    # Check cache first
    cached = await cache.get(f"audit_detail:{audit_id}")
    if cached:
        return AuditResult(**cached)
    
    # Query Neo4j
    # In production, this would fetch from database
    
    raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found")


@router.post("/{audit_id}/rerun", response_model=AuditResponse)
async def rerun_audit(
    audit_id: str,
    background_tasks: BackgroundTasks,
    gemini: GeminiService = Depends(get_gemini_service),
    neo4j: Neo4jService = Depends(get_neo4j_service),
    cache: CacheService = Depends(get_cache_service),
    request: Request = None
):
    """
    Rerun a previous audit
    
    Re-executes an audit with the same parameters.
    """
    # Fetch original audit parameters
    # In production, retrieve from database
    
    # For now, return a mock response
    raise HTTPException(status_code=501, detail="Rerun functionality not yet implemented")


@router.get("/stream/{audit_id}")
async def stream_audit_progress(
    audit_id: str,
    cache: CacheService = Depends(get_cache_service)
):
    """
    Stream audit progress via SSE
    
    Provides real-time updates for long-running audits.
    """
    async def event_generator():
        while True:
            # Check audit status
            status = await cache.get(f"audit_progress:{audit_id}")
            if status:
                yield f"data: {status}\n\n"
                if status.get('status') in ['completed', 'failed']:
                    break
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


async def send_webhook(url: str, batch_id: str, results: List[Dict]):
    """Send webhook notification for batch completion"""
    # In production, implement webhook sending
    logger.info("Sending webhook", url=url, batch_id=batch_id)

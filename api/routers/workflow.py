"""
Integrated Workflow API Router

Provides endpoints for managing integrated standards research and analysis workflows.

Author: Code Standards Auditor
Date: September 01, 2025
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json

from fastapi import APIRouter, HTTPException, Depends, Body, BackgroundTasks, Query, Request
from pydantic import BaseModel, Field

from services.integrated_workflow_service import IntegratedWorkflowService, WorkflowStatus
from config.settings import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["integrated-workflow"],
    responses={404: {"description": "Not found"}}
)


# Dependency injection function
def get_workflow_service(request: Request) -> IntegratedWorkflowService:
    """Get or create workflow service from app state"""
    if not hasattr(request.app.state, 'workflow_service'):
        request.app.state.workflow_service = IntegratedWorkflowService()
    return request.app.state.workflow_service


# Pydantic models
class WorkflowStartRequest(BaseModel):
    """Request to start a new integrated workflow."""
    research_request: str = Field(..., description="Natural language research request")
    code_samples: Optional[List[str]] = Field(default=None, description="Code samples to analyze")
    project_context: Optional[Dict[str, Any]] = Field(default=None, description="Project context")
    user_preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences")


class WorkflowStatusResponse(BaseModel):
    """Response containing workflow status."""
    workflow_id: str
    status: str
    phase: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


# Endpoints

@router.post("/start", response_model=Dict[str, str])
async def start_workflow(
    request: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    workflow_service: IntegratedWorkflowService = Depends(get_workflow_service)
):
    """
    Start a new integrated workflow from research request to code analysis.

    This endpoint initiates a complete workflow that:
    1. Researches and creates coding standards based on the request
    2. Generates comprehensive documentation
    3. Validates the standard quality
    4. Deploys to configured systems
    5. Analyzes provided code samples (if any)
    6. Provides feedback and recommendations
    """
    try:
        logger.info(f"Starting integrated workflow: {request.research_request[:100]}...")

        workflow_id = await workflow_service.start_research_to_analysis_workflow(
            research_request=request.research_request,
            code_samples=request.code_samples,
            project_context=request.project_context,
            user_preferences=request.user_preferences
        )

        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Integrated workflow started successfully",
            "estimated_completion": "5-15 minutes depending on complexity"
        }

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    workflow_service: IntegratedWorkflowService = Depends(get_workflow_service)
):
    """
    Get the current status of a workflow.

    Returns detailed information about the workflow progress,
    current phase, and any available results.
    """
    try:
        status = await workflow_service.get_workflow_status(workflow_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return WorkflowStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    workflow_service: IntegratedWorkflowService = Depends(get_workflow_service)
):
    """
    Cancel an active workflow.

    Stops the workflow execution if it's still in progress.
    Completed workflows cannot be cancelled.
    """
    try:
        result = await workflow_service.cancel_workflow(workflow_id)

        if not result.get("success", False):
            raise HTTPException(status_code=404, detail=result.get("message", "Workflow not found"))

        return {
            "success": True,
            "message": result["message"],
            "workflow_id": workflow_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/results")
async def get_workflow_results(
    workflow_id: str,
    workflow_service: IntegratedWorkflowService = Depends(get_workflow_service)
):
    """
    Get the complete results of a completed workflow.

    Returns all outputs from the workflow including:
    - Generated standards
    - Documentation packages
    - Validation results
    - Deployment information
    - Code analysis results (if applicable)
    - Feedback and recommendations
    """
    try:
        status = await workflow_service.get_workflow_status(workflow_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        if status.get("status") != WorkflowStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow is not completed. Current status: {status.get('status')}"
            )

        return {
            "workflow_id": workflow_id,
            "results": status.get("results", {}),
            "execution_summary": {
                "execution_time": status.get("execution_time"),
                "completed_at": status.get("completed_at"),
                "phases_completed": len(status.get("results", {}))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/report")
async def get_workflow_report(
    workflow_id: str,
    workflow_service: IntegratedWorkflowService = Depends(get_workflow_service),
    format: str = Query(default="json", description="Report format: json, markdown, pdf")
):
    """
    Get a formatted report of the workflow execution and results.

    Available formats:
    - json: Structured JSON report
    - markdown: Human-readable markdown report
    - pdf: PDF report (if enabled)
    """
    try:
        status = await workflow_service.get_workflow_status(workflow_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        if status.get("status") != WorkflowStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot generate report for incomplete workflow. Status: {status.get('status')}"
            )

        # Generate report based on format
        if format.lower() == "json":
            return await _generate_json_report(workflow_id, status)
        elif format.lower() == "markdown":
            report_content = await _generate_markdown_report(workflow_id, status)
            return {"format": "markdown", "content": report_content}
        elif format.lower() == "pdf":
            # PDF generation would be implemented here
            raise HTTPException(status_code=501, detail="PDF reports not yet implemented")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate workflow report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def list_active_workflows(
    limit: int = Query(default=20, description="Maximum number of workflows to return")
):
    """
    List currently active workflows.
    
    Returns a list of workflows that are currently in progress.
    """
    try:
        # This would be implemented by adding a method to the workflow service
        # For now, return a placeholder
        return {
            "active_workflows": [],
            "count": 0,
            "message": "Active workflows listing not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to list active workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_workflow_statistics(
    workflow_service: IntegratedWorkflowService = Depends(get_workflow_service)
):
    """
    Get workflow execution statistics.

    Returns aggregate statistics about workflow usage and performance.
    """
    try:
        stats = workflow_service.get_service_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get workflow statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

async def _generate_json_report(workflow_id: str, status: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a structured JSON report."""
    results = status.get("results", {})
    
    return {
        "workflow_report": {
            "workflow_id": workflow_id,
            "generated_at": datetime.now().isoformat(),
            "execution_summary": {
                "status": status.get("status"),
                "execution_time": status.get("execution_time"),
                "completed_at": status.get("completed_at"),
                "phases_completed": list(results.keys())
            },
            "research_results": {
                "standard_created": bool(results.get("research", {}).get("standard")),
                "quality_score": results.get("validation", {}).get("overall_score", 0),
                "validation_passed": results.get("validation", {}).get("validation_passed", False)
            },
            "deployment_results": {
                "deployment_locations": len(results.get("deployment", {}).get("deployment_results", {})),
                "deployment_success": results.get("deployment", {}).get("success", False)
            },
            "analysis_results": {
                "code_samples_analyzed": results.get("analysis", {}).get("total_samples", 0),
                "overall_compliance": results.get("analysis", {}).get("overall_compliance", 0),
                "recommendations_generated": results.get("analysis", {}).get("aggregate_analysis", {}).get("total_recommendations", 0)
            },
            "actionable_outcomes": results.get("feedback", {}).get("feedback", {}).get("next_steps", [])
        }
    }


async def _generate_markdown_report(workflow_id: str, status: Dict[str, Any]) -> str:
    """Generate a markdown report."""
    results = status.get("results", {})
    
    report = f"""# Workflow Execution Report

**Workflow ID:** {workflow_id}  
**Generated:** {datetime.now().isoformat()}  
**Status:** {status.get('status', 'Unknown')}  
**Execution Time:** {status.get('execution_time', 0):.2f} seconds  

## Executive Summary

This workflow successfully completed the integrated standards research and analysis process.

### Research Results
- **Standard Created:** {'✅' if results.get('research', {}).get('standard') else '❌'}
- **Quality Score:** {results.get('validation', {}).get('overall_score', 0)}/100
- **Validation Status:** {'✅ Passed' if results.get('validation', {}).get('validation_passed') else '❌ Failed'}

### Deployment Results  
- **Deployment Locations:** {len(results.get('deployment', {}).get('deployment_results', {}))}
- **Deployment Success:** {'✅' if results.get('deployment', {}).get('success') else '❌'}

### Analysis Results
- **Code Samples Analyzed:** {results.get('analysis', {}).get('total_samples', 0)}
- **Overall Compliance:** {results.get('analysis', {}).get('overall_compliance', 0):.1f}%
- **Recommendations Generated:** {results.get('analysis', {}).get('aggregate_analysis', {}).get('total_recommendations', 0)}

## Next Steps

{chr(10).join(['- ' + step for step in results.get('feedback', {}).get('feedback', {}).get('next_steps', [])])}

## Detailed Results

### Research Phase
{json.dumps(results.get('research', {}), indent=2) if results.get('research') else 'No research results available'}

### Validation Phase  
{json.dumps(results.get('validation', {}), indent=2) if results.get('validation') else 'No validation results available'}

### Analysis Phase
{json.dumps(results.get('analysis', {}), indent=2) if results.get('analysis') else 'No analysis results available'}

---
*Generated by Code Standards Auditor v2.0*
"""
    
    return report


@router.get("/health")
async def workflow_health_check(
    workflow_service: IntegratedWorkflowService = Depends(get_workflow_service)
):
    """Health check for workflow service."""
    stats = workflow_service.get_service_statistics()

    return {
        "status": "healthy",
        "service": "integrated_workflow",
        "version": "1.0.0",
        "statistics": stats.get("statistics", {}),
        "active_workflows": stats.get("active_workflows", 0),
        "timestamp": datetime.now().isoformat()
    }

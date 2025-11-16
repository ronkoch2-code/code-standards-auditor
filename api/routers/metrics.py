"""
Metrics API Router

Provides endpoints for monitoring auto-refresh and other system metrics.

Author: Code Standards Auditor
Date: November 16, 2025
Version: 1.0.0 (v4.2.2)
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field

from services.standards_access_service import StandardsAccessService
from config.settings import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/metrics",
    tags=["metrics"],
    responses={404: {"description": "Not found"}}
)


# Dependency injection
def get_access_service(request: Request) -> StandardsAccessService:
    """Get or create standards access service from app state"""
    if not hasattr(request.app.state, 'access_service'):
        request.app.state.access_service = StandardsAccessService()
    return request.app.state.access_service


# Response models
class AutoRefreshMetricsResponse(BaseModel):
    """Response model for auto-refresh metrics"""
    enabled: bool = Field(..., description="Whether auto-refresh is enabled")
    mode: str = Field(..., description="Refresh mode (blocking/background)")
    freshness_threshold_days: int = Field(..., description="Freshness threshold in days")
    total_accesses: int = Field(..., description="Total standard accesses")
    stale_standards_detected: int = Field(..., description="Number of stale standards detected")
    refresh_attempts: int = Field(..., description="Total refresh attempts")
    refresh_successes: int = Field(..., description="Successful refreshes")
    refresh_failures: int = Field(..., description="Failed refreshes")
    avg_refresh_duration_seconds: float = Field(..., description="Average refresh duration")
    success_rate: float = Field(..., description="Refresh success rate percentage")
    background_queue: Optional[Dict[str, Any]] = Field(None, description="Background queue status")

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "mode": "background",
                "freshness_threshold_days": 30,
                "total_accesses": 1250,
                "stale_standards_detected": 42,
                "refresh_attempts": 42,
                "refresh_successes": 40,
                "refresh_failures": 2,
                "avg_refresh_duration_seconds": 28.5,
                "success_rate": 95.2,
                "background_queue": {
                    "queue_size": 2,
                    "active_workers": 3,
                    "active_refreshes": 1,
                    "refreshing_standards": ["python/security_standards_v1.0.0.md"]
                }
            }
        }


class StandardRefreshStatusResponse(BaseModel):
    """Response model for individual standard refresh status"""
    standard_id: str = Field(..., description="Standard identifier")
    last_accessed: Optional[str] = Field(None, description="Last access timestamp")
    access_count: int = Field(..., description="Total access count")
    auto_update_enabled: bool = Field(..., description="Whether auto-update is enabled")
    freshness_threshold_days: int = Field(..., description="Freshness threshold for this standard")
    last_auto_update_attempt: Optional[str] = Field(None, description="Last update attempt timestamp")
    last_auto_update_success: Optional[str] = Field(None, description="Last successful update timestamp")
    auto_update_failures: int = Field(..., description="Number of consecutive failures")
    needs_refresh: bool = Field(..., description="Whether standard currently needs refresh")

    class Config:
        json_schema_extra = {
            "example": {
                "standard_id": "python/coding_standards_v1.0.0.md",
                "last_accessed": "2025-11-16T10:30:00Z",
                "access_count": 127,
                "auto_update_enabled": True,
                "freshness_threshold_days": 30,
                "last_auto_update_attempt": "2025-11-15T09:00:00Z",
                "last_auto_update_success": "2025-11-15T09:02:00Z",
                "auto_update_failures": 0,
                "needs_refresh": False
            }
        }


class UpdateStandardSettingsRequest(BaseModel):
    """Request model for updating standard auto-refresh settings"""
    auto_update_enabled: Optional[bool] = Field(None, description="Enable/disable auto-update")
    freshness_threshold_days: Optional[int] = Field(None, ge=1, le=365, description="Custom freshness threshold")

    class Config:
        json_schema_extra = {
            "example": {
                "auto_update_enabled": False,
                "freshness_threshold_days": 60
            }
        }


# Endpoints
@router.get(
    "/auto-refresh",
    response_model=AutoRefreshMetricsResponse,
    summary="Get auto-refresh metrics",
    description="Retrieve comprehensive metrics about the auto-refresh system"
)
async def get_auto_refresh_metrics(
    access_service: StandardsAccessService = Depends(get_access_service)
) -> AutoRefreshMetricsResponse:
    """
    Get auto-refresh metrics including access counts, refresh statistics, and queue status.

    Returns:
        AutoRefreshMetricsResponse: Comprehensive auto-refresh metrics
    """
    try:
        metrics = access_service.get_metrics()

        return AutoRefreshMetricsResponse(
            enabled=settings.ENABLE_AUTO_REFRESH_ON_ACCESS,
            mode=settings.AUTO_REFRESH_MODE,
            freshness_threshold_days=settings.STANDARD_FRESHNESS_THRESHOLD_DAYS,
            **metrics
        )

    except Exception as e:
        logger.error(f"Failed to get auto-refresh metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.get(
    "/standards/{standard_id}/refresh-status",
    response_model=StandardRefreshStatusResponse,
    summary="Get refresh status for a standard",
    description="Get detailed refresh status and metadata for a specific standard"
)
async def get_standard_refresh_status(
    standard_id: str,
    access_service: StandardsAccessService = Depends(get_access_service)
) -> StandardRefreshStatusResponse:
    """
    Get refresh status for a specific standard.

    Args:
        standard_id: Standard identifier (e.g., "python/coding_standards_v1.0.0.md")

    Returns:
        StandardRefreshStatusResponse: Detailed refresh status

    Raises:
        HTTPException: If standard not found
    """
    try:
        # Get metadata
        metadata = access_service.get_standard_metadata(standard_id)

        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Standard not found: {standard_id}"
            )

        # Check if needs refresh
        from services.standards_access_service import StandardMetadata
        metadata_obj = StandardMetadata.from_dict(metadata)
        needs_refresh = await access_service._needs_refresh(metadata_obj)

        return StandardRefreshStatusResponse(
            standard_id=standard_id,
            needs_refresh=needs_refresh,
            **metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get refresh status for {standard_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve refresh status: {str(e)}"
        )


@router.patch(
    "/standards/{standard_id}/auto-refresh-settings",
    response_model=Dict[str, Any],
    summary="Update auto-refresh settings for a standard",
    description="Update auto-refresh configuration for a specific standard"
)
async def update_standard_refresh_settings(
    standard_id: str,
    settings_update: UpdateStandardSettingsRequest,
    access_service: StandardsAccessService = Depends(get_access_service)
) -> Dict[str, Any]:
    """
    Update auto-refresh settings for a specific standard.

    Args:
        standard_id: Standard identifier
        settings_update: New settings to apply

    Returns:
        Updated metadata

    Raises:
        HTTPException: If standard not found or update fails
    """
    try:
        updated = access_service.update_standard_settings(
            standard_id,
            auto_update_enabled=settings_update.auto_update_enabled,
            freshness_threshold_days=settings_update.freshness_threshold_days
        )

        logger.info(f"Updated auto-refresh settings for {standard_id}")

        return {
            "standard_id": standard_id,
            "updated_at": datetime.now().isoformat(),
            "settings": updated
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update settings for {standard_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        )


@router.post(
    "/standards/{standard_id}/refresh",
    response_model=Dict[str, Any],
    summary="Manually trigger standard refresh",
    description="Force refresh of a standard regardless of age"
)
async def trigger_manual_refresh(
    standard_id: str,
    access_service: StandardsAccessService = Depends(get_access_service)
) -> Dict[str, Any]:
    """
    Manually trigger a refresh for a specific standard.

    This endpoint forces a refresh regardless of the standard's age
    or auto-refresh settings.

    Args:
        standard_id: Standard identifier

    Returns:
        Refresh result information

    Raises:
        HTTPException: If standard not found or refresh fails
    """
    try:
        logger.info(f"Manual refresh triggered for {standard_id}")

        # Get standard with force_refresh=True
        result = await access_service.get_standard(
            standard_id,
            force_refresh=True
        )

        return {
            "standard_id": standard_id,
            "refresh_triggered_at": datetime.now().isoformat(),
            "was_refreshed": result["was_refreshed"],
            "metadata": result["metadata"]
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Manual refresh failed for {standard_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Refresh failed: {str(e)}"
        )


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Health check for metrics system",
    description="Check health of auto-refresh and metrics systems"
)
async def metrics_health_check(
    access_service: StandardsAccessService = Depends(get_access_service)
) -> Dict[str, Any]:
    """
    Health check for metrics and auto-refresh systems.

    Returns:
        Health status information
    """
    try:
        metrics = access_service.get_metrics()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "auto_refresh": {
                "enabled": settings.ENABLE_AUTO_REFRESH_ON_ACCESS,
                "mode": settings.AUTO_REFRESH_MODE,
                "operational": True
            },
            "metrics": {
                "total_accesses": metrics.get("total_accesses", 0),
                "success_rate": metrics.get("success_rate", 0.0)
            }
        }

        # Check if background queue is operational
        if settings.AUTO_REFRESH_MODE == "background":
            background_queue = metrics.get("background_queue", {})
            active_workers = background_queue.get("active_workers", 0)

            if active_workers < settings.AUTO_REFRESH_MAX_CONCURRENT:
                health_status["status"] = "degraded"
                health_status["warnings"] = [
                    f"Background queue has {active_workers} workers "
                    f"(expected {settings.AUTO_REFRESH_MAX_CONCURRENT})"
                ]

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

"""
Common Pydantic schemas used across the API
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List, Generic, TypeVar
from datetime import datetime


T = TypeVar('T')


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input parameters",
                "details": {
                    "field": "language",
                    "error": "Must be one of: python, java, javascript"
                },
                "request_id": "req_123456",
                "timestamp": "2025-01-27T10:00:00Z"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"processed_items": 10},
                "timestamp": "2025-01-27T10:00:00Z"
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_previous: bool = Field(..., description="Whether there's a previous page")
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        """Create a paginated response"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: float = Field(..., description="Unix timestamp")
    services: Dict[str, str] = Field(..., description="Service health statuses")
    uptime: Optional[float] = Field(None, description="Uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": 1706352000.0,
                "services": {
                    "neo4j": "connected",
                    "redis": "connected",
                    "gemini": "available"
                },
                "uptime": 3600.0
            }
        }


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    limit: int = Field(..., description="Request limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_at: datetime = Field(..., description="Reset timestamp")
    retry_after: Optional[int] = Field(None, description="Seconds until retry allowed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "limit": 100,
                "remaining": 95,
                "reset_at": "2025-01-27T11:00:00Z",
                "retry_after": None
            }
        }

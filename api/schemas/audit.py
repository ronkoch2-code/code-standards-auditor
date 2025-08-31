"""
Audit-related Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AuditStatus(str, Enum):
    """Audit status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SeverityLevel(str, Enum):
    """Violation severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ViolationDetail(BaseModel):
    """Details of a code standard violation"""
    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: SeverityLevel = Field(..., description="Violation severity")
    message: str = Field(..., description="Violation description")
    file_path: str = Field(..., description="File where violation occurred")
    line_number: Optional[int] = Field(None, description="Line number of violation")
    column_number: Optional[int] = Field(None, description="Column number of violation")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    suggestion: Optional[str] = Field(None, description="Fix suggestion")
    category: str = Field(..., description="Violation category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "PY001",
                "rule_name": "Missing docstring",
                "severity": "medium",
                "message": "Function lacks a docstring",
                "file_path": "src/main.py",
                "line_number": 42,
                "column_number": 5,
                "code_snippet": "def process_data(items):",
                "suggestion": "Add a docstring describing the function's purpose",
                "category": "documentation",
                "confidence": 0.95
            }
        }


class AuditRequest(BaseModel):
    """Request model for code audit"""
    code: Optional[str] = Field(None, description="Code content to audit")
    file_path: Optional[str] = Field(None, description="Path to file to audit")
    file_urls: Optional[List[str]] = Field(None, description="URLs of files to audit")
    language: str = Field(..., description="Programming language")
    standard_ids: Optional[List[str]] = Field(None, description="Specific standards to check against")
    include_suggestions: bool = Field(True, description="Include fix suggestions")
    max_violations: Optional[int] = Field(None, ge=1, description="Maximum violations to return")
    severity_threshold: Optional[SeverityLevel] = Field(None, description="Minimum severity to report")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for audit")
    
    @validator('language')
    def validate_language(cls, v):
        """Validate supported languages"""
        supported = ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'cpp', 'csharp']
        if v.lower() not in supported:
            raise ValueError(f"Language must be one of: {', '.join(supported)}")
        return v.lower()
    
    @validator('file_urls')
    def validate_urls(cls, v):
        """Validate file URLs"""
        if v:
            for url in v:
                if not url.startswith(('http://', 'https://')):
                    raise ValueError(f"Invalid URL: {url}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "def process(data):\n    return data * 2",
                "language": "python",
                "include_suggestions": True,
                "severity_threshold": "medium"
            }
        }


class AuditResult(BaseModel):
    """Result of a code audit"""
    audit_id: str = Field(..., description="Unique audit identifier")
    status: AuditStatus = Field(..., description="Audit status")
    started_at: datetime = Field(..., description="Audit start time")
    completed_at: Optional[datetime] = Field(None, description="Audit completion time")
    duration_ms: Optional[int] = Field(None, description="Audit duration in milliseconds")
    total_violations: int = Field(..., description="Total number of violations found")
    violations_by_severity: Dict[str, int] = Field(..., description="Violation count by severity")
    violations: List[ViolationDetail] = Field(..., description="List of violations")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Overall compliance score")
    standards_checked: List[str] = Field(..., description="Standards that were checked")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audit_id": "aud_123456",
                "status": "completed",
                "started_at": "2025-01-27T10:00:00Z",
                "completed_at": "2025-01-27T10:00:05Z",
                "duration_ms": 5000,
                "total_violations": 3,
                "violations_by_severity": {
                    "critical": 0,
                    "high": 1,
                    "medium": 2,
                    "low": 0,
                    "info": 0
                },
                "violations": [],
                "compliance_score": 85.5,
                "standards_checked": ["PEP8", "Security Best Practices"]
            }
        }


class AuditResponse(BaseModel):
    """Response model for audit endpoint"""
    success: bool = Field(..., description="Request success status")
    result: Optional[AuditResult] = Field(None, description="Audit result")
    error: Optional[str] = Field(None, description="Error message if failed")
    request_id: str = Field(..., description="Request tracking ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result": {},
                "error": None,
                "request_id": "req_123456"
            }
        }


class BatchAuditRequest(BaseModel):
    """Request model for batch audit"""
    items: List[AuditRequest] = Field(..., min_length=1, max_length=100, description="Audit requests")
    parallel: bool = Field(True, description="Process audits in parallel")
    stop_on_error: bool = Field(False, description="Stop batch on first error")
    callback_url: Optional[str] = Field(None, description="Webhook URL for results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "file_path": "src/main.py",
                        "language": "python"
                    },
                    {
                        "file_path": "src/utils.py",
                        "language": "python"
                    }
                ],
                "parallel": True,
                "stop_on_error": False
            }
        }


class BatchAuditResponse(BaseModel):
    """Response model for batch audit"""
    batch_id: str = Field(..., description="Batch audit identifier")
    status: AuditStatus = Field(..., description="Overall batch status")
    total_items: int = Field(..., description="Total items in batch")
    completed_items: int = Field(..., description="Number of completed items")
    failed_items: int = Field(..., description="Number of failed items")
    results: List[AuditResult] = Field(..., description="Individual audit results")
    started_at: datetime = Field(..., description="Batch start time")
    completed_at: Optional[datetime] = Field(None, description="Batch completion time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_789012",
                "status": "completed",
                "total_items": 2,
                "completed_items": 2,
                "failed_items": 0,
                "results": [],
                "started_at": "2025-01-27T10:00:00Z",
                "completed_at": "2025-01-27T10:00:10Z"
            }
        }


class AuditHistory(BaseModel):
    """Audit history entry"""
    audit_id: str = Field(..., description="Audit identifier")
    file_path: str = Field(..., description="Audited file path")
    language: str = Field(..., description="Programming language")
    timestamp: datetime = Field(..., description="Audit timestamp")
    compliance_score: float = Field(..., description="Compliance score")
    total_violations: int = Field(..., description="Total violations")
    status: AuditStatus = Field(..., description="Audit status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audit_id": "aud_123456",
                "file_path": "src/main.py",
                "language": "python",
                "timestamp": "2025-01-27T10:00:00Z",
                "compliance_score": 85.5,
                "total_violations": 3,
                "status": "completed"
            }
        }

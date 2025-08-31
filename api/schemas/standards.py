"""
Standards-related Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StandardCategory(str, Enum):
    """Standard category enumeration"""
    CODING = "coding"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    GENERAL = "general"


class StandardVersion(BaseModel):
    """Standard version information"""
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version")
    created_at: datetime = Field(..., description="Version creation timestamp")
    created_by: str = Field(..., description="Version author")
    changelog: str = Field(..., description="Version changelog")
    is_active: bool = Field(True, description="Whether version is active")
    deprecated_at: Optional[datetime] = Field(None, description="Deprecation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "1.0.0",
                "created_at": "2025-01-27T10:00:00Z",
                "created_by": "admin",
                "changelog": "Initial version",
                "is_active": True,
                "deprecated_at": None
            }
        }


class StandardRule(BaseModel):
    """Individual standard rule"""
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    severity: str = Field(..., description="Rule severity level")
    category: StandardCategory = Field(..., description="Rule category")
    enabled: bool = Field(True, description="Whether rule is enabled")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Rule parameters")
    examples: Optional[List[Dict[str, str]]] = Field(None, description="Good/bad examples")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "PY001",
                "name": "Function Docstring Required",
                "description": "All functions must have docstrings",
                "severity": "medium",
                "category": "documentation",
                "enabled": True,
                "parameters": {
                    "min_length": 10
                },
                "examples": [
                    {
                        "type": "good",
                        "code": "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    return a + b"
                    }
                ]
            }
        }


class StandardCreate(BaseModel):
    """Request model for creating a standard"""
    name: str = Field(..., min_length=1, max_length=200, description="Standard name")
    description: str = Field(..., description="Standard description")
    language: str = Field(..., description="Programming language")
    category: StandardCategory = Field(..., description="Standard category")
    version: str = Field("1.0.0", pattern=r"^\d+\.\d+\.\d+$", description="Initial version")
    rules: List[StandardRule] = Field(..., min_length=1, description="Standard rules")
    tags: Optional[List[str]] = Field(None, description="Standard tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('language')
    def validate_language(cls, v):
        """Validate supported languages"""
        supported = ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'cpp', 'csharp', 'general']
        if v.lower() not in supported:
            raise ValueError(f"Language must be one of: {', '.join(supported)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python Best Practices",
                "description": "Comprehensive Python coding standards",
                "language": "python",
                "category": "coding",
                "version": "1.0.0",
                "rules": [],
                "tags": ["python", "best-practices"]
            }
        }


class StandardUpdate(BaseModel):
    """Request model for updating a standard"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Standard name")
    description: Optional[str] = Field(None, description="Standard description")
    category: Optional[StandardCategory] = Field(None, description="Standard category")
    rules: Optional[List[StandardRule]] = Field(None, description="Updated rules")
    tags: Optional[List[str]] = Field(None, description="Standard tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    create_version: bool = Field(False, description="Create new version on update")
    version_changelog: Optional[str] = Field(None, description="Changelog for new version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Updated description",
                "tags": ["python", "updated"],
                "create_version": True,
                "version_changelog": "Added new security rules"
            }
        }


class StandardResponse(BaseModel):
    """Response model for standard details"""
    standard_id: str = Field(..., description="Unique standard identifier")
    name: str = Field(..., description="Standard name")
    description: str = Field(..., description="Standard description")
    language: str = Field(..., description="Programming language")
    category: StandardCategory = Field(..., description="Standard category")
    current_version: str = Field(..., description="Current version")
    versions: List[StandardVersion] = Field(..., description="Version history")
    rules: List[StandardRule] = Field(..., description="Standard rules")
    tags: List[str] = Field(..., description="Standard tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    usage_count: int = Field(..., description="Number of times used in audits")
    average_compliance: Optional[float] = Field(None, description="Average compliance score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "standard_id": "std_123456",
                "name": "Python Best Practices",
                "description": "Comprehensive Python coding standards",
                "language": "python",
                "category": "coding",
                "current_version": "1.0.0",
                "versions": [],
                "rules": [],
                "tags": ["python", "best-practices"],
                "created_at": "2025-01-27T10:00:00Z",
                "updated_at": "2025-01-27T10:00:00Z",
                "usage_count": 42,
                "average_compliance": 85.5
            }
        }


class StandardQuery(BaseModel):
    """Query parameters for searching standards"""
    language: Optional[str] = Field(None, description="Filter by language")
    category: Optional[StandardCategory] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    search: Optional[str] = Field(None, description="Search in name and description")
    min_compliance: Optional[float] = Field(None, ge=0, le=100, description="Minimum compliance score")
    active_only: bool = Field(True, description="Only show active standards")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "python",
                "category": "security",
                "tags": ["owasp"],
                "active_only": True
            }
        }


class StandardImport(BaseModel):
    """Request model for importing standards"""
    source: str = Field(..., description="Import source (url, file, preset)")
    format: str = Field(..., description="Format (json, yaml, eslint, pylint)")
    content: Optional[str] = Field(None, description="Direct content for import")
    url: Optional[str] = Field(None, description="URL to import from")
    mapping: Optional[Dict[str, str]] = Field(None, description="Field mapping")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate import format"""
        supported = ['json', 'yaml', 'eslint', 'pylint', 'checkstyle', 'sonar']
        if v.lower() not in supported:
            raise ValueError(f"Format must be one of: {', '.join(supported)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "url",
                "format": "json",
                "url": "https://example.com/standards.json",
                "mapping": {
                    "rule_name": "name",
                    "rule_description": "description"
                }
            }
        }


class StandardExport(BaseModel):
    """Request model for exporting standards"""
    standard_ids: Optional[List[str]] = Field(None, description="Specific standards to export")
    format: str = Field("json", description="Export format")
    include_metadata: bool = Field(True, description="Include metadata")
    include_history: bool = Field(False, description="Include version history")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate export format"""
        supported = ['json', 'yaml', 'csv', 'markdown']
        if v.lower() not in supported:
            raise ValueError(f"Format must be one of: {', '.join(supported)}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "standard_ids": ["std_123456"],
                "format": "json",
                "include_metadata": True,
                "include_history": False
            }
        }

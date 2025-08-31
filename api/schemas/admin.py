"""
Admin-related Pydantic schemas
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class CacheStats(BaseModel):
    """Cache statistics"""
    total_keys: int = Field(..., description="Total number of cache keys")
    memory_used_mb: float = Field(..., description="Memory used in MB")
    hit_rate: float = Field(..., ge=0.0, le=100.0, description="Cache hit rate percentage")
    miss_rate: float = Field(..., ge=0.0, le=100.0, description="Cache miss rate percentage")
    evictions: int = Field(..., description="Number of evictions")
    namespaces: Dict[str, int] = Field(..., description="Keys per namespace")
    last_flush: Optional[datetime] = Field(None, description="Last cache flush timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_keys": 1234,
                "memory_used_mb": 45.6,
                "hit_rate": 89.5,
                "miss_rate": 10.5,
                "evictions": 12,
                "namespaces": {
                    "audit": 500,
                    "standards": 300,
                    "gemini": 434
                },
                "last_flush": "2025-01-27T08:00:00Z"
            }
        }


class SystemStats(BaseModel):
    """System statistics"""
    api_version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    total_requests: int = Field(..., description="Total API requests")
    active_connections: int = Field(..., description="Active connections")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    disk_usage_gb: float = Field(..., description="Disk usage in GB")
    audit_stats: Dict[str, Any] = Field(..., description="Audit statistics")
    gemini_stats: Dict[str, Any] = Field(..., description="Gemini API statistics")
    neo4j_stats: Dict[str, Any] = Field(..., description="Neo4j database statistics")
    error_rate: float = Field(..., description="Error rate percentage")
    average_response_time_ms: float = Field(..., description="Average response time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "api_version": "1.0.0",
                "uptime_seconds": 86400.0,
                "total_requests": 10000,
                "active_connections": 25,
                "cpu_usage_percent": 35.2,
                "memory_usage_mb": 512.3,
                "disk_usage_gb": 2.1,
                "audit_stats": {
                    "total_audits": 500,
                    "average_duration_ms": 2500
                },
                "gemini_stats": {
                    "total_requests": 1500,
                    "tokens_used": 250000
                },
                "neo4j_stats": {
                    "total_nodes": 5000,
                    "total_relationships": 15000
                },
                "error_rate": 0.5,
                "average_response_time_ms": 150.5
            }
        }


class UserCreate(BaseModel):
    """Request model for creating a user"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="Full name")
    role: UserRole = Field(..., description="User role")
    api_key: Optional[str] = Field(None, description="Custom API key (auto-generated if not provided)")
    rate_limit: Optional[int] = Field(None, description="Custom rate limit per minute")
    enabled: bool = Field(True, description="Whether user is enabled")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "developer",
                "enabled": True
            }
        }


class UserResponse(BaseModel):
    """Response model for user details"""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="Full name")
    role: UserRole = Field(..., description="User role")
    api_key: str = Field(..., description="API key (partially masked)")
    rate_limit: int = Field(..., description="Rate limit per minute")
    enabled: bool = Field(..., description="Whether user is enabled")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")
    total_requests: int = Field(..., description="Total API requests made")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_123456",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "developer",
                "api_key": "sk_live_****************************abcd",
                "rate_limit": 100,
                "enabled": True,
                "created_at": "2025-01-27T10:00:00Z",
                "last_active": "2025-01-27T12:00:00Z",
                "total_requests": 150
            }
        }


class ConfigUpdate(BaseModel):
    """Request model for updating configuration"""
    section: str = Field(..., description="Configuration section")
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, description="Configuration description")
    requires_restart: bool = Field(False, description="Whether change requires restart")
    
    class Config:
        json_schema_extra = {
            "example": {
                "section": "rate_limiting",
                "key": "default_limit",
                "value": 100,
                "description": "Default rate limit per minute",
                "requires_restart": False
            }
        }


class ConfigResponse(BaseModel):
    """Response model for configuration"""
    configs: Dict[str, Dict[str, Any]] = Field(..., description="Configuration sections")
    last_updated: datetime = Field(..., description="Last update timestamp")
    version: str = Field(..., description="Configuration version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "configs": {
                    "api": {
                        "host": "0.0.0.0",
                        "port": 8000,
                        "debug": False
                    },
                    "cache": {
                        "enabled": True,
                        "ttl": 3600
                    }
                },
                "last_updated": "2025-01-27T10:00:00Z",
                "version": "1.0.0"
            }
        }


class MaintenanceMode(BaseModel):
    """Maintenance mode configuration"""
    enabled: bool = Field(..., description="Whether maintenance mode is enabled")
    message: str = Field(..., description="Maintenance message")
    estimated_end: Optional[datetime] = Field(None, description="Estimated end time")
    allowed_ips: Optional[List[str]] = Field(None, description="IPs allowed during maintenance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "message": "System maintenance in progress",
                "estimated_end": "2025-01-27T14:00:00Z",
                "allowed_ips": ["192.168.1.1"]
            }
        }


class BackupRequest(BaseModel):
    """Request model for creating backup"""
    include_cache: bool = Field(True, description="Include cache data")
    include_database: bool = Field(True, description="Include database")
    include_configs: bool = Field(True, description="Include configurations")
    include_logs: bool = Field(False, description="Include logs")
    compression: str = Field("gzip", description="Compression type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "include_cache": True,
                "include_database": True,
                "include_configs": True,
                "include_logs": False,
                "compression": "gzip"
            }
        }


class BackupResponse(BaseModel):
    """Response model for backup operation"""
    backup_id: str = Field(..., description="Backup identifier")
    status: str = Field(..., description="Backup status")
    size_mb: float = Field(..., description="Backup size in MB")
    location: str = Field(..., description="Backup location")
    created_at: datetime = Field(..., description="Backup creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Backup expiration timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "backup_id": "bkp_20250127_100000",
                "status": "completed",
                "size_mb": 125.5,
                "location": "/backups/bkp_20250127_100000.tar.gz",
                "created_at": "2025-01-27T10:00:00Z",
                "expires_at": "2025-02-27T10:00:00Z"
            }
        }

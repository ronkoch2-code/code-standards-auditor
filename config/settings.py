"""
Configuration Settings for Code Standards Auditor
Centralized configuration management using environment variables
"""

import os
from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_RELOAD: bool = Field(default=False, env="API_RELOAD")
    API_VERSION: str = Field(default="1.0.0", env="API_VERSION")
    
    # Security
    API_KEY_HEADER: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    JWT_SECRET_KEY: str = Field(default="", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # Neo4j Database
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="", env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="neo4j", env="NEO4J_DATABASE")
    NEO4J_MAX_CONNECTION_LIFETIME: int = Field(default=3600, env="NEO4J_MAX_CONNECTION_LIFETIME")
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = Field(default=50, env="NEO4J_MAX_CONNECTION_POOL_SIZE")
    
    # Redis Cache
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_POOL_SIZE: int = Field(default=10, env="REDIS_POOL_SIZE")
    CACHE_TTL_SECONDS: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    # Google Gemini Configuration
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-1.5-pro", env="GEMINI_MODEL")
    GEMINI_MAX_TOKENS: int = Field(default=32000, env="GEMINI_MAX_TOKENS")
    GEMINI_TEMPERATURE: float = Field(default=0.1, env="GEMINI_TEMPERATURE")
    GEMINI_TOP_P: float = Field(default=0.95, env="GEMINI_TOP_P")
    GEMINI_TOP_K: int = Field(default=40, env="GEMINI_TOP_K")
    GEMINI_CACHE_TTL_MINUTES: int = Field(default=60, env="GEMINI_CACHE_TTL_MINUTES")
    GEMINI_BATCH_SIZE: int = Field(default=10, env="GEMINI_BATCH_SIZE")
    GEMINI_ENABLE_CACHING: bool = Field(default=True, env="GEMINI_ENABLE_CACHING")
    
    # Anthropic Configuration (Fallback)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-opus-20240229", env="ANTHROPIC_MODEL")
    ANTHROPIC_MAX_TOKENS: int = Field(default=4096, env="ANTHROPIC_MAX_TOKENS")
    
    # Code Analysis Configuration
    MAX_FILE_SIZE_BYTES: int = Field(default=1048576, env="MAX_FILE_SIZE_BYTES")  # 1MB
    MAX_FILES_PER_BATCH: int = Field(default=50, env="MAX_FILES_PER_BATCH")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["python", "java", "javascript", "typescript", "go", "rust"],
        env="SUPPORTED_LANGUAGES"
    )
    DEFAULT_SEVERITY_THRESHOLD: str = Field(default="warning", env="DEFAULT_SEVERITY_THRESHOLD")
    
    # Standards Management
    STANDARDS_BASE_PATH: str = Field(
        default="/Volumes/FS001/pythonscripts/standards",
        env="STANDARDS_BASE_PATH"
    )
    STANDARDS_VERSION_RETENTION_DAYS: int = Field(default=90, env="STANDARDS_VERSION_RETENTION_DAYS")
    AUTO_UPDATE_STANDARDS: bool = Field(default=True, env="AUTO_UPDATE_STANDARDS")
    
    # Performance Tuning
    ASYNC_POOL_SIZE: int = Field(default=10, env="ASYNC_POOL_SIZE")
    REQUEST_TIMEOUT_SECONDS: int = Field(default=300, env="REQUEST_TIMEOUT_SECONDS")
    BACKGROUND_TASK_WORKERS: int = Field(default=4, env="BACKGROUND_TASK_WORKERS")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PREFIX: str = Field(default="code_auditor", env="METRICS_PREFIX")
    HEALTH_CHECK_INTERVAL_SECONDS: int = Field(default=30, env="HEALTH_CHECK_INTERVAL_SECONDS")
    
    # Feature Flags
    ENABLE_BATCH_PROCESSING: bool = Field(default=True, env="ENABLE_BATCH_PROCESSING")
    ENABLE_REAL_TIME_UPDATES: bool = Field(default=True, env="ENABLE_REAL_TIME_UPDATES")
    ENABLE_STANDARDS_EVOLUTION: bool = Field(default=True, env="ENABLE_STANDARDS_EVOLUTION")
    ENABLE_WEBSOCKET: bool = Field(default=False, env="ENABLE_WEBSOCKET")
    
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        if not v:
            # Generate a default secret key for development
            # In production, this should be set via environment variable
            import secrets
            return secrets.token_urlsafe(32)
        return v
    
    @validator("GEMINI_API_KEY")
    def validate_gemini_key(cls, v):
        if not v:
            raise ValueError("GEMINI_API_KEY must be set")
        return v
    
    @validator("NEO4J_PASSWORD")
    def validate_neo4j_password(cls, v):
        if not v:
            # Try to get from environment if not set
            env_password = os.environ.get("NEO4J_PASSWORD")
            if env_password:
                return env_password
            raise ValueError("NEO4J_PASSWORD must be set")
        return v
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("SUPPORTED_LANGUAGES", pre=True)
    def parse_supported_languages(cls, v):
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Export commonly used settings
settings = get_settings()

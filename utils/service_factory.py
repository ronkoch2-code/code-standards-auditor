"""
Service Factory for Code Standards Auditor
Provides centralized service initialization and dependency injection
"""

from typing import Optional
from services.neo4j_service import Neo4jService
from services.gemini_service import GeminiService
from services.cache_service import CacheService
from config.settings import Settings

settings = Settings()

# Global service instances (singleton pattern)
_neo4j_service: Optional[Neo4jService] = None
_gemini_service: Optional[GeminiService] = None
_cache_service: Optional[CacheService] = None


def get_neo4j_service() -> Neo4jService:
    """
    Get or create Neo4j service instance

    Returns:
        Neo4jService instance
    """
    global _neo4j_service

    if _neo4j_service is None:
        _neo4j_service = Neo4jService(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )

    return _neo4j_service


def get_gemini_service() -> GeminiService:
    """
    Get or create Gemini service instance

    Returns:
        GeminiService instance
    """
    global _gemini_service

    if _gemini_service is None:
        # GeminiService configures API key globally, just pass other parameters
        _gemini_service = GeminiService(
            cache_ttl_minutes=settings.GEMINI_CACHE_TTL_MINUTES,
            enable_caching=settings.GEMINI_ENABLE_CACHING
        )

    return _gemini_service


def get_cache_service() -> CacheService:
    """
    Get or create Cache service instance

    Returns:
        CacheService instance
    """
    global _cache_service

    if _cache_service is None:
        _cache_service = CacheService(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            default_ttl=settings.CACHE_TTL_SECONDS
        )

    return _cache_service


def reset_services() -> None:
    """
    Reset all service instances (useful for testing)
    """
    global _neo4j_service, _gemini_service, _cache_service

    _neo4j_service = None
    _gemini_service = None
    _cache_service = None

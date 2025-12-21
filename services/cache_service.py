"""
Cache Service for Code Standards Auditor
High-level caching service with business logic
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import hashlib
import json
from utils.cache_manager import CacheManager
import structlog

logger = structlog.get_logger()


class CacheService:
    """
    High-level cache service with business logic specific caching strategies
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600
    ):
        self.cache_manager = CacheManager(
            host=host,
            port=port,
            db=db,
            password=password,
            default_ttl=default_ttl
        )
        
        # Define TTL strategies for different cache types
        self.ttl_config = {
            "audit_result": 3600,        # 1 hour
            "standards": 86400,          # 24 hours
            "llm_response": 7200,         # 2 hours
            "project_config": 1800,       # 30 minutes
            "statistics": 300,            # 5 minutes
            "health_check": 30,           # 30 seconds
        }
    
    async def connect(self):
        """Connect to cache backend"""
        await self.cache_manager.connect()
    
    async def disconnect(self):
        """Disconnect from cache backend"""
        await self.cache_manager.disconnect()
    
    async def health_check(self) -> bool:
        """Check cache health"""
        return await self.cache_manager.health_check()

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> bool:
        """
        Generic set method for caching arbitrary data.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not specified)
            namespace: Cache namespace for organization

        Returns:
            True if successful, False otherwise
        """
        return await self.cache_manager.set(
            key,
            value,
            ttl=ttl or self.cache_manager.default_ttl,
            namespace=namespace
        )

    async def get(
        self,
        key: str,
        namespace: str = "default"
    ) -> Optional[Any]:
        """
        Generic get method for retrieving cached data.

        Args:
            key: Cache key
            namespace: Cache namespace

        Returns:
            Cached value or None if not found
        """
        return await self.cache_manager.get(key, namespace=namespace)
    
    def _generate_audit_key(
        self,
        code_hash: str,
        language: str,
        project_id: Optional[str] = None
    ) -> str:
        """Generate cache key for audit results"""
        components = ["audit", language, code_hash]
        if project_id:
            components.append(project_id)
        return ":".join(components)
    
    async def get_audit_result(
        self,
        code: str,
        language: str,
        project_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached audit result"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        key = self._generate_audit_key(code_hash, language, project_id)
        
        result = await self.cache_manager.get(key, namespace="audit")
        if result:
            logger.info(f"Cache hit for audit: {key}")
        return result
    
    async def set_audit_result(
        self,
        code: str,
        language: str,
        result: Dict[str, Any],
        project_id: Optional[str] = None
    ) -> bool:
        """Cache audit result"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        key = self._generate_audit_key(code_hash, language, project_id)
        
        success = await self.cache_manager.set(
            key,
            result,
            ttl=self.ttl_config["audit_result"],
            namespace="audit"
        )
        
        if success:
            logger.info(f"Cached audit result: {key}")
        return success
    
    async def get_standards(
        self,
        language: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached standards"""
        key = f"{language}:{version or 'latest'}"
        return await self.cache_manager.get(key, namespace="standards")
    
    async def set_standards(
        self,
        language: str,
        standards: Dict[str, Any],
        version: Optional[str] = None
    ) -> bool:
        """Cache standards"""
        key = f"{language}:{version or 'latest'}"
        return await self.cache_manager.set(
            key,
            standards,
            ttl=self.ttl_config["standards"],
            namespace="standards"
        )
    
    async def get_llm_response(
        self,
        prompt_hash: str,
        model: str
    ) -> Optional[str]:
        """Get cached LLM response"""
        key = f"{model}:{prompt_hash}"
        return await self.cache_manager.get(key, namespace="llm")
    
    async def set_llm_response(
        self,
        prompt_hash: str,
        model: str,
        response: str
    ) -> bool:
        """Cache LLM response"""
        key = f"{model}:{prompt_hash}"
        return await self.cache_manager.set(
            key,
            response,
            ttl=self.ttl_config["llm_response"],
            namespace="llm"
        )
    
    async def get_project_config(
        self,
        project_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached project configuration"""
        return await self.cache_manager.get(project_id, namespace="project")
    
    async def set_project_config(
        self,
        project_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """Cache project configuration"""
        return await self.cache_manager.set(
            project_id,
            config,
            ttl=self.ttl_config["project_config"],
            namespace="project"
        )
    
    async def get_statistics(
        self,
        stat_type: str,
        key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached statistics"""
        cache_key = f"{stat_type}:{key}" if key else stat_type
        return await self.cache_manager.get(cache_key, namespace="stats")
    
    async def set_statistics(
        self,
        stat_type: str,
        data: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """Cache statistics"""
        cache_key = f"{stat_type}:{key}" if key else stat_type
        return await self.cache_manager.set(
            cache_key,
            data,
            ttl=self.ttl_config["statistics"],
            namespace="stats"
        )
    
    async def invalidate_project_cache(self, project_id: str) -> int:
        """Invalidate all cache entries for a project"""
        deleted = 0
        
        # Clear project config
        if await self.cache_manager.delete(project_id, namespace="project"):
            deleted += 1
        
        # Clear audit results for this project
        # Note: This would need to scan for keys, which is expensive
        # In production, consider maintaining a set of keys per project
        
        logger.info(f"Invalidated {deleted} cache entries for project {project_id}")
        return deleted
    
    async def invalidate_standards_cache(self, language: Optional[str] = None):
        """Invalidate standards cache"""
        if language:
            # Clear specific language standards
            await self.cache_manager.delete(f"{language}:latest", namespace="standards")
        else:
            # Clear all standards
            await self.cache_manager.clear_namespace("standards")

        logger.info(f"Invalidated standards cache for language: {language or 'all'}")

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "standard:123*")

        Returns:
            Number of entries deleted
        """
        try:
            # Use cache_manager's pattern deletion if available
            if hasattr(self.cache_manager, 'delete_pattern'):
                deleted = await self.cache_manager.delete_pattern(pattern)
            else:
                # Fallback: extract namespace and key from pattern
                # Pattern format: "namespace:key*" or just "key*"
                if ":" in pattern:
                    parts = pattern.split(":", 1)
                    namespace = parts[0]
                    key_pattern = parts[1].rstrip("*")
                    # Delete the specific key
                    if await self.cache_manager.delete(key_pattern, namespace=namespace):
                        deleted = 1
                    else:
                        deleted = 0
                else:
                    # No namespace, try deleting directly
                    key = pattern.rstrip("*")
                    if await self.cache_manager.delete(key):
                        deleted = 1
                    else:
                        deleted = 0

            logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
            return deleted
        except Exception as e:
            logger.warning(f"Failed to invalidate pattern {pattern}: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = await self.cache_manager.get_stats()
        
        # Add namespace-specific stats if needed
        stats["namespaces"] = {
            "audit": "Audit results",
            "standards": "Coding standards",
            "llm": "LLM responses",
            "project": "Project configurations",
            "stats": "Statistics"
        }
        
        return stats
    
    async def warm_cache(
        self,
        language: str,
        standards: Optional[Dict[str, Any]] = None
    ):
        """Pre-warm cache with commonly used data"""
        warmed = 0
        
        # Warm standards cache if provided
        if standards:
            if await self.set_standards(language, standards):
                warmed += 1
                logger.info(f"Warmed standards cache for {language}")
        
        # Could add more warming strategies here
        # e.g., common patterns, frequently used prompts, etc.
        
        return warmed

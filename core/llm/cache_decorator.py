"""
LLM Cache Decorator

Provides caching functionality for LLM responses to reduce API costs
and improve response times.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from typing import Dict, Optional, Any, Callable
from functools import wraps
import hashlib
import json
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Cache for LLM responses with TTL support.

    Supports both in-memory and Redis backends.
    """

    def __init__(
        self,
        backend: str = "memory",
        ttl_seconds: int = 3600,
        max_size: int = 1000,
        redis_client: Optional[Any] = None
    ):
        self.backend = backend
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.redis_client = redis_client

        # In-memory cache
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: list = []

        logger.info(f"Initialized LLM cache with backend: {backend}, TTL: {ttl_seconds}s")

    def _generate_cache_key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        **kwargs
    ) -> str:
        """
        Generate a cache key from request parameters.

        Args:
            prompt: The prompt text
            model: Model name
            temperature: Temperature parameter
            **kwargs: Additional parameters

        Returns:
            Cache key (hash)
        """
        # Create a deterministic string from parameters
        key_data = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            **kwargs
        }

        # Sort keys for determinism
        key_string = json.dumps(key_data, sort_keys=True)

        # Generate hash
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        if self.backend == "memory":
            return await self._get_from_memory(key)
        elif self.backend == "redis":
            return await self._get_from_redis(key)
        return None

    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached response.

        Args:
            key: Cache key
            value: Data to cache
            ttl: Optional TTL override

        Returns:
            True if successful
        """
        if self.backend == "memory":
            return await self._set_in_memory(key, value, ttl)
        elif self.backend == "redis":
            return await self._set_in_redis(key, value, ttl)
        return False

    async def delete(self, key: str) -> bool:
        """Delete a cached entry."""
        if self.backend == "memory":
            if key in self._memory_cache:
                del self._memory_cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return True
        elif self.backend == "redis" and self.redis_client:
            try:
                await self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Error deleting from Redis: {e}")

        return False

    async def clear(self) -> int:
        """Clear all cached entries."""
        if self.backend == "memory":
            count = len(self._memory_cache)
            self._memory_cache.clear()
            self._access_order.clear()
            return count
        elif self.backend == "redis" and self.redis_client:
            try:
                # This is a simplified version
                # In production, you'd want to use key patterns
                return 0
            except Exception as e:
                logger.error(f"Error clearing Redis cache: {e}")

        return 0

    async def _get_from_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Get from in-memory cache."""
        if key not in self._memory_cache:
            return None

        entry = self._memory_cache[key]

        # Check if expired
        if entry["expires_at"] < datetime.now().isoformat():
            del self._memory_cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None

        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"Cache hit: {key[:16]}...")
        return entry["data"]

    async def _set_in_memory(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set in in-memory cache."""
        # Evict if at max size
        if len(self._memory_cache) >= self.max_size and key not in self._memory_cache:
            # Remove oldest entry
            if self._access_order:
                oldest_key = self._access_order.pop(0)
                del self._memory_cache[oldest_key]

        ttl = ttl or self.ttl_seconds
        expires_at = datetime.now() + timedelta(seconds=ttl)

        self._memory_cache[key] = {
            "data": value,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now().isoformat()
        }

        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"Cached: {key[:16]}... (TTL: {ttl}s)")
        return True

    async def _get_from_redis(self, key: str) -> Optional[Dict[str, Any]]:
        """Get from Redis cache."""
        if not self.redis_client:
            return None

        try:
            data = await self.redis_client.get(key)
            if data:
                logger.debug(f"Redis cache hit: {key[:16]}...")
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting from Redis: {e}")

        return None

    async def _set_in_redis(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set in Redis cache."""
        if not self.redis_client:
            return False

        try:
            ttl = ttl or self.ttl_seconds
            data = json.dumps(value)
            await self.redis_client.setex(key, ttl, data)
            logger.debug(f"Redis cached: {key[:16]}... (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting in Redis: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.backend == "memory":
            return {
                "backend": "memory",
                "entries": len(self._memory_cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds
            }
        elif self.backend == "redis":
            return {
                "backend": "redis",
                "ttl_seconds": self.ttl_seconds
            }
        return {"backend": "unknown"}


# Global cache instance
_cache_instance: Optional[LLMCache] = None


def get_llm_cache(
    backend: str = "memory",
    ttl_seconds: int = 3600,
    redis_client: Optional[Any] = None
) -> LLMCache:
    """Get or create the global LLM cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LLMCache(
            backend=backend,
            ttl_seconds=ttl_seconds,
            redis_client=redis_client
        )
    return _cache_instance


def cached_llm_call(
    cache: Optional[LLMCache] = None,
    ttl: Optional[int] = None,
    cache_key_fn: Optional[Callable] = None
):
    """
    Decorator to cache LLM function calls.

    Args:
        cache: Optional cache instance (uses global if None)
        ttl: Optional TTL override
        cache_key_fn: Optional function to generate cache key

    Example:
        @cached_llm_call(ttl=7200)
        async def generate_response(prompt: str, model: str) -> str:
            # LLM call here
            return response
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache instance
            cache_instance = cache or get_llm_cache()

            # Generate cache key
            if cache_key_fn:
                cache_key = cache_key_fn(*args, **kwargs)
            else:
                # Default: hash function name and arguments
                key_data = {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(sorted(kwargs.items()))
                }
                key_string = json.dumps(key_data, sort_keys=True)
                cache_key = hashlib.sha256(key_string.encode()).hexdigest()

            # Try to get from cache
            cached_result = await cache_instance.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Using cached result for {func.__name__}")
                return cached_result

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_instance.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class CacheStats:
    """Track cache hit/miss statistics."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0

    def record_hit(self):
        """Record a cache hit."""
        self.hits += 1

    def record_miss(self):
        """Record a cache miss."""
        self.misses += 1

    def record_error(self):
        """Record a cache error."""
        self.errors += 1

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": self.get_hit_rate(),
            "total_requests": self.hits + self.misses
        }

    def reset(self):
        """Reset statistics."""
        self.hits = 0
        self.misses = 0
        self.errors = 0


# Global stats instance
_stats_instance = CacheStats()


def get_cache_stats() -> CacheStats:
    """Get the global cache stats instance."""
    return _stats_instance

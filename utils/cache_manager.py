"""
Cache Manager for Code Standards Auditor
Provides unified caching interface with Redis backend
"""

import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class CacheManager:
    """
    Centralized cache management with Redis backend
    Provides async interface for caching with TTL support
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        pool_size: int = 10,
        default_ttl: int = 3600
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.pool_size = pool_size
        self.default_ttl = default_ttl
        
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
        
        # Statistics tracking
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def connect(self):
        """
        Establish connection to Redis
        """
        try:
            self.connection_pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.pool_size,
                decode_responses=False  # We'll handle encoding/decoding ourselves
            )
            
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """
        Close Redis connection
        """
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def health_check(self) -> bool:
        """
        Check Redis connection health
        """
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except (ConnectionError, TimeoutError, OSError) as e:
            # Redis connection/network issues
            import structlog
            logger = structlog.get_logger()
            logger.debug("Redis health check failed", error=str(e))
            return False
    
    def _serialize(self, value: Any) -> bytes:
        """
        Serialize value for storage
        """
        try:
            # Try JSON first (more portable)
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize value from storage
        """
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    def _generate_key(self, key: str, namespace: Optional[str] = None) -> str:
        """
        Generate a namespaced cache key
        """
        if namespace:
            return f"{namespace}:{key}"
        return key
    
    async def get(
        self,
        key: str,
        namespace: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get value from cache
        """
        if not self.redis_client:
            logger.warning("Cache not connected")
            return None
        
        full_key = self._generate_key(key, namespace)
        
        try:
            data = await self.redis_client.get(full_key)
            
            if data is None:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss: {full_key}")
                return None
            
            self.stats["hits"] += 1
            logger.debug(f"Cache hit: {full_key}")
            
            return self._deserialize(data)
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache get error for {full_key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Set value in cache with optional TTL
        """
        if not self.redis_client:
            logger.warning("Cache not connected")
            return False
        
        full_key = self._generate_key(key, namespace)
        ttl = ttl or self.default_ttl
        
        try:
            serialized = self._serialize(value)
            await self.redis_client.setex(
                full_key,
                ttl,
                serialized
            )
            
            self.stats["sets"] += 1
            logger.debug(f"Cache set: {full_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache set error for {full_key}: {e}")
            return False
    
    async def delete(
        self,
        key: str,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Delete value from cache
        """
        if not self.redis_client:
            logger.warning("Cache not connected")
            return False
        
        full_key = self._generate_key(key, namespace)
        
        try:
            result = await self.redis_client.delete(full_key)
            self.stats["deletes"] += 1
            logger.debug(f"Cache delete: {full_key}")
            return bool(result)
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache delete error for {full_key}: {e}")
            return False
    
    async def exists(
        self,
        key: str,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Check if key exists in cache
        """
        if not self.redis_client:
            return False
        
        full_key = self._generate_key(key, namespace)
        
        try:
            return bool(await self.redis_client.exists(full_key))
        except Exception as e:
            logger.error(f"Cache exists error for {full_key}: {e}")
            return False
    
    async def get_many(
        self,
        keys: List[str],
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get multiple values from cache
        """
        if not self.redis_client:
            logger.warning("Cache not connected")
            return {}
        
        full_keys = [self._generate_key(k, namespace) for k in keys]
        
        try:
            values = await self.redis_client.mget(full_keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    self.stats["hits"] += 1
                    result[key] = self._deserialize(value)
                else:
                    self.stats["misses"] += 1
            
            return result
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Set multiple values in cache
        """
        if not self.redis_client:
            logger.warning("Cache not connected")
            return False
        
        ttl = ttl or self.default_ttl
        
        try:
            # Use pipeline for atomic operation
            async with self.redis_client.pipeline() as pipe:
                for key, value in mapping.items():
                    full_key = self._generate_key(key, namespace)
                    serialized = self._serialize(value)
                    pipe.setex(full_key, ttl, serialized)
                
                await pipe.execute()
            
            self.stats["sets"] += len(mapping)
            logger.debug(f"Cache set_many: {len(mapping)} keys")
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """
        Clear all keys in a namespace
        """
        if not self.redis_client:
            logger.warning("Cache not connected")
            return 0
        
        pattern = f"{namespace}:*"
        
        try:
            # Find all keys matching the pattern
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    deleted_count += deleted
                    self.stats["deletes"] += deleted
                
                if cursor == 0:
                    break
            
            logger.info(f"Cleared namespace {namespace}: {deleted_count} keys deleted")
            return deleted_count
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache clear_namespace error: {e}")
            return 0
    
    async def clear(self) -> bool:
        """
        Clear entire cache (use with caution)
        """
        if not self.redis_client:
            logger.warning("Cache not connected")
            return False
        
        try:
            await self.redis_client.flushdb()
            logger.warning("Cache cleared: all keys deleted")
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        """
        stats = self.stats.copy()
        
        # Calculate hit rate
        total_requests = stats["hits"] + stats["misses"]
        if total_requests > 0:
            stats["hit_rate"] = (stats["hits"] / total_requests) * 100
        else:
            stats["hit_rate"] = 0
        
        # Get Redis info if connected
        if self.redis_client:
            try:
                info = await self.redis_client.info("stats")
                stats["redis_info"] = {
                    "total_connections_received": info.get("total_connections_received", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            except Exception as e:
                logger.error(f"Failed to get Redis info: {e}")
        
        return stats
    
    async def get_ttl(
        self,
        key: str,
        namespace: Optional[str] = None
    ) -> Optional[int]:
        """
        Get remaining TTL for a key
        """
        if not self.redis_client:
            return None
        
        full_key = self._generate_key(key, namespace)
        
        try:
            ttl = await self.redis_client.ttl(full_key)
            return ttl if ttl >= 0 else None
        except Exception as e:
            logger.error(f"Cache get_ttl error for {full_key}: {e}")
            return None
    
    async def extend_ttl(
        self,
        key: str,
        ttl: int,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Extend TTL for an existing key
        """
        if not self.redis_client:
            return False
        
        full_key = self._generate_key(key, namespace)
        
        try:
            result = await self.redis_client.expire(full_key, ttl)
            logger.debug(f"Extended TTL for {full_key} to {ttl}s")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache extend_ttl error for {full_key}: {e}")
            return False

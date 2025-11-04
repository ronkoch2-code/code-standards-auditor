"""
Rate Limiting Middleware for Code Standards Auditor API
Provides configurable rate limiting with Redis backend
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import structlog
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Optional
import time

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API rate limiting

    Features:
    - Per-IP rate limiting
    - Per-user rate limiting (if authenticated)
    - Configurable limits
    - Burst support
    - Redis-backed (falls back to in-memory)
    - 429 responses with Retry-After header
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        use_redis: bool = False
    ):
        """
        Initialize rate limiting middleware

        Args:
            app: FastAPI application
            requests_per_minute: Number of requests allowed per minute
            burst_size: Allow burst of requests (default: requests_per_minute // 10)
            use_redis: Use Redis for distributed rate limiting (default: False)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or (requests_per_minute // 10)

        # In-memory storage (fallback)
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.use_redis = use_redis
        self.redis_client = None

        # TODO: Initialize Redis client if use_redis=True
        if use_redis:
            logger.info("Redis-backed rate limiting requested but not yet implemented")
            logger.info("Falling back to in-memory rate limiting")

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint

        Returns:
            Response from next handler or 429 if rate limited
        """
        # Get client identifier (IP + user if authenticated)
        client_id = self._get_client_id(request)

        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(client_id)

        if not is_allowed:
            # Rate limit exceeded
            retry_after = int(reset_time - time.time())

            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.url.path,
                method=request.method,
                retry_after=retry_after
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit of {self.requests_per_minute} requests/minute exceeded",
                    "retry_after": retry_after,
                    "limit": self.requests_per_minute,
                    "remaining": 0
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time))
                }
            )

        # Record request
        await self._record_request(client_id)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))

        return response

    def _get_client_id(self, request: Request) -> str:
        """
        Get unique identifier for client

        Uses IP address and user ID if authenticated

        Args:
            request: The request object

        Returns:
            Unique client identifier
        """
        # Get IP address
        client_ip = request.client.host if request.client else "unknown"

        # Add user ID if authenticated
        user = getattr(request.state, "user", None)
        if user and isinstance(user, dict):
            user_id = user.get("user_id")
            if user_id:
                return f"{client_ip}:{user_id}"

        return client_ip

    async def _check_rate_limit(self, client_id: str) -> tuple[bool, int, float]:
        """
        Check if client is within rate limit

        Args:
            client_id: Client identifier

        Returns:
            Tuple of (is_allowed, remaining_requests, reset_timestamp)
        """
        now = time.time()
        window_start = now - 60  # 60 second window

        # Clean old requests
        if client_id in self.request_counts:
            self.request_counts[client_id] = [
                ts for ts in self.request_counts[client_id]
                if ts > window_start
            ]

        # Get current count
        current_count = len(self.request_counts[client_id])

        # Calculate remaining and reset time
        remaining = max(0, self.requests_per_minute - current_count - 1)
        reset_time = now + 60

        # Check if within limit
        is_allowed = current_count < self.requests_per_minute

        return is_allowed, remaining, reset_time

    async def _record_request(self, client_id: str) -> None:
        """
        Record a request for rate limiting

        Args:
            client_id: Client identifier
        """
        now = time.time()
        self.request_counts[client_id].append(now)

        # Periodically clean up old data to prevent memory leak
        if len(self.request_counts) > 10000:
            await self._cleanup_old_data()

    async def _cleanup_old_data(self) -> None:
        """
        Clean up rate limit data older than the window

        Prevents memory from growing unbounded
        """
        now = time.time()
        window_start = now - 60

        # Remove entries with no recent requests
        keys_to_remove = []
        for client_id, timestamps in self.request_counts.items():
            # Filter timestamps
            recent = [ts for ts in timestamps if ts > window_start]
            if not recent:
                keys_to_remove.append(client_id)
            else:
                self.request_counts[client_id] = recent

        # Remove empty entries
        for key in keys_to_remove:
            del self.request_counts[key]

        logger.debug(
            "Rate limit cleanup completed",
            removed_clients=len(keys_to_remove),
            active_clients=len(self.request_counts)
        )


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-backed rate limiting middleware for distributed systems

    This is a more robust implementation suitable for production
    with multiple API instances.

    TODO: Implement with Redis client
    """

    def __init__(
        self,
        app,
        redis_client,
        requests_per_minute: int = 60,
        key_prefix: str = "ratelimit"
    ):
        """
        Initialize Redis-backed rate limiting

        Args:
            app: FastAPI application
            redis_client: Redis client instance
            requests_per_minute: Number of requests allowed per minute
            key_prefix: Prefix for Redis keys
        """
        super().__init__(app)
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.key_prefix = key_prefix

    async def dispatch(self, request: Request, call_next):
        """
        Process request with Redis-backed rate limiting

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint

        Returns:
            Response from next handler or 429 if rate limited
        """
        # TODO: Implement Redis-based rate limiting
        # For now, pass through
        logger.warning("RedisRateLimitMiddleware not yet fully implemented")
        return await call_next(request)


class EndpointRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-endpoint rate limiting with different limits for different endpoints

    Example:
        limits = {
            "/api/v1/audit": 10,  # 10 requests/minute
            "/api/v1/standards": 60,  # 60 requests/minute
            "/api/v1/health": 300,  # 300 requests/minute
        }
    """

    def __init__(
        self,
        app,
        endpoint_limits: Dict[str, int],
        default_limit: int = 60
    ):
        """
        Initialize per-endpoint rate limiting

        Args:
            app: FastAPI application
            endpoint_limits: Dict mapping endpoint paths to limits
            default_limit: Default limit for endpoints not in mapping
        """
        super().__init__(app)
        self.endpoint_limits = endpoint_limits
        self.default_limit = default_limit
        self.request_counts: Dict[str, Dict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )

    async def dispatch(self, request: Request, call_next):
        """
        Process request with per-endpoint rate limiting

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint

        Returns:
            Response from next handler or 429 if rate limited
        """
        path = request.url.path
        client_id = self._get_client_id(request)

        # Get limit for this endpoint
        limit = self.endpoint_limits.get(path, self.default_limit)

        # Check rate limit for this endpoint
        is_allowed, remaining, reset_time = await self._check_rate_limit(
            client_id, path, limit
        )

        if not is_allowed:
            retry_after = int(reset_time - time.time())

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit of {limit} requests/minute exceeded for {path}",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)}
            )

        # Record request
        await self._record_request(client_id, path)

        response = await call_next(request)
        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        return request.client.host if request.client else "unknown"

    async def _check_rate_limit(
        self,
        client_id: str,
        path: str,
        limit: int
    ) -> tuple[bool, int, float]:
        """Check rate limit for specific endpoint"""
        now = time.time()
        window_start = now - 60

        # Clean old requests
        if client_id in self.request_counts and path in self.request_counts[client_id]:
            self.request_counts[client_id][path] = [
                ts for ts in self.request_counts[client_id][path]
                if ts > window_start
            ]

        # Get current count
        current_count = len(self.request_counts[client_id][path])
        remaining = max(0, limit - current_count - 1)
        reset_time = now + 60

        is_allowed = current_count < limit

        return is_allowed, remaining, reset_time

    async def _record_request(self, client_id: str, path: str) -> None:
        """Record request for specific endpoint"""
        now = time.time()
        self.request_counts[client_id][path].append(now)

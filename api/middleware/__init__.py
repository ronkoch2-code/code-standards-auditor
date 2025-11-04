"""
API Middleware Package

Provides middleware for:
- Authentication (JWT and API key)
- Request/Response logging
- Rate limiting
- Performance monitoring
"""

from api.middleware.auth import AuthMiddleware, create_jwt_token
from api.middleware.logging import (
    LoggingMiddleware,
    PerformanceLoggingMiddleware,
    DetailedLoggingMiddleware,
    get_request_id
)
from api.middleware.rate_limit import (
    RateLimitMiddleware,
    RedisRateLimitMiddleware,
    EndpointRateLimitMiddleware
)

__all__ = [
    # Auth
    "AuthMiddleware",
    "create_jwt_token",
    # Logging
    "LoggingMiddleware",
    "PerformanceLoggingMiddleware",
    "DetailedLoggingMiddleware",
    "get_request_id",
    # Rate Limiting
    "RateLimitMiddleware",
    "RedisRateLimitMiddleware",
    "EndpointRateLimitMiddleware",
]

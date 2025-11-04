"""
Logging Middleware for Code Standards Auditor API
Provides request/response logging with timing and request tracking
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog
import time
import uuid
from typing import Callable

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging

    Features:
    - Unique request ID for tracing
    - Request timing
    - Request/response logging
    - Error tracking
    - Structured logging with context
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request with logging

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint

        Returns:
            Response from the next handler
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Extract request info
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else None

        # Log request start
        logger.info(
            "Request started",
            request_id=request_id,
            method=method,
            path=path,
            query=query,
            client_host=client_host,
            user_agent=request.headers.get("user-agent", "unknown")
        )

        # Process request and handle errors
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log successful response
            logger.info(
                "Request completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=f"{duration * 1000:.2f}",
                duration_seconds=f"{duration:.3f}"
            )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log error
            logger.error(
                "Request failed",
                request_id=request_id,
                method=method,
                path=path,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=f"{duration * 1000:.2f}",
                duration_seconds=f"{duration:.3f}"
            )

            # Re-raise to let error handlers deal with it
            raise


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Advanced middleware for performance monitoring

    Features:
    - Slow request detection
    - Performance metrics
    - Threshold-based alerting
    """

    def __init__(self, app, slow_threshold_ms: float = 1000.0):
        """
        Initialize performance logging middleware

        Args:
            app: FastAPI application
            slow_threshold_ms: Threshold in milliseconds for slow request alert
        """
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request with performance monitoring

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint

        Returns:
            Response from the next handler
        """
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # Alert on slow requests
        if duration_ms > self.slow_threshold_ms:
            logger.warning(
                "Slow request detected",
                request_id=getattr(request.state, "request_id", "unknown"),
                method=request.method,
                path=request.url.path,
                duration_ms=f"{duration_ms:.2f}",
                threshold_ms=self.slow_threshold_ms,
                status_code=response.status_code
            )

        # Add timing header
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        return response


class DetailedLoggingMiddleware(BaseHTTPMiddleware):
    """
    Detailed logging middleware for debugging

    CAUTION: This logs request/response bodies and should only be used
    in development or debugging scenarios. DO NOT use in production as it:
    - Logs sensitive data
    - Increases log volume significantly
    - Impacts performance
    """

    def __init__(self, app, max_body_length: int = 1000):
        """
        Initialize detailed logging middleware

        Args:
            app: FastAPI application
            max_body_length: Maximum body length to log (truncate beyond this)
        """
        super().__init__(app)
        self.max_body_length = max_body_length

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request with detailed logging

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint

        Returns:
            Response from the next handler
        """
        # Log request details
        headers = dict(request.headers)
        # Redact sensitive headers
        if "authorization" in headers:
            headers["authorization"] = "***REDACTED***"
        if "x-api-key" in headers:
            headers["x-api-key"] = "***REDACTED***"

        try:
            # Try to read body (may not always work)
            body = await request.body()
            body_str = body.decode("utf-8")[:self.max_body_length]
            if len(body) > self.max_body_length:
                body_str += "... (truncated)"
        except Exception:
            body_str = "<unable to read body>"

        logger.debug(
            "Request details",
            request_id=getattr(request.state, "request_id", "unknown"),
            method=request.method,
            path=request.url.path,
            headers=headers,
            body=body_str
        )

        response = await call_next(request)

        return response


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state

    Args:
        request: FastAPI request object

    Returns:
        Request ID or 'unknown' if not set
    """
    return getattr(request.state, "request_id", "unknown")

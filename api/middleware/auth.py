"""
Authentication Middleware for Code Standards Auditor API
Handles JWT and API key authentication
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional, List
import jwt
import structlog
from datetime import datetime, timedelta

from config.settings import Settings

logger = structlog.get_logger()
settings = Settings()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for authentication using JWT tokens or API keys

    Supports:
    - JWT token authentication (Bearer token)
    - API key authentication (X-API-Key header)
    - Public endpoints (no auth required)
    """

    # Endpoints that don't require authentication
    PUBLIC_PATHS: List[str] = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/metrics",
    ]

    def __init__(self, app):
        super().__init__(app)
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = settings.JWT_ALGORITHM
        self.api_key_header = settings.API_KEY_HEADER

    async def dispatch(self, request: Request, call_next):
        """
        Process request authentication

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint

        Returns:
            Response from the next handler or 401/403 error
        """
        # Allow public paths without authentication
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Extract and validate authentication
        auth_result = await self._authenticate_request(request)

        if not auth_result["authenticated"]:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "detail": auth_result["error"],
                    "path": request.url.path
                }
            )

        # Add user info to request state
        request.state.user = auth_result.get("user", {})
        request.state.auth_method = auth_result.get("method", "unknown")

        # Log successful authentication
        logger.info(
            "Request authenticated",
            path=request.url.path,
            method=request.method,
            auth_method=auth_result["method"],
            user_id=auth_result.get("user", {}).get("user_id")
        )

        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)"""
        # Exact match
        if path in self.PUBLIC_PATHS:
            return True

        # Prefix match (e.g., /docs/*)
        for public_path in self.PUBLIC_PATHS:
            if path.startswith(public_path):
                return True

        return False

    async def _authenticate_request(self, request: Request) -> dict:
        """
        Authenticate request using JWT or API key

        Returns:
            dict with authentication result:
            {
                "authenticated": bool,
                "method": str ("jwt" or "api_key"),
                "user": dict (user info),
                "error": str (if not authenticated)
            }
        """
        # Try JWT authentication first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            jwt_result = self._validate_jwt(token)
            if jwt_result["valid"]:
                return {
                    "authenticated": True,
                    "method": "jwt",
                    "user": jwt_result["payload"]
                }

        # Try API key authentication
        api_key = request.headers.get(self.api_key_header)
        if api_key:
            api_key_result = self._validate_api_key(api_key)
            if api_key_result["valid"]:
                return {
                    "authenticated": True,
                    "method": "api_key",
                    "user": api_key_result["user"]
                }

        # No valid authentication found
        return {
            "authenticated": False,
            "error": "No valid authentication credentials provided"
        }

    def _validate_jwt(self, token: str) -> dict:
        """
        Validate JWT token

        Args:
            token: JWT token string

        Returns:
            dict with validation result and payload if valid
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return {
                    "valid": False,
                    "error": "Token expired"
                }

            return {
                "valid": True,
                "payload": payload
            }

        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e))
            return {
                "valid": False,
                "error": f"Invalid token: {str(e)}"
            }
        except Exception as e:
            logger.error("JWT validation error", error=str(e))
            return {
                "valid": False,
                "error": "Token validation failed"
            }

    def _validate_api_key(self, api_key: str) -> dict:
        """
        Validate API key

        Args:
            api_key: API key string

        Returns:
            dict with validation result and user info if valid

        Note:
            This is a basic implementation. In production, you should:
            1. Store API keys in database (hashed)
            2. Associate with user accounts
            3. Support key rotation
            4. Track usage per key
        """
        # TODO: Implement proper API key validation with database lookup
        # For now, this is a placeholder that allows any non-empty key
        # in development mode

        if not api_key:
            return {
                "valid": False,
                "error": "Empty API key"
            }

        # In production, query database for API key
        # For development, accept any key (log warning)
        logger.warning(
            "API key authentication using placeholder validation",
            note="Implement proper validation before production use"
        )

        return {
            "valid": True,
            "user": {
                "user_id": "api_key_user",
                "auth_method": "api_key",
                "api_key": api_key[:8] + "...",  # Log partial key only
            }
        }


def create_jwt_token(
    user_id: str,
    additional_claims: Optional[dict] = None,
    expires_hours: Optional[int] = None
) -> str:
    """
    Create a JWT token for a user

    Args:
        user_id: User identifier
        additional_claims: Additional claims to include in token
        expires_hours: Token expiration in hours (default from settings)

    Returns:
        Encoded JWT token string
    """
    settings = Settings()

    if expires_hours is None:
        expires_hours = settings.JWT_EXPIRATION_HOURS

    exp = datetime.utcnow() + timedelta(hours=expires_hours)

    payload = {
        "user_id": user_id,
        "exp": exp,
        "iat": datetime.utcnow(),
    }

    if additional_claims:
        payload.update(additional_claims)

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return token

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog
from typing import Callable

from ..core.config import settings
from ..core.security import verify_token

logger = structlog.get_logger(__name__)


class CORSMiddlewareCustom:
    """Custom CORS middleware configuration."""

    def __init__(self, app):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=settings.CORS_METHODS,
            allow_headers=settings.CORS_HEADERS,
        )


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to measure request processing time."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(
            "Request processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
        )
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware to verify JWT tokens."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for certain paths
        if self._skip_authentication(request.url.path):
            return await call_next(request)

        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]
        try:
            # Verify token
            payload = verify_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )

            # Add user info to request state
            request.state.user_id = user_id
            request.state.token_type = payload.get("type", "access")

        except Exception as e:
            logger.error("Authentication failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    def _skip_authentication(self, path: str) -> bool:
        """Check if authentication is required for the path."""
        # List of paths that don't require authentication
        no_auth_paths = [
            "/api/v1/auth/login",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
        ]
        return any(path.startswith(no_auth_path) for no_auth_path in no_auth_paths)


class RoleAuthorizationMiddleware(BaseHTTPMiddleware):
    """Role-based authorization middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authorization for certain paths
        if self._skip_authorization(request.url.path):
            return await call_next(request)

        # Check if user is authenticated
        if not hasattr(request.state, "user_id"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # Get user role from database
        from ..services.auth import auth_service
        with request.state.db_session as db:
            user = auth_service.get_user_by_id(db, request.state.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            request.state.user_role = user.role
            request.state.user = user

        return await call_next(request)

    def _skip_authorization(self, path: str) -> bool:
        """Check if authorization is required for the path."""
        # Public paths that don't require authorization
        no_auth_paths = [
            "/api/v1/auth/login",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
        ]
        # Admin-only paths
        admin_only_paths = [
            "/api/v1/admin",
        ]

        # Check if path requires admin role
        requires_admin = any(path.startswith(admin_path) for admin_path in admin_only_paths)

        if requires_admin:
            return False  # Don't skip authorization for admin paths

        return any(path.startswith(no_auth_path) for no_auth_path in no_auth_paths)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(
                "Unhandled exception",
                method=request.method,
                url=str(request.url),
                error=str(e),
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


def setup_middleware(app):
    """Setup all middlewares for the application."""
    app.add_middleware(CORSMiddlewareCustom)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RoleAuthorizationMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
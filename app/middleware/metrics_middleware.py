"""Middleware for session management and request logging."""

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for session management, request timing, and logging.

    Features:
    - Session ID generation and management via cookies
    - Request/response timing headers
    - Request logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with session management and timing.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware or route handler

        Returns:
            Response with session cookie and timing headers
        """
        # Skip for health check and static endpoints
        if self._should_skip(request.url.path):
            return await call_next(request)

        # Generate or retrieve session_id
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.debug(f"Generated new session_id: {session_id}")

        # Attach session_id to request state for controllers to access
        request.state.session_id = session_id

        # Track request timing
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Request failed: {request.method} {request.url.path} " f"({response_time_ms}ms) - {str(e)}")
            raise

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Add timing header
        response.headers["X-Response-Time"] = f"{response_time_ms}ms"

        # Set session cookie (HttpOnly, Secure in production)
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=31536000,  # 1 year
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
        )

        # Log request completion
        logger.info(f"{request.method} {request.url.path} - " f"{response.status_code} ({response_time_ms}ms)")

        return response

    def _should_skip(self, path: str) -> bool:
        """
        Check if processing should be skipped for this endpoint.

        Args:
            path: Request URL path

        Returns:
            True if should be skipped
        """
        skip_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
        }
        return path in skip_paths

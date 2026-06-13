"""Middleware components for the FastAPI application."""

import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)

# Context variable to store request ID across async boundaries
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return request_id_ctx.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add a unique request ID to each request.

    The request ID is:
    - Generated as a UUID if not provided in X-Request-ID header
    - Added to response headers as X-Request-ID
    - Made available via get_request_id() for logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get request ID from header or generate one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store in context for use throughout request handling
        token = request_id_ctx.set(request_id)

        # Log the request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            },
        )

        try:
            response = await call_next(request)

            # Log the response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                },
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            logger.exception(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                },
            )
            raise

        finally:
            # Reset context
            request_id_ctx.reset(token)

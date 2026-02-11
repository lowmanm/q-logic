"""Request lifecycle middleware: request IDs, logging, error boundary."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import structlog

from app.core.config import settings

logger = structlog.get_logger("middleware")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for traceability."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )

        return response


class ErrorBoundaryMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return safe error responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            logger.exception("unhandled_error", error=str(exc))
            detail = str(exc) if not settings.is_production else "Internal server error"
            return JSONResponse(
                status_code=500,
                content={"detail": detail},
            )

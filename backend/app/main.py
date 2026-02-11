"""Q-Logic Dynamic Schema Orchestration — FastAPI application entry point."""

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware, ErrorBoundaryMiddleware
from app.api.routes import auth, schema, workspace, employees, metrics

setup_logging()
logger = structlog.get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", environment=settings.ENVIRONMENT)
    if not settings.is_production:
        # Dev convenience: auto-create tables. Production uses Alembic migrations.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware ordering: outermost executes first.
# ErrorBoundary catches anything unhandled, RequestId attaches traceability.
app.add_middleware(ErrorBoundaryMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(schema.router, prefix="/api")
app.include_router(workspace.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")


@app.get("/api/health")
async def health():
    """Liveness probe — always returns ok if the process is running."""
    return {"status": "ok"}


@app.get("/api/health/ready")
async def readiness():
    """Readiness probe — verifies database connectivity."""
    from sqlalchemy import text as sa_text

    try:
        async with engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        logger.exception("readiness_check_failed")
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "disconnected"},
        )

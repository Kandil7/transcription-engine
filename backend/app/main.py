"""Main FastAPI application for Transcription Engine."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from structlog import get_logger

from app.api.v1.api import api_router
from app.config import settings
from app.core.exceptions import TranscriptionEngineError
from app.core.logging import setup_logging
from app.core.monitoring import init_monitoring
from app.db.session import init_db

# Setup logging
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Transcription Engine", profile=settings.detected_profile.value)

    # Initialize database
    await init_db()

    # Initialize monitoring
    if settings.enable_prometheus:
        init_monitoring()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Transcription Engine")


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Advanced AI-powered transcription, translation, and summarization engine",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics endpoint
if settings.enable_prometheus:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.version,
        "profile": settings.detected_profile.value,
        "gpu_memory_gb": settings.gpu_memory_gb,
        "cpu_cores": settings.cpu_cores,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Transcription Engine API",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
    }


# Custom exception handler for TranscriptionEngineError
@app.exception_handler(TranscriptionEngineError)
async def transcription_engine_exception_handler(request: Request, exc: TranscriptionEngineError):
    """Handler for custom TranscriptionEngineError exceptions."""
    logger.error(
        "TranscriptionEngineError",
        error_code=exc.error_code,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        exc_info=exc
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "type": exc.__class__.__name__.lower(),
            **exc.details
        },
    )


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "type": "internal_error"
        },
    )


# Include API routers
app.include_router(api_router, prefix=settings.api_v1_str)


if __name__ == "__main__":
    import uvicorn

    setup_logging()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
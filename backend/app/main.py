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
from app.core.validation import validate_all
from app.db.session import init_db

# Setup logging
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Transcription Engine", profile=settings.detected_profile.value)

    # Validate configuration
    try:
        warnings = await validate_all()
        if warnings:
            logger.warning("Configuration validation warnings", warnings=warnings)
        else:
            logger.info("Configuration validation passed")
    except Exception as e:
        logger.error("Configuration validation failed", error=str(e))
        # Don't fail startup, but log the error

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        # In production, you might want to fail fast here
        if settings.environment.value == "production":
            raise

    # Initialize monitoring
    if settings.enable_prometheus:
        try:
            init_monitoring()
            logger.info("Monitoring initialized successfully")
        except Exception as e:
            logger.warning("Monitoring initialization failed", error=str(e))

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
    """Health check endpoint with detailed status."""
    from app.core.validation import validate_database_connection, validate_redis_connection
    
    health_status = {
        "status": "healthy",
        "version": settings.version,
        "profile": settings.detected_profile.value,
        "gpu_memory_gb": settings.gpu_memory_gb,
        "cpu_cores": settings.cpu_cores,
        "environment": settings.environment.value,
    }
    
    # Check database connectivity
    try:
        await validate_database_connection()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        await validate_redis_connection()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


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
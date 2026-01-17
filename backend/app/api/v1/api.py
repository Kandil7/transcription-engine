"""Main API router combining all endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import jobs, qa, streaming, upload, websocket

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"])
api_router.include_router(streaming.router, prefix="/stream", tags=["streaming"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
"""Main API router combining all endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import jobs, upload, websocket

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
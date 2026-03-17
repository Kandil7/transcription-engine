"""Streaming transcription API endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from structlog import get_logger

try:
    from app.services.streaming_service import streaming_service
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False
    streaming_service = None

logger = get_logger(__name__)
router = APIRouter()


class StreamStartRequest(BaseModel):
    """Request model for starting a stream."""

    language: str = "ar"


class StreamStatusResponse(BaseModel):
    """Response model for stream status."""

    stream_id: str
    status: str
    language: str
    segments_processed: int = 0
    buffer_size: int = 0
    last_activity: float = 0.0


class StreamListResponse(BaseModel):
    """Response model for listing streams."""

    active_streams: List[dict]


@router.post("/{stream_id}/start", response_model=dict)
async def start_stream(stream_id: str, request: StreamStartRequest):
    """
    Start a new streaming transcription session.

    - **stream_id**: Unique stream identifier
    - **language**: Language code for transcription
    """
    if not STREAMING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Streaming service is not available"
        )
    
    try:
        await streaming_service.start_stream(stream_id, request.language)

        return {
            "message": "Streaming session started",
            "stream_id": stream_id,
            "language": request.language,
            "websocket_url": f"ws://localhost:8000/api/v1/ws/stream/{stream_id}"
        }

    except Exception as e:
        logger.error("Failed to start stream", stream_id=stream_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start streaming session: {str(e)}"
        )


@router.get("/{stream_id}/status", response_model=StreamStatusResponse)
async def get_stream_status(stream_id: str) -> StreamStatusResponse:
    """
    Get the status of a streaming session.

    - **stream_id**: Unique stream identifier
    """
    if not STREAMING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Streaming service is not available"
        )
    
    try:
        status_info = await streaming_service.get_stream_status(stream_id)

        return StreamStatusResponse(
            stream_id=stream_id,
            status=status_info.get("status", "unknown"),
            language=status_info.get("language", "unknown"),
            segments_processed=status_info.get("segments_processed", 0),
            buffer_size=status_info.get("buffer_size", 0),
            last_activity=status_info.get("last_activity", 0.0),
        )

    except Exception as e:
        logger.error("Failed to get stream status", stream_id=stream_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stream status"
        )


@router.post("/{stream_id}/stop", response_model=dict)
async def stop_stream(stream_id: str):
    """
    Stop a streaming session and get final results.

    - **stream_id**: Unique stream identifier
    """
    if not STREAMING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Streaming service is not available"
        )
    
    try:
        final_results = await streaming_service.end_stream(stream_id)

        return {
            "message": "Streaming session stopped",
            "stream_id": stream_id,
            "final_results": final_results
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to stop stream", stream_id=stream_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop streaming session: {str(e)}"
        )


@router.get("/active", response_model=StreamListResponse)
async def list_active_streams() -> StreamListResponse:
    """
    List all active streaming sessions.
    """
    if not STREAMING_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Streaming service is not available"
        )
    
    try:
        active_streams = streaming_service.list_active_streams()

        return StreamListResponse(active_streams=active_streams)

    except Exception as e:
        logger.error("Failed to list active streams", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list active streams"
        )
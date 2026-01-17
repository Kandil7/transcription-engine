"""WebSocket endpoint for real-time job updates and streaming transcription."""

import json
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from structlog import get_logger

from app.services.job_service import get_job
from app.services.streaming_service import streaming_service
from app.services.websocket_manager import WebSocketManager

logger = get_logger(__name__)
router = APIRouter()

# Global WebSocket manager instance
ws_manager = WebSocketManager()


@router.websocket("/jobs/{job_id}")
async def job_progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress updates.

    - **job_id**: Unique job identifier to subscribe to updates for
    """
    await websocket.accept()

    # Validate job exists
    job = await get_job(job_id)
    if not job:
        await websocket.send_json({
            "type": "error",
            "message": "Job not found",
            "job_id": job_id
        })
        await websocket.close()
        return

    # Register this connection for the job
    await ws_manager.connect(job_id, websocket)

    try:
        # Send initial job status
        await ws_manager.send_to_job(job_id, {
            "type": "job_status",
            "job_id": job_id,
            "status": job.status.value,
            "progress": job.progress,
            "message": job.message,
        })

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client messages (optional)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client requests
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "get_status":
                    job = await get_job(job_id)
                    if job:
                        await websocket.send_json({
                            "type": "job_status",
                            "job_id": job_id,
                            "status": job.status.value,
                            "progress": job.progress,
                            "message": job.message,
                        })

            except json.JSONDecodeError:
                # Invalid JSON, ignore
                continue

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", job_id=job_id)
    except Exception as e:
        logger.error("WebSocket error", job_id=job_id, error=str(e))
    finally:
        # Clean up connection
        await ws_manager.disconnect(job_id, websocket)


@router.websocket("/stream/{session_id}")
async def streaming_transcription_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time streaming transcription.

    - **session_id**: Unique session identifier for the streaming session
    """
    await websocket.accept()

    logger.info("Streaming transcription session started", session_id=session_id)

    # Initialize streaming session
    await streaming_service.start_stream(session_id)

    try:
        # Send session confirmation
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id,
            "message": "Real-time streaming transcription session started"
        })

        # Keep connection alive for streaming
        while True:
            try:
                # Receive audio data from client
                audio_chunk = await websocket.receive_bytes()

                # Process audio chunk in real-time
                async for result in streaming_service.process_audio_chunk(session_id, audio_chunk):
                    await websocket.send_json(result)

            except Exception as e:
                logger.error("Streaming processing error", session_id=session_id, error=str(e))
                await websocket.send_json({
                    "type": "error",
                    "session_id": session_id,
                    "message": f"Processing error: {str(e)}"
                })

    except WebSocketDisconnect:
        logger.info("Streaming WebSocket disconnected", session_id=session_id)

        # Get final results before cleanup
        try:
            final_results = await streaming_service.end_stream(session_id)
            await websocket.send_json({
                "type": "session_ended",
                "session_id": session_id,
                "final_results": final_results
            })
        except Exception as e:
            logger.error("Error getting final results", session_id=session_id, error=str(e))

    except Exception as e:
        logger.error("Streaming WebSocket error", session_id=session_id, error=str(e))
    finally:
        # Clean up streaming session
        try:
            await streaming_service.end_stream(session_id)
        except Exception as cleanup_error:
            logger.error("Error during streaming cleanup", session_id=session_id, error=str(cleanup_error))
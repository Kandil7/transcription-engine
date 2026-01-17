"""WebSocket manager for real-time job updates."""

import asyncio
from typing import Dict, List, Set

from fastapi import WebSocket
from structlog import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        """Connect a WebSocket to a job."""
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        logger.info("WebSocket connected", job_id=job_id, total_connections=len(self.active_connections[job_id]))

    async def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        """Disconnect a WebSocket from a job."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

            logger.info("WebSocket disconnected", job_id=job_id, remaining_connections=len(self.active_connections.get(job_id, set())))

    async def send_to_job(self, job_id: str, message: dict) -> None:
        """Send a message to all WebSockets connected to a job."""
        if job_id not in self.active_connections:
            return

        disconnected = set()

        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error("Failed to send message to WebSocket", job_id=job_id, error=str(e))
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            self.active_connections[job_id].discard(websocket)

        if not self.active_connections[job_id]:
            del self.active_connections[job_id]

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected WebSockets."""
        all_sockets = []
        for job_sockets in self.active_connections.values():
            all_sockets.extend(job_sockets)

        disconnected = set()

        for websocket in all_sockets:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for job_id, job_sockets in self.active_connections.items():
            for websocket in disconnected:
                job_sockets.discard(websocket)

            if not job_sockets:
                del self.active_connections[job_id]

    async def get_connection_count(self, job_id: str) -> int:
        """Get the number of active connections for a job."""
        return len(self.active_connections.get(job_id, set()))

    async def get_total_connections(self) -> int:
        """Get the total number of active connections across all jobs."""
        return sum(len(sockets) for sockets in self.active_connections.values())
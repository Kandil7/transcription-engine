"""Real-time streaming transcription service."""

import asyncio
import io
import time
from typing import AsyncGenerator, Dict, Optional

import numpy as np
from faster_whisper import WhisperModel
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


class StreamingTranscriptionService:
    """Service for real-time streaming transcription."""

    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self.model_loaded = False
        self.active_streams: Dict[str, Dict] = {}

    async def load_model(self) -> None:
        """Load the Whisper model for streaming."""
        if self.model_loaded:
            return

        try:
            logger.info("Loading streaming Whisper model")

            # Use a smaller model for streaming to reduce latency
            model_size = "base"  # Smaller model for faster streaming
            if settings.detected_profile.value == "ultra":
                model_size = "small"  # Still relatively fast but more accurate

            self.model = WhisperModel(
                model_size,
                device="cuda" if settings.gpu_memory_gb > 0 else "cpu",
                compute_type="float16" if settings.gpu_memory_gb > 0 else "int8",
            )

            self.model_loaded = True
            logger.info("Streaming model loaded successfully", model_size=model_size)

        except Exception as e:
            logger.error("Failed to load streaming model", error=str(e))
            raise

    async def start_stream(self, stream_id: str, language: str = "ar") -> None:
        """Start a new streaming session."""
        await self.load_model()

        self.active_streams[stream_id] = {
            "language": language,
            "audio_buffer": b"",
            "last_segment_time": time.time(),
            "segments": [],
            "is_active": True,
        }

        logger.info("Streaming session started", stream_id=stream_id, language=language)

    async def process_audio_chunk(self, stream_id: str, audio_chunk: bytes) -> AsyncGenerator[Dict, None]:
        """
        Process an audio chunk and yield transcription results in real-time.

        Args:
            stream_id: Unique stream identifier
            audio_chunk: Raw audio data (WAV format)

        Yields:
            Dict with transcription results
        """
        if stream_id not in self.active_streams:
            raise ValueError(f"Stream {stream_id} not found")

        stream_data = self.active_streams[stream_id]
        if not stream_data["is_active"]:
            return

        # Accumulate audio data
        stream_data["audio_buffer"] += audio_chunk

        # Process when we have enough data (every 2 seconds worth of audio)
        current_time = time.time()
        if current_time - stream_data["last_segment_time"] >= 2.0:
            try:
                # Convert audio buffer to temporary file-like object
                audio_data = io.BytesIO(stream_data["audio_buffer"])

                # Transcribe the accumulated audio
                segments, info = self.model.transcribe(
                    audio_data,
                    language=stream_data["language"] if stream_data["language"] != "auto" else None,
                    beam_size=1,  # Faster for streaming
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=300),
                    without_timestamps=False,
                )

                # Process new segments
                new_segments = []
                for segment in segments:
                    # Check if this is a new segment (not already processed)
                    segment_key = f"{segment.start:.2f}-{segment.end:.2f}"
                    if segment_key not in [s["key"] for s in stream_data["segments"]]:
                        segment_dict = {
                            "key": segment_key,
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text.strip(),
                            "confidence": getattr(segment, 'confidence', None),
                            "timestamp": current_time,
                        }

                        new_segments.append(segment_dict)
                        stream_data["segments"].append(segment_dict)

                        # Yield the segment immediately
                        yield {
                            "type": "transcription_chunk",
                            "stream_id": stream_id,
                            "segment": segment_dict,
                            "detected_language": info.language if hasattr(info, 'language') else stream_data["language"],
                        }

                # Update last processing time
                stream_data["last_segment_time"] = current_time

                # Clear buffer periodically to prevent memory buildup
                if len(stream_data["audio_buffer"]) > 1024 * 1024:  # 1MB
                    stream_data["audio_buffer"] = stream_data["audio_buffer"][-512 * 1024:]  # Keep last 512KB

            except Exception as e:
                logger.error("Streaming processing error", stream_id=stream_id, error=str(e))
                yield {
                    "type": "error",
                    "stream_id": stream_id,
                    "message": f"Processing error: {str(e)}",
                }

    async def end_stream(self, stream_id: str) -> Dict:
        """
        End a streaming session and return final results.

        Args:
            stream_id: Stream identifier

        Returns:
            Final transcription results
        """
        if stream_id not in self.active_streams:
            raise ValueError(f"Stream {stream_id} not found")

        stream_data = self.active_streams[stream_id]
        stream_data["is_active"] = False

        # Compile final transcript
        full_transcript = " ".join([seg["text"] for seg in stream_data["segments"]])

        # Calculate statistics
        total_duration = 0
        if stream_data["segments"]:
            total_duration = stream_data["segments"][-1]["end"] - stream_data["segments"][0]["start"]

        result = {
            "stream_id": stream_id,
            "full_transcript": full_transcript,
            "segments": stream_data["segments"],
            "total_segments": len(stream_data["segments"]),
            "total_duration_seconds": total_duration,
            "language": stream_data["language"],
            "completed_at": time.time(),
        }

        # Clean up
        del self.active_streams[stream_id]

        logger.info("Streaming session ended", stream_id=stream_id, segments=len(stream_data["segments"]))
        return result

    async def get_stream_status(self, stream_id: str) -> Dict:
        """Get status of a streaming session."""
        if stream_id not in self.active_streams:
            return {"status": "not_found", "stream_id": stream_id}

        stream_data = self.active_streams[stream_id]
        return {
            "stream_id": stream_id,
            "status": "active" if stream_data["is_active"] else "ended",
            "language": stream_data["language"],
            "segments_processed": len(stream_data["segments"]),
            "buffer_size": len(stream_data["audio_buffer"]),
            "last_activity": stream_data["last_segment_time"],
        }

    def list_active_streams(self) -> list:
        """List all active streaming sessions."""
        return [
            {
                "stream_id": stream_id,
                "language": data["language"],
                "segments": len(data["segments"]),
                "last_activity": data["last_segment_time"],
            }
            for stream_id, data in self.active_streams.items()
            if data["is_active"]
        ]


# Global streaming service instance
streaming_service = StreamingTranscriptionService()
"""Voice analytics endpoints for speaker diarization and emotion detection."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from structlog import get_logger

from app.services.job_service import get_job
from app.services.voice_analytics_service import voice_analytics_service

logger = get_logger(__name__)
router = APIRouter()


class SpeakerSegment(BaseModel):
    """Speaker segment model."""

    speaker: str
    start: float
    end: float
    duration: float
    emotion: str = "neutral"
    confidence: float = 0.0


class MeetingAnalysis(BaseModel):
    """Meeting analysis model."""

    total_duration: float
    total_speakers: int
    dominant_speaker: str = None
    meeting_balance_score: float
    speaker_stats: dict


class VoiceAnalyticsResponse(BaseModel):
    """Voice analytics response model."""

    job_id: str
    speaker_segments: List[SpeakerSegment]
    meeting_analysis: MeetingAnalysis
    model_status: dict


@router.post("/{job_id}/analyze", response_model=VoiceAnalyticsResponse)
async def analyze_voice(job_id: str) -> VoiceAnalyticsResponse:
    """
    Perform voice analytics (speaker diarization and emotion detection) on a job.

    - **job_id**: Unique job identifier
    """
    try:
        # Validate job exists and is completed
        job = await get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        if job.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is not completed. Current status: {job.status}"
            )

        if not job.file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No audio file available for voice analysis"
            )

        logger.info("Starting voice analytics", job_id=job_id)

        # Perform speaker diarization
        diarization_segments = await voice_analytics_service.perform_diarization(job.file_path)

        # Analyze emotions
        enhanced_segments = await voice_analytics_service.analyze_emotions(
            job.file_path,
            diarization_segments
        )

        # Analyze meeting dynamics
        meeting_analysis = await voice_analytics_service.analyze_meeting_dynamics(
            enhanced_segments
        )

        # Convert to response models
        speaker_segments = [
            SpeakerSegment(
                speaker=seg["speaker"],
                start=seg["start"],
                end=seg["end"],
                duration=seg["duration"],
                emotion=seg.get("emotion", "neutral"),
                confidence=seg.get("confidence", 0.0)
            )
            for seg in enhanced_segments
        ]

        meeting_analysis_model = MeetingAnalysis(
            total_duration=meeting_analysis.get("total_duration", 0),
            total_speakers=meeting_analysis.get("total_speakers", 0),
            dominant_speaker=meeting_analysis.get("dominant_speaker"),
            meeting_balance_score=meeting_analysis.get("meeting_balance_score", 0),
            speaker_stats=meeting_analysis.get("speaker_stats", {})
        )

        model_status = voice_analytics_service.get_model_status()

        logger.info(
            "Voice analytics completed",
            job_id=job_id,
            speakers_found=len(set(s.speaker for s in speaker_segments))
        )

        return VoiceAnalyticsResponse(
            job_id=job_id,
            speaker_segments=speaker_segments,
            meeting_analysis=meeting_analysis_model,
            model_status=model_status
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Voice analytics failed", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice analytics failed: {str(e)}"
        )


@router.get("/{job_id}/speakers", response_model=List[SpeakerSegment])
async def get_speaker_segments(job_id: str) -> List[SpeakerSegment]:
    """
    Get speaker segments for a job (requires prior voice analysis).

    - **job_id**: Unique job identifier
    """
    try:
        # For now, this would need to be stored in the database
        # In a full implementation, you'd store voice analytics results

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Speaker segments retrieval not yet implemented. Use /analyze endpoint first."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get speaker segments", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve speaker segments"
        )


@router.get("/models/status")
async def get_models_status():
    """
    Get the status of voice analytics models.
    """
    try:
        status = voice_analytics_service.get_model_status()
        return {
            "models": status,
            "message": "Voice analytics models status"
        }

    except Exception as e:
        logger.error("Failed to get models status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get models status"
        )
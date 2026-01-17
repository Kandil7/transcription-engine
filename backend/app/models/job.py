"""Job models for transcription tasks."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Enumeration of possible job statuses."""

    PENDING = "pending"
    DOWNLOADING = "downloading"  # For URL-based uploads
    PREPROCESSING = "preprocessing"
    TRANSCRIBING = "transcribing"
    RAG_PROCESSING = "rag_processing"
    TRANSLATING = "translating"
    SUMMARIZING = "summarizing"
    TTS_PROCESSING = "tts_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreate(BaseModel):
    """Model for creating a new transcription job."""

    id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path or URL to the file")
    file_size: int = Field(..., description="File size in bytes")
    duration: float = Field(..., description="Audio duration in seconds")
    language: str = Field("ar", description="Source language code")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    enable_translation: bool = Field(True, description="Whether to translate the content")
    enable_summary: bool = Field(True, description="Whether to generate a summary")
    enable_voice_analytics: bool = Field(False, description="Whether to perform voice analytics")
    target_language: Optional[str] = Field("en", description="Target language for translation")
    summary_length: Optional[str] = Field("medium", description="Summary length (short/medium/long)")
    text_sample: Optional[str] = Field(None, description="Sample text for dialect detection (Arabic only)")


class JobUpdate(BaseModel):
    """Model for updating an existing job."""

    status: Optional[JobStatus] = None
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    message: Optional[str] = None
    transcript: Optional[str] = None
    translation: Optional[str] = None
    summary: Optional[str] = None
    processing_stats: Optional[dict] = None


class Job(BaseModel):
    """Complete job model with all fields."""

    id: str
    filename: str
    file_path: str
    file_size: int
    duration: float
    language: str
    status: JobStatus
    progress: Optional[float] = None
    message: Optional[str] = None

    # Processing options
    enable_translation: bool
    enable_summary: bool
    target_language: Optional[str] = None
    summary_length: Optional[str] = None
    text_sample: Optional[str] = None

    # Results
    transcript: Optional[str] = None
    translation: Optional[str] = None
    summary: Optional[str] = None
    hierarchical_summary: Optional[dict] = None
    voice_analytics: Optional[dict] = None
    subtitles_srt: Optional[str] = None
    subtitles_vtt: Optional[str] = None
    audio_summary_url: Optional[str] = None

    # Metadata
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Processing statistics
    processing_stats: Optional[dict] = None

    # Hardware info
    processing_profile: Optional[str] = None
    gpu_used: Optional[bool] = None

    class Config:
        from_attributes = True


class ProcessingStats(BaseModel):
    """Statistics for job processing."""

    transcription_time_seconds: Optional[float] = None
    translation_time_seconds: Optional[float] = None
    summary_time_seconds: Optional[float] = None
    tts_time_seconds: Optional[float] = None
    total_time_seconds: Optional[float] = None

    # Quality metrics
    wer_score: Optional[float] = None  # Word Error Rate
    confidence_score: Optional[float] = None

    # Resource usage
    peak_memory_mb: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

    # Audio processing
    chunks_processed: Optional[int] = None
    total_chunks: Optional[int] = None
    audio_sample_rate: Optional[int] = None
    audio_channels: Optional[int] = None

    # Model info
    whisper_model_used: Optional[str] = None
    translation_model_used: Optional[str] = None
    summary_model_used: Optional[str] = None
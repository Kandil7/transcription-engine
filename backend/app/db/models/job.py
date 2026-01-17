"""Database models for jobs."""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func, JSON

from app.db.session import Base


class Job(Base):
    """Database model for transcription jobs."""

    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)
    language = Column(String(10), nullable=False, default="ar")
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Float, nullable=True)

    # Processing options
    enable_translation = Column(Boolean, default=True)
    enable_summary = Column(Boolean, default=True)
    target_language = Column(String(10), nullable=True)
    summary_length = Column(String(20), nullable=True)

    # Results
    transcript = Column(Text, nullable=True)
    translation = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    hierarchical_summary = Column(JSON, nullable=True)
    subtitles_srt = Column(Text, nullable=True)
    subtitles_vtt = Column(Text, nullable=True)
    audio_summary_url = Column(Text, nullable=True)

    # Messages and errors
    message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Processing statistics (stored as JSON)
    processing_stats = Column(JSON, nullable=True)

    # Hardware info
    processing_profile = Column(String(20), nullable=True)
    gpu_used = Column(Boolean, nullable=True)
"""Configuration settings for the Transcription Engine."""

import os
from enum import Enum
from typing import Optional

from pydantic import BaseSettings, Field


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class HardwareProfile(str, Enum):
    ULTRA = "ultra"        # RTX 4090/A100, VRAM >= 20GB
    STD_GPU = "std_gpu"    # RTX 3060-4070, VRAM 8-12GB
    CPU_STRONG = "cpu_strong"  # Strong CPU, no GPU
    EDGE_WEAK = "edge_weak"    # Mobile/weak devices


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Basic settings
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    project_name: str = "Transcription Engine"
    version: str = "1.0.0"
    api_v1_str: str = "/api/v1"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = Field(default="postgresql://postgres:password@localhost:5432/transcription_db", env="DATABASE_URL")

    # Redis/Celery
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")

    # Storage
    storage_type: str = Field(default="local", env="STORAGE_TYPE")  # local, s3, minio
    upload_dir: str = Field(default="/tmp/uploads", env="UPLOAD_DIR")
    processed_dir: str = Field(default="/tmp/processed", env="PROCESSED_DIR")

    # MinIO/S3 settings
    minio_endpoint: Optional[str] = Field(default=None, env="MINIO_ENDPOINT")
    minio_access_key: Optional[str] = Field(default=None, env="MINIO_ACCESS_KEY")
    minio_secret_key: Optional[str] = Field(default=None, env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=True, env="MINIO_SECURE")
    minio_bucket: str = Field(default="transcription", env="MINIO_BUCKET")
    minio_bucket: str = "transcription-engine"

    # AWS S3 (alternative to MinIO)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket: str = "transcription-engine"

    # Vector Database
    vector_db_url: str = Field(default="http://localhost:8001")
    vector_db_collection: str = "transcription_embeddings"

    # AI Models
    whisper_model_size: str = Field(default="large-v3", env="WHISPER_MODEL_SIZE")
    translation_model: str = Field(default="facebook/nllb-200-distilled-600M", env="TRANSLATION_MODEL")
    summarization_model: str = Field(default="facebook/bart-large-cnn", env="SUMMARIZATION_MODEL")
    embedding_model: str = Field(default="aubmindlab/bert-base-arabertv02", env="EMBEDDING_MODEL")

    # Hardware detection and profiles
    detected_profile: HardwareProfile = HardwareProfile.CPU_STRONG
    gpu_memory_gb: float = 0.0
    cpu_cores: int = 1
    ram_gb: float = 4.0

    # Processing limits
    max_file_size_mb: int = Field(default=500, env="MAX_FILE_SIZE_MB")  # 500MB max file size
    max_duration_hours: int = Field(default=4, env="MAX_DURATION_HOURS")  # 4 hours max duration
    chunk_size_seconds: int = Field(default=300, env="CHUNK_SIZE_SECONDS")  # 5 minutes default chunk
    chunk_overlap_seconds: int = Field(default=2, env="CHUNK_OVERLAP_SECONDS")  # 2 seconds overlap

    # Monitoring & Logging
    enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")

    # Performance tuning per profile
    profile_configs: dict = Field(default_factory=lambda: {
        HardwareProfile.ULTRA: {
            "whisper_model": "large-v3",
            "beam_size": 5,
            "batch_size": 16,
            "compute_type": "float16",
            "enable_rag": True,
            "enable_diarization": True,
            "enable_tts": True,
        },
        HardwareProfile.STD_GPU: {
            "whisper_model": "medium",
            "beam_size": 3,
            "batch_size": 8,
            "compute_type": "float16",
            "enable_rag": True,
            "enable_diarization": False,
            "enable_tts": False,
        },
        HardwareProfile.CPU_STRONG: {
            "whisper_model": "small",
            "beam_size": 1,
            "batch_size": 1,
            "compute_type": "int8",
            "enable_rag": False,
            "enable_diarization": False,
            "enable_tts": False,
        },
        HardwareProfile.EDGE_WEAK: {
            "whisper_model": "tiny",
            "beam_size": 1,
            "batch_size": 1,
            "compute_type": "int8",
            "enable_rag": False,
            "enable_diarization": False,
            "enable_tts": False,
        }
    })

    # Monitoring
    enable_prometheus: bool = True
    enable_opentelemetry: bool = True
    log_level: str = "INFO"

    # Feature flags
    enable_streaming: bool = False
    enable_rag: bool = True
    enable_translation: bool = True
    enable_summarization: bool = Field(default=True, env="ENABLE_SUMMARIZATION")
    enable_tts: bool = Field(default=False, env="ENABLE_TTS")
    enable_voice_analytics: bool = Field(default=False, env="ENABLE_VOICE_ANALYTICS")

    # TTS settings
    tts_engine: str = Field(default="edge-tts", env="TTS_ENGINE")  # "edge-tts" or "coqui"
    tts_voice: str = Field(default="ar-EG-SalmaNeural", env="TTS_VOICE")  # Arabic voice for edge-tts

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def detect_hardware_profile() -> HardwareProfile:
    """Auto-detect hardware capabilities and return appropriate profile."""
    try:
        import torch

        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            if device_count > 0:
                # Get VRAM of primary GPU
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                settings.gpu_memory_gb = vram_gb

                if vram_gb >= 20:
                    return HardwareProfile.ULTRA
                elif vram_gb >= 8:
                    return HardwareProfile.STD_GPU
                else:
                    return HardwareProfile.EDGE_WEAK
        else:
            # CPU-only system
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            settings.cpu_cores = cpu_count

            if cpu_count >= 8:
                return HardwareProfile.CPU_STRONG
            else:
                return HardwareProfile.EDGE_WEAK

    except ImportError:
        # Fallback if torch not available
        return HardwareProfile.EDGE_WEAK

    return HardwareProfile.CPU_STRONG


# Update detected profile
settings.detected_profile = detect_hardware_profile()
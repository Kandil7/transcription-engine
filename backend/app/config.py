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
    database_url: str = Field(default="postgresql://postgres:password@localhost:5432/transcription_db")

    # Redis/Celery
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/0")

    # Storage
    storage_type: str = Field(default="local")  # local, s3, minio
    upload_dir: str = "/tmp/uploads"
    processed_dir: str = "/tmp/processed"

    # MinIO/S3 settings
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None
    minio_secure: bool = True
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
    whisper_model_size: str = "large-v3"
    translation_model: str = "facebook/nllb-200-distilled-600M"
    summarization_model: str = "facebook/bart-large-cnn"
    embedding_model: str = "aubmindlab/bert-base-arabertv02"

    # Hardware detection and profiles
    detected_profile: HardwareProfile = HardwareProfile.CPU_STRONG
    gpu_memory_gb: float = 0.0
    cpu_cores: int = 1
    ram_gb: float = 4.0

    # Processing limits
    max_file_size_mb: int = 500  # 500MB max file size
    max_duration_hours: int = 4  # 4 hours max duration
    chunk_size_seconds: int = 300  # 5 minutes default chunk
    chunk_overlap_seconds: int = 2  # 2 seconds overlap

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
    enable_summarization: bool = True
    enable_tts: bool = False
    enable_voice_analytics: bool = False

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
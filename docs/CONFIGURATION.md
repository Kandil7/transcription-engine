# Configuration Guide

Comprehensive configuration reference for the SoutiAI Transcription Engine.

## Overview

The Transcription Engine uses a hierarchical configuration system with environment variables, configuration files, and runtime detection. Configuration is managed through Pydantic models for validation and type safety.

## Configuration Hierarchy

Configuration is loaded in this order (later sources override earlier ones):

1. **Default values** in code
2. **Environment variables** (.env file)
3. **Runtime detection** (hardware profiles)
4. **Command-line arguments** (for scripts)

## Environment Variables

### Core Application Settings

```bash
# Application
APP_NAME=TranscriptionEngine
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]
```

### Database Configuration

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/transcription_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_ECHO=false

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20
REDIS_DB_CACHE=1
REDIS_DB_QUEUE=2

# ChromaDB (Vector Database)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIR=./data/chroma
```

### Storage Configuration

```bash
# MinIO/S3
STORAGE_TYPE=minio  # or 's3' or 'local'
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_NAME=transcription-files

# S3 (Alternative)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=transcription-files

# Local Storage
LOCAL_STORAGE_PATH=./data/files
```

### AI Model Configuration

```bash
# Hardware Detection
DETECTED_PROFILE=auto  # or 'ULTRA', 'STD_GPU', 'CPU_STRONG', 'EDGE_WEAK'

# Whisper Models
WHISPER_MODEL_SIZE=large-v3
WHISPER_COMPUTE_TYPE=float16
WHISPER_BEAM_SIZE=5
WHISPER_VAD_FILTER=true
WHISPER_VAD_MIN_SILENCE=500

# Egyptian Dialect Models
EGYPTIAN_DIALECT_MODELS_PATH=./models/egyptian
DIALECT_DETECTOR_PATH=./models/dialect_detector
ENABLE_DIALECT_DETECTION=true

# Translation Models
TRANSLATION_MODEL=nllb-200-distilled-600M
TRANSLATION_CACHE_SIZE=10000
TRANSLATION_MAX_LENGTH=512

# Summarization Models
SUMMARIZATION_MODEL=bart-large-cnn
SUMMARIZATION_MAX_LENGTH=150
SUMMARIZATION_MIN_LENGTH=50

# Voice Analytics
VOICE_ANALYTICS_ENABLED=true
DIARIZATION_MODEL=pyannote/speaker-diarization
EMOTION_MODEL=wav2vec2-large-robust-12-ft-emotion-msp-dim
```

### Queue & Background Processing

```bash
# Celery
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=['json']
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC

# Worker Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# Queue Names
CELERY_DEFAULT_QUEUE=transcription
CELERY_HIGH_PRIORITY_QUEUE=urgent
```

### Security Configuration

```bash
# JWT Authentication
JWT_SECRET_KEY=your-256-bit-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# API Keys (for service authentication)
API_KEY_HEADER=X-API-Key
API_KEYS=your-api-key-1,your-api-key-2

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds
RATE_LIMIT_BURST=20

# Encryption
ENCRYPTION_KEY=your-32-byte-encryption-key
ENCRYPTION_ALGORITHM=AES256
```

### Monitoring & Observability

```bash
# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
METRICS_PATH=/metrics

# Logging
LOG_FORMAT=json
LOG_FILE=./logs/transcription.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5

# Sentry (Error Tracking)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production

# Health Checks
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_DATABASE=true
HEALTH_CHECK_REDIS=true
HEALTH_CHECK_MODELS=true
```

### Feature Flags

```bash
# Enable/Disable Features
ENABLE_RAG=true
ENABLE_VOICE_ANALYTICS=true
ENABLE_STREAMING=true
ENABLE_TRANSLATION=true
ENABLE_SUMMARIZATION=true
ENABLE_DIALECT_DETECTION=true

# Experimental Features
ENABLE_EXPERIMENTAL_MODELS=false
ENABLE_MODEL_AUTO_UPDATE=false
ENABLE_ADVANCED_ANALYTICS=false
```

## Hardware Profiles

The system automatically detects and configures for different hardware profiles:

### ULTRA Profile (High-end GPU)
```python
{
    "gpu_memory": "24GB+",
    "cpu_cores": "8+",
    "ram": "32GB+",
    "whisper_model": "large-v3",
    "batch_size": 8,
    "compute_type": "float16",
    "beam_size": 5
}
```

### STD_GPU Profile (Standard GPU)
```python
{
    "gpu_memory": "8GB+",
    "cpu_cores": "4+",
    "ram": "16GB+",
    "whisper_model": "large-v2",
    "batch_size": 4,
    "compute_type": "int8_float16",
    "beam_size": 5
}
```

### CPU_STRONG Profile (High-end CPU)
```python
{
    "gpu_memory": "0GB",
    "cpu_cores": "8+",
    "ram": "32GB+",
    "whisper_model": "medium",
    "batch_size": 2,
    "compute_type": "int8",
    "beam_size": 3
}
```

### EDGE_WEAK Profile (Low-end Hardware)
```python
{
    "gpu_memory": "0GB",
    "cpu_cores": "2+",
    "ram": "8GB+",
    "whisper_model": "base",
    "batch_size": 1,
    "compute_type": "int8",
    "beam_size": 1
}
```

## Configuration Files

### .env.example Template

```bash
# Application
APP_NAME=TranscriptionEngine
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/transcription_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage
STORAGE_TYPE=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# AI Models
DETECTED_PROFILE=auto
WHISPER_MODEL_SIZE=large-v3

# Security
JWT_SECRET_KEY=change-this-in-production-to-a-secure-random-key
ENCRYPTION_KEY=change-this-to-a-32-byte-encryption-key

# Feature Flags
ENABLE_RAG=true
ENABLE_VOICE_ANALYTICS=true
ENABLE_DIALECT_DETECTION=true
```

### Docker Compose Overrides

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  api:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - DETECTED_PROFILE=CPU_STRONG
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  celery_worker:
    environment:
      - CELERY_WORKER_CONCURRENCY=2
    deploy:
      replicas: 2
```

## Runtime Configuration

### Dynamic Profile Detection

The system automatically detects hardware and sets the optimal profile:

```python
def detect_hardware_profile() -> str:
    """Detect the best hardware profile for current system."""
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        if gpu_memory >= 24:
            return "ULTRA"
        elif gpu_memory >= 8:
            return "STD_GPU"
    else:
        cpu_count = os.cpu_count()
        memory_gb = psutil.virtual_memory().total / 1024**3

        if cpu_count >= 8 and memory_gb >= 32:
            return "CPU_STRONG"
        elif cpu_count >= 2 and memory_gb >= 8:
            return "EDGE_WEAK"

    return "EDGE_WEAK"  # fallback
```

### Model Auto-selection

Based on detected profile, models are automatically selected:

```python
profile_configs = {
    "ULTRA": {
        "whisper_model": "large-v3",
        "compute_type": "float16",
        "batch_size": 8,
        "beam_size": 5
    },
    "STD_GPU": {
        "whisper_model": "large-v2",
        "compute_type": "int8_float16",
        "batch_size": 4,
        "beam_size": 5
    },
    "CPU_STRONG": {
        "whisper_model": "medium",
        "compute_type": "int8",
        "batch_size": 2,
        "beam_size": 3
    },
    "EDGE_WEAK": {
        "whisper_model": "base",
        "compute_type": "int8",
        "batch_size": 1,
        "beam_size": 1
    }
}
```

## Configuration Validation

### Pydantic Models

All configuration is validated using Pydantic:

```python
from pydantic import BaseSettings, validator
from typing import List, Optional

class AppConfig(BaseSettings):
    """Application configuration with validation."""

    app_name: str = "TranscriptionEngine"
    debug: bool = False
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret key must be at least 32 characters')
        return v

    @validator('port')
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Environment-specific Configs

```python
# config.py
import os
from functools import lru_cache

@lru_cache()
def get_config() -> AppConfig:
    """Get cached configuration instance."""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return AppConfig(
            debug=False,
            log_level="WARNING",
            # Production-specific settings
        )
    elif env == "staging":
        return AppConfig(
            debug=False,
            log_level="INFO",
            # Staging-specific settings
        )
    else:  # development
        return AppConfig(
            debug=True,
            log_level="DEBUG",
            # Development-specific settings
        )
```

## Security Configuration

### Secret Management

```bash
# Use strong, random keys
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Never commit secrets to version control
echo ".env*" >> .gitignore
echo "secrets/" >> .gitignore

# Use environment-specific secrets
# production.env, staging.env, development.env
```

### Access Control

```python
# Role-based permissions
PERMISSIONS = {
    "admin": ["read", "write", "delete", "manage_users"],
    "user": ["read", "write"],
    "service": ["read", "write"],
    "viewer": ["read"]
}

# API endpoint permissions
ENDPOINT_PERMISSIONS = {
    "/api/v1/admin/*": ["admin"],
    "/api/v1/jobs": ["user", "admin"],
    "/api/v1/jobs/{job_id}": ["user", "admin"],
    "/api/v1/health": ["*"]
}
```

## Monitoring Configuration

### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Business metrics
JOBS_CREATED = Counter('jobs_created_total', 'Total jobs created')
JOBS_COMPLETED = Counter('jobs_completed_total', 'Total jobs completed')
TRANSCRIPTION_TIME = Histogram('transcription_duration_seconds', 'Transcription time')

# System metrics
GPU_MEMORY_USED = Gauge('gpu_memory_used_bytes', 'GPU memory used')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
```

### Alert Rules

```yaml
# monitoring/prometheus/rules.yml
groups:
- name: transcription_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"

  - alert: JobQueueBacklog
    expr: celery_queue_length > 100
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Job queue backlog detected"

  - alert: HighMemoryUsage
    expr: (1 - system_memory_available / system_memory_total) > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
```

## Feature Flag Configuration

### Runtime Feature Toggles

```python
# features.py
import os

class FeatureFlags:
    """Runtime feature flags."""

    def __init__(self):
        self._flags = {}

    def is_enabled(self, feature: str) -> bool:
        """Check if feature is enabled."""
        if feature not in self._flags:
            # Check environment variable
            env_var = f"ENABLE_{feature.upper()}"
            self._flags[feature] = os.getenv(env_var, "false").lower() == "true"

        return self._flags[feature]

    def enable(self, feature: str):
        """Enable a feature."""
        self._flags[feature] = True

    def disable(self, feature: str):
        """Disable a feature."""
        self._flags[feature] = False

# Global instance
features = FeatureFlags()

# Usage in code
if features.is_enabled("dialect_detection"):
    # Use dialect detection
    pass
```

## Configuration Best Practices

### Environment Separation

```bash
# Create separate config files
cp .env.example .env.development
cp .env.example .env.staging
cp .env.example .env.production

# Use different settings per environment
# development: debug logging, local services
# staging: production-like, separate databases
# production: optimized, secure settings
```

### Configuration Validation

```python
# Validate configuration on startup
def validate_config(config: AppConfig) -> List[str]:
    """Validate configuration and return errors."""
    errors = []

    # Check database connectivity
    try:
        # Test database connection
        pass
    except Exception as e:
        errors.append(f"Database connection failed: {e}")

    # Check Redis connectivity
    try:
        # Test Redis connection
        pass
    except Exception as e:
        errors.append(f"Redis connection failed: {e}")

    # Check required directories
    required_dirs = ["./logs", "./data"]
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")

    return errors
```

### Configuration Documentation

```python
def generate_config_docs() -> str:
    """Generate configuration documentation."""
    docs = []
    docs.append("# Configuration Reference\n")

    for field_name, field in AppConfig.__fields__.items():
        docs.append(f"## {field_name}\n")
        docs.append(f"- **Type**: {field.type_}\n")
        docs.append(f"- **Default**: {field.default}\n")
        docs.append(f"- **Required**: {'Yes' if field.is_required() else 'No'}\n")

        if field.field_info.description:
            docs.append(f"- **Description**: {field.field_info.description}\n")

        docs.append("\n")

    return "\n".join(docs)
```

## Troubleshooting Configuration Issues

### Common Configuration Problems

1. **Database Connection Issues**
   ```bash
   # Test database connection
   python -c "from app.db.session import get_db; next(get_db())"

   # Check environment variables
   echo $DATABASE_URL
   ```

2. **Redis Connection Issues**
   ```bash
   # Test Redis connection
   redis-cli ping

   # Check Redis configuration
   redis-cli config get *
   ```

3. **Model Loading Issues**
   ```bash
   # Check model paths
   ls -la models/

   # Test model loading
   python -c "from app.services.transcription_service import transcription_service; transcription_service.load_model()"
   ```

4. **Permission Issues**
   ```bash
   # Check file permissions
   ls -la data/
   ls -la logs/

   # Fix permissions
   chmod 755 data/
   chmod 755 logs/
   ```

### Configuration Debugging

```python
# Debug configuration loading
import logging
logging.basicConfig(level=logging.DEBUG)

from app.config import get_config

try:
    config = get_config()
    print("Configuration loaded successfully")
    print(f"Database URL: {config.database_url}")
    print(f"Debug mode: {config.debug}")
except Exception as e:
    print(f"Configuration error: {e}")
    import traceback
    traceback.print_exc()
```

This comprehensive configuration system ensures the Transcription Engine can be deployed and scaled across different environments while maintaining security, performance, and reliability.</content>
</xai:function_call">CONFIGURATION.md
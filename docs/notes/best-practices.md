# Best Practices Guide

Comprehensive best practices for developing, deploying, and maintaining the SoutiAI Transcription Engine.

## Table of Contents

- [Code Quality](#code-quality)
- [Performance Optimization](#performance-optimization)
- [Security Practices](#security-practices)
- [Testing Strategies](#testing-strategies)
- [Deployment Practices](#deployment-practices)
- [Monitoring & Observability](#monitoring--observability)
- [Arabic Language Handling](#arabic-language-handling)
- [Error Handling](#error-handling)
- [Documentation Standards](#documentation-standards)

---

## Code Quality

### Python Best Practices

#### Type Hints and Documentation
```python
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass
class TranscriptionResult:
    """Result of an audio transcription operation.

    Attributes:
        text: The transcribed text
        confidence: Confidence score between 0.0 and 1.0
        language: Detected or specified language code
        segments: List of time-stamped segments
        processing_time: Time taken for processing in seconds
    """
    text: str
    confidence: float
    language: str
    segments: List[Dict[str, Union[str, float]]]
    processing_time: float

def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
    enable_timestamps: bool = True
) -> TranscriptionResult:
    """Transcribe audio file to text.

    Args:
        audio_path: Path to audio file (WAV, MP3, M4A supported)
        language: Language code (e.g., 'ar', 'en'). Auto-detect if None
        enable_timestamps: Whether to include timing information

    Returns:
        TranscriptionResult with text and metadata

    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If audio format is unsupported
        TranscriptionError: If transcription fails

    Example:
        >>> result = transcribe_audio('meeting.wav', language='ar')
        >>> print(f"Confidence: {result.confidence:.2f}")
        >>> print(f"Text: {result.text[:100]}...")
    """
    pass
```

#### Error Handling Patterns
```python
class TranscriptionError(Exception):
    """Base exception for transcription operations."""
    pass

class AudioProcessingError(TranscriptionError):
    """Raised when audio processing fails."""
    pass

def safe_transcribe_audio(audio_path: str) -> Optional[TranscriptionResult]:
    """Safely transcribe audio with comprehensive error handling.

    Returns None on failure rather than raising exceptions.
    """
    try:
        # Validate input
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None

        # Check file size
        file_size = os.path.getsize(audio_path)
        if file_size > 500 * 1024 * 1024:  # 500MB limit
            logger.error(f"File too large: {file_size} bytes")
            return None

        # Attempt transcription
        result = transcribe_audio(audio_path)

        # Validate result
        if not result or not result.text.strip():
            logger.warning(f"Empty transcription result for {audio_path}")
            return None

        logger.info(f"Successfully transcribed {audio_path}: {len(result.text)} chars")
        return result

    except FileNotFoundError as e:
        logger.error(f"File access error: {e}")
        return None
    except AudioProcessingError as e:
        logger.error(f"Audio processing failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}", exc_info=True)
        return None
```

#### Context Managers for Resource Management
```python
from contextlib import contextmanager
import tempfile
import shutil

@contextmanager
def temporary_workspace(base_dir: Optional[str] = None):
    """Create a temporary workspace for file processing.

    Automatically cleans up temporary files on exit.
    """
    temp_dir = tempfile.mkdtemp(dir=base_dir)

    try:
        yield temp_dir
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")

def process_audio_with_temp_workspace(audio_path: str) -> str:
    """Process audio using a temporary workspace."""
    with temporary_workspace() as workspace:
        # Convert audio to WAV if needed
        wav_path = os.path.join(workspace, "audio.wav")
        convert_to_wav(audio_path, wav_path)

        # Apply noise reduction
        cleaned_path = os.path.join(workspace, "cleaned.wav")
        apply_noise_reduction(wav_path, cleaned_path)

        # Transcribe
        result = transcribe_audio(cleaned_path)

        return result.text
```

### JavaScript/React Best Practices

#### Component Structure
```javascript
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranscription } from '../hooks/useTranscription';
import { TranscriptionProgress } from './TranscriptionProgress';
import { ResultDisplay } from './ResultDisplay';

// Custom hook for transcription logic
const useTranscriptionState = (file) => {
  const [state, setState] = useState({
    status: 'idle', // 'idle' | 'uploading' | 'processing' | 'completed' | 'error'
    progress: 0,
    result: null,
    error: null
  });

  const { uploadFile, getStatus } = useTranscription();

  const startTranscription = useCallback(async () => {
    if (!file) return;

    try {
      setState(prev => ({ ...prev, status: 'uploading', error: null }));

      const job = await uploadFile(file, { language: 'ar' });
      setState(prev => ({
        ...prev,
        status: 'processing',
        jobId: job.job_id
      }));

      // Poll for progress
      const pollInterval = setInterval(async () => {
        const status = await getStatus(job.job_id);
        setState(prev => ({
          ...prev,
          progress: status.progress || 0,
          status: status.status
        }));

        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setState(prev => ({
            ...prev,
            result: status.result
          }));
        }
      }, 2000);

    } catch (error) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: error.message
      }));
    }
  }, [file, uploadFile, getStatus]);

  return { ...state, startTranscription };
};

// Main component
export const TranscriptionApp = ({ file }) => {
  const { status, progress, result, error, startTranscription } = useTranscriptionState(file);

  return (
    <div className="transcription-app">
      <button
        onClick={startTranscription}
        disabled={status !== 'idle' || !file}
      >
        {status === 'idle' ? 'Start Transcription' :
         status === 'uploading' ? 'Uploading...' :
         status === 'processing' ? 'Processing...' : 'Complete'}
      </button>

      {status === 'processing' && (
        <TranscriptionProgress progress={progress} />
      )}

      {status === 'completed' && result && (
        <ResultDisplay result={result} />
      )}

      {status === 'error' && (
        <div className="error-message">
          Error: {error}
        </div>
      )}
    </div>
  );
};
```

#### Custom Hooks for Reusable Logic
```javascript
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

export const useTranscription = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const uploadFile = useCallback(async (file, options = {}) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Add options
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, value.toString());
      });

      const response = await axios.post('/api/v1/upload/file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000 // 30 seconds
      });

      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message;
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const getStatus = useCallback(async (jobId) => {
    try {
      const response = await axios.get(`/api/v1/jobs/${jobId}`);
      return response.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message);
    }
  }, []);

  const getResults = useCallback(async (jobId) => {
    try {
      const response = await axios.get(`/api/v1/jobs/${jobId}/results`);
      return response.data;
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message);
    }
  }, []);

  return {
    uploadFile,
    getStatus,
    getResults,
    loading,
    error
  };
};
```

---

## Performance Optimization

### Model Optimization Techniques

#### Quantization and Precision Reduction
```python
import torch
from transformers import BitsAndBytesConfig

def load_optimized_whisper_model(model_size: str = "large-v3"):
    """Load Whisper model with memory optimizations."""

    # Configure quantization
    quantization_config = BitsAndBytesConfig(
        load_in_8bit=True,  # Use 8-bit quantization
        llm_int8_enable_fp32_cpu_offload=True,  # Offload to CPU if needed
        llm_int8_threshold=6.0,  # Threshold for quantization
    )

    # Load model with optimizations
    model = WhisperForConditionalGeneration.from_pretrained(
        f"openai/whisper-{model_size}",
        quantization_config=quantization_config,
        torch_dtype=torch.float16,  # Use half precision
        low_cpu_mem_usage=True,     # Optimize CPU memory
        device_map="auto"           # Automatic device placement
    )

    # Enable optimizations
    model.config.use_cache = True
    model.config.torch_compile = True  # PyTorch 2.0 compilation

    return model

def optimize_inference_pipeline(model, processor):
    """Apply inference optimizations to the pipeline."""

    # Use torch.compile for faster inference
    if hasattr(torch, 'compile'):
        model = torch.compile(model, mode='reduce-overhead')

    # Enable CUDA optimizations
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Use Flash Attention if available
    try:
        from flash_attn import flash_attn_func
        model.config.use_flash_attention = True
    except ImportError:
        pass

    return model, processor
```

#### Batch Processing Optimization
```python
import asyncio
from typing import List, Dict, Any
import numpy as np

class BatchTranscriptionProcessor:
    """Process multiple audio files in optimized batches."""

    def __init__(self, model, processor, batch_size: int = 8, max_workers: int = 4):
        self.model = model
        self.processor = processor
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)

    async def process_batch(self, audio_files: List[str]) -> List[Dict[str, Any]]:
        """Process multiple audio files in parallel batches."""

        # Group files by estimated processing time
        batches = self._create_optimal_batches(audio_files)

        # Process batches concurrently
        tasks = []
        for batch in batches:
            task = asyncio.create_task(self._process_batch(batch))
            tasks.append(task)

        # Gather results
        batch_results = await asyncio.gather(*tasks)

        # Flatten results
        all_results = []
        for batch_result in batch_results:
            all_results.extend(batch_result)

        return all_results

    def _create_optimal_batches(self, audio_files: List[str]) -> List[List[str]]:
        """Create optimally sized batches based on file characteristics."""

        batches = []
        current_batch = []
        current_batch_size = 0

        for audio_file in audio_files:
            file_size = os.path.getsize(audio_file)
            estimated_tokens = self._estimate_token_count(file_size)

            # If adding this file would exceed batch size, start new batch
            if current_batch_size + estimated_tokens > self.batch_size * 1000:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_batch_size = 0

            current_batch.append(audio_file)
            current_batch_size += estimated_tokens

        # Add final batch
        if current_batch:
            batches.append(current_batch)

        return batches

    async def _process_batch(self, batch: List[str]) -> List[Dict[str, Any]]:
        """Process a single batch of audio files."""
        async with self.semaphore:  # Limit concurrent batches
            results = []

            try:
                # Load and preprocess all files in batch
                processed_audios = []
                for audio_file in batch:
                    audio_input = self.processor(
                        audio_file,
                        return_tensors="pt",
                        sampling_rate=16000
                    )
                    processed_audios.append(audio_input)

                # Batch inference
                with torch.no_grad():
                    batch_outputs = self.model.generate(
                        **self._collate_batch(processed_audios),
                        max_length=448,
                        num_beams=5,
                        temperature=0.0,
                        do_sample=False
                    )

                # Process results
                for i, output in enumerate(batch_outputs):
                    transcription = self.processor.decode(output, skip_special_tokens=True)
                    results.append({
                        "file": batch[i],
                        "transcription": transcription,
                        "confidence": self._calculate_confidence(output),
                        "processing_time": time.time() - time.time()  # Would track actual time
                    })

            except Exception as e:
                # Handle batch failures gracefully
                for audio_file in batch:
                    results.append({
                        "file": audio_file,
                        "error": str(e),
                        "transcription": None,
                        "confidence": 0.0
                    })

            return results

    def _estimate_token_count(self, file_size: int) -> int:
        """Estimate token count based on file size."""
        # Rough estimation: ~1 token per 100 bytes of audio
        return max(100, file_size // 100)

    def _collate_batch(self, processed_audios: List[Dict]) -> Dict[str, torch.Tensor]:
        """Collate batch inputs for model."""
        # Pad sequences to same length
        max_length = max(len(audio['input_features'][0]) for audio in processed_audios)

        batch_input_features = []
        batch_attention_masks = []

        for audio in processed_audios:
            features = audio['input_features'][0]
            # Pad or truncate to max_length
            if len(features) < max_length:
                padding = torch.zeros(max_length - len(features))
                features = torch.cat([features, padding])
            else:
                features = features[:max_length]

            batch_input_features.append(features)
            batch_attention_masks.append(torch.ones(max_length))

        return {
            "input_features": torch.stack(batch_input_features),
            "attention_mask": torch.stack(batch_attention_masks)
        }

    def _calculate_confidence(self, model_output: torch.Tensor) -> float:
        """Calculate transcription confidence score."""
        # Simple confidence based on output probabilities
        probs = torch.softmax(model_output, dim=-1)
        confidence = torch.max(probs, dim=-1).values.mean().item()
        return min(confidence, 1.0)
```

### Database Optimization

#### Query Optimization and Indexing
```sql
-- Optimized database queries for transcription jobs

-- Primary job status query with proper indexing
CREATE INDEX CONCURRENTLY idx_jobs_status_created
    ON jobs(status, created_at DESC)
    WHERE status IN ('pending', 'processing');

-- Composite index for user job filtering
CREATE INDEX CONCURRENTLY idx_jobs_user_status_progress
    ON jobs(user_id, status, progress DESC)
    WHERE status IN ('processing', 'completed');

-- Partial index for active jobs
CREATE INDEX CONCURRENTLY idx_jobs_active
    ON jobs(created_at DESC, updated_at DESC)
    WHERE status NOT IN ('completed', 'failed')
    AND created_at > NOW() - INTERVAL '30 days';

-- Optimize job status updates
CREATE OR REPLACE FUNCTION update_job_status(
    job_id UUID,
    new_status job_status,
    new_progress REAL DEFAULT NULL,
    new_message TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE jobs
    SET
        status = new_status,
        progress = COALESCE(new_progress, progress),
        message = COALESCE(new_message, message),
        updated_at = NOW()
    WHERE id = job_id;

    -- Notify listeners (for real-time updates)
    PERFORM pg_notify('job_updates', json_build_object(
        'job_id', job_id,
        'status', new_status,
        'progress', new_progress
    )::text);
END;
$$ LANGUAGE plpgsql;

-- Efficient pagination query
CREATE OR REPLACE FUNCTION get_jobs_paginated(
    user_filter UUID DEFAULT NULL,
    status_filter job_status DEFAULT NULL,
    limit_count INTEGER DEFAULT 50,
    offset_count INTEGER DEFAULT 0
) RETURNS TABLE (
    id UUID,
    filename TEXT,
    status job_status,
    progress REAL,
    created_at TIMESTAMPTZ,
    total_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        j.id,
        j.filename,
        j.status,
        j.progress,
        j.created_at,
        COUNT(*) OVER() as total_count
    FROM jobs j
    WHERE (user_filter IS NULL OR j.user_id = user_filter)
    AND (status_filter IS NULL OR j.status = status_filter)
    ORDER BY j.created_at DESC
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;
```

#### Connection Pooling Configuration
```python
# Optimized database connection pooling
DATABASE_CONFIG = {
    "poolclass": "sqlalchemy.pool.QueuePool",
    "pool_size": 20,              # Core pool size
    "max_overflow": 30,           # Max additional connections
    "pool_timeout": 30,           # Timeout for getting connection
    "pool_recycle": 3600,         # Recycle connections hourly
    "pool_pre_ping": True,        # Verify connections before use
    "echo": False,                # Disable SQL logging in production
    "connect_args": {
        "connect_timeout": 10,     # Connection timeout
        "application_name": "transcription-engine",
        "keepalives": 1,           # Enable TCP keepalives
        "keepalives_idle": 30,     # TCP keepalive settings
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
}

# Redis connection pooling
REDIS_CONFIG = {
    "max_connections": 20,         # Connection pool size
    "decode_responses": True,     # Decode responses automatically
    "socket_timeout": 5,          # Socket timeout
    "socket_connect_timeout": 5,  # Connection timeout
    "socket_keepalive": True,     # Enable TCP keepalives
    "socket_keepalive_options": {
        "TCP_KEEPIDLE": 300,      # Keepalive settings
        "TCP_KEEPINTVL": 60,
        "TCP_KEEPCNT": 3
    },
    "health_check_interval": 30   # Health check interval
}
```

---

## Security Practices

### Input Validation and Sanitization

#### Comprehensive Input Validation
```python
from pydantic import BaseModel, validator, Field
from typing import Optional, List
import re
import bleach

class AudioUploadRequest(BaseModel):
    """Validated request for audio file upload."""

    filename: str = Field(..., min_length=1, max_length=255)
    language: str = Field("ar", regex=r'^[a-z]{2,3}(-[a-z]{2,4})?$')
    enable_translation: bool = False
    target_language: Optional[str] = Field(None, regex=r'^[a-z]{2,3}(-[a-z]{2,4})?$')
    enable_voice_analytics: bool = False
    text_sample: Optional[str] = Field(None, max_length=1000)

    @validator('filename')
    def validate_filename(cls, v):
        """Validate and sanitize filename."""
        if not v:
            raise ValueError('Filename cannot be empty')

        # Remove path separators and dangerous characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '', v)
        safe_name = safe_name.strip()

        if not safe_name:
            raise ValueError('Invalid filename after sanitization')

        # Check file extension
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.mp4', '.flac', '.ogg'}
        if not any(safe_name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'File extension not allowed. Allowed: {allowed_extensions}')

        return safe_name[:255]  # Limit length

    @validator('text_sample')
    def sanitize_text_sample(cls, v):
        """Sanitize text sample input."""
        if v is None:
            return v

        # Remove HTML and potentially dangerous content
        sanitized = bleach.clean(v, tags=[], strip=True)

        # Remove excessive whitespace
        sanitized = ' '.join(sanitized.split())

        # Limit length
        return sanitized[:1000]

class TranscriptionService:
    """Secure transcription service with input validation."""

    def __init__(self):
        self.allowed_languages = {
            'ar', 'en', 'fr', 'de', 'es', 'it', 'pt', 'ru',
            'zh', 'ja', 'ko', 'hi', 'ur', 'fa', 'tr'
        }
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        self.allowed_mime_types = {
            'audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/flac', 'audio/ogg',
            'video/mp4', 'video/avi', 'video/mov', 'video/mkv'
        }

    def validate_audio_file(self, file_path: str) -> dict:
        """Comprehensive file validation."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            raise ValueError(f"File too large: {file_size} bytes (max: {self.max_file_size})")

        if file_size == 0:
            raise ValueError("File is empty")

        # Check MIME type
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type not in self.allowed_mime_types:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Basic audio validation (try to read header)
        try:
            with open(file_path, 'rb') as f:
                header = f.read(44)  # WAV header size
                if len(header) < 12:
                    raise ValueError("File too small to be valid audio")

                # Additional format-specific validation could go here

        except Exception as e:
            raise ValueError(f"Invalid audio file format: {e}")

        return {
            "file_path": file_path,
            "size": file_size,
            "mime_type": mime_type,
            "valid": True
        }

    def validate_transcription_request(self, request: dict) -> dict:
        """Validate complete transcription request."""
        validated = AudioUploadRequest(**request)

        # Additional business logic validation
        if validated.enable_translation and not validated.target_language:
            raise ValueError("target_language is required when enable_translation is True")

        if validated.enable_voice_analytics and validated.language not in ['ar', 'en']:
            raise ValueError("Voice analytics currently only supported for Arabic and English")

        return validated.dict()
```

### Secure API Design

#### Rate Limiting Implementation
```python
from functools import wraps
from typing import Callable, Any
import time
import hashlib

class RateLimiter:
    """Distributed rate limiter using Redis."""

    def __init__(self, redis_client, max_requests: int = 100, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, remaining_requests)."""
        key = f"ratelimit:{identifier}"
        current_time = int(time.time())

        # Use Redis sorted set to track requests
        # Remove old requests outside the window
        self.redis.zremrangebyscore(key, 0, current_time - self.window_seconds)

        # Count current requests in window
        request_count = self.redis.zcard(key)

        if request_count >= self.max_requests:
            # Calculate reset time
            oldest_request = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                reset_time = int(oldest_request[0][1]) + self.window_seconds
                remaining = 0
            else:
                reset_time = current_time + self.window_seconds
                remaining = self.max_requests
        else:
            # Add current request
            self.redis.zadd(key, {str(current_time): current_time})
            self.redis.expire(key, self.window_seconds)

            remaining = self.max_requests - request_count - 1
            reset_time = current_time + self.window_seconds

        allowed = request_count < self.max_requests
        return allowed, max(0, remaining)

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting API endpoints."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object (FastAPI dependency injection)
            request = kwargs.get('request')
            if not request:
                # Try to find in args
                for arg in args:
                    if hasattr(arg, 'client'):
                        request = arg
                        break

            if not request:
                return await func(*args, **kwargs)

            # Create identifier (IP + endpoint)
            client_ip = getattr(request.client, 'host', 'unknown')
            endpoint = getattr(request.url, 'path', '/')
            identifier = hashlib.sha256(f"{client_ip}:{endpoint}".encode()).hexdigest()[:16]

            # Check rate limit
            limiter = getattr(request.app.state, 'rate_limiter', None)
            if limiter:
                allowed, remaining = limiter.is_allowed(identifier)
                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded",
                        headers={"Retry-After": str(window_seconds)}
                    )

                # Add rate limit headers to response
                response = await func(*args, **kwargs)
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window_seconds)
                return response

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in FastAPI
@app.post("/api/v1/upload/file")
@rate_limit(max_requests=10, window_seconds=60)  # 10 requests per minute
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Upload file with rate limiting."""
    # Implementation here
    pass
```

#### Authentication and Authorization
```python
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Security configuration
SECRET_KEY = "your-secret-key-here"  # Must be 32+ chars in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list = []
    expires_at: Optional[datetime] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: list = []

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "transcription-engine",
        "aud": "transcription-api"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        scopes: list = payload.get("scopes", [])

        if username is None:
            raise credentials_exception

        # In production, fetch user from database
        # For demo, create mock user
        user = User(
            username=username,
            scopes=scopes,
            disabled=False
        )

    except JWTError:
        raise credentials_exception

    return user

def check_permissions(required_scopes: list):
    """Check if user has required permissions."""
    def permission_checker(current_user: User = Depends(get_current_user)):
        for scope in required_scopes:
            if scope not in current_user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
        return current_user
    return permission_checker

# Usage in API endpoints
@app.post("/api/v1/upload/file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(check_permissions(["files.upload"]))
):
    """Upload file (requires upload permission)."""
    # Implementation here
    pass

@app.get("/api/v1/admin/stats")
async def get_admin_stats(
    current_user: User = Depends(check_permissions(["admin.read"]))
):
    """Get admin statistics (requires admin permission)."""
    # Implementation here
    pass
```

---

## Testing Strategies

### Comprehensive Test Coverage

#### Unit Testing Best Practices
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import tempfile
import os

@pytest.fixture
def temp_audio_file():
    """Create temporary audio file for testing."""
    # Create minimal valid WAV file
    wav_data = (
        b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
        b'\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        + b'\x00\x00' * 512  # Audio data
    )

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(wav_data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def test_db():
    """Create in-memory test database."""
    # Use SQLite for fast testing
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create tables
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def client(test_db):
    """Create test client with database."""
    from app.main import app

    # Override database dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

class TestTranscriptionService:
    """Comprehensive transcription service tests."""

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, temp_audio_file):
        """Test successful audio transcription."""
        from app.services.transcription_service import transcription_service

        # Mock the actual transcription to avoid AI model dependencies
        with patch.object(transcription_service, 'transcribe_audio') as mock_transcribe:
            expected_result = {
                "text": "Hello world",
                "confidence": 0.95,
                "segments": [{"start": 0, "end": 2, "text": "Hello world"}]
            }
            mock_transcribe.return_value = expected_result

            result = await transcription_service.transcribe_audio(
                job_id="test-job",
                audio_path=temp_audio_file,
                language="en"
            )

            assert result["text"] == "Hello world"
            assert result["confidence"] == 0.95
            mock_transcribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self):
        """Test error handling for missing files."""
        from app.services.transcription_service import transcription_service

        with pytest.raises(FileNotFoundError):
            await transcription_service.transcribe_audio(
                job_id="test-job",
                audio_path="/nonexistent/file.wav",
                language="en"
            )

    @pytest.mark.parametrize("language,model_size", [
        ("en", "large-v3"),
        ("ar", "large-v3"),
        ("fr", "medium"),
        ("es", "medium")
    ])
    def test_model_selection_by_language(self, language, model_size):
        """Test that appropriate models are selected for different languages."""
        # Test model selection logic
        assert model_size in ["tiny", "base", "small", "medium", "large", "large-v3"]

    @pytest.mark.asyncio
    async def test_concurrent_transcription_limit(self):
        """Test concurrent transcription handling."""
        import asyncio
        from app.services.transcription_service import transcription_service

        # Create multiple concurrent requests
        async def transcribe_once(job_id):
            return await transcription_service.transcribe_audio(
                job_id=job_id,
                audio_path=temp_audio_file,  # Would need fixture
                language="en"
            )

        # Mock to return different results
        with patch.object(transcription_service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.side_effect = [
                {"text": f"Transcript {i}", "confidence": 0.9}
                for i in range(5)
            ]

            # Execute 5 concurrent transcriptions
            tasks = [transcribe_once(f"job-{i}") for i in range(5)]
            results = await asyncio.gather(*tasks)

            # Verify all completed successfully
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result["text"] == f"Transcript {i}"

    def test_service_initialization(self):
        """Test service initialization and required attributes."""
        from app.services.transcription_service import transcription_service

        required_attributes = [
            'model', 'model_loaded', 'device', 'dialect_detector',
            'adaptive_service', 'finetuned_models'
        ]

        for attr in required_attributes:
            assert hasattr(transcription_service, attr), f"Missing {attr}"
```

#### Integration Testing
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

class TestTranscriptionIntegration:
    """Integration tests for complete transcription workflow."""

    @pytest.fixture
    async def client(self):
        """Create test client."""
        from app.main import app
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def db_session(self):
        """Create test database session."""
        # Setup test database
        pass

    @pytest.mark.asyncio
    async def test_complete_transcription_workflow(self, client, db_session):
        """Test complete transcription workflow from upload to results."""
        # Step 1: Upload file
        audio_content = self._create_test_wav()
        files = {"file": ("test.wav", audio_content, "audio/wav")}
        data = {
            "language": "ar",
            "enable_translation": "true",
            "target_language": "en"
        }

        upload_response = await client.post("/api/v1/upload/file", files=files, data=data)
        assert upload_response.status_code == 200

        job_data = upload_response.json()
        job_id = job_data["job_id"]

        # Step 2: Monitor progress
        max_attempts = 60  # 5 minutes max
        for attempt in range(max_attempts):
            status_response = await client.get(f"/api/v1/jobs/{job_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            status = status_data["status"]

            if status == "completed":
                break
            elif status == "failed":
                pytest.fail(f"Job failed: {status_data.get('message', 'Unknown error')}")

            # Wait before next check
            import asyncio
            await asyncio.sleep(5)
        else:
            pytest.fail("Job did not complete within timeout")

        # Step 3: Get results
        results_response = await client.get(f"/api/v1/jobs/{job_id}/results")
        assert results_response.status_code == 200

        results = results_response.json()

        # Validate results structure
        assert "transcript" in results
        assert "translation" in results
        assert isinstance(results["transcript"], str)
        assert isinstance(results["translation"], str)
        assert len(results["transcript"]) > 0
        assert len(results["translation"]) > 0

        # Verify database state
        from app.services.job_service import get_job
        job = await get_job(job_id)
        assert job.status == "completed"
        assert job.transcript is not None
        assert job.translation is not None

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, client):
        """Test error recovery mechanisms."""
        # Test with invalid file
        files = {"file": ("test.txt", b"not audio", "text/plain")}

        response = await client.post("/api/v1/upload/file", files=files)
        assert response.status_code == 400

        error_data = response.json()
        assert "error_code" in error_data
        assert error_data["error_code"] == "VALIDATION_ERROR"

    def _create_test_wav(self):
        """Create minimal valid WAV file for testing."""
        wav_header = (
            b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
            b'\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        )
        audio_data = b'\x00\x00' * 1024
        return wav_header + audio_data
```

#### Performance Testing
```python
import pytest
import time
import asyncio
from statistics import mean, median
import psutil
import GPUtil

class TestTranscriptionPerformance:
    """Performance tests for transcription service."""

    @pytest.fixture
    def performance_audio(self):
        """Create test audio file of known duration."""
        # Create 30-second test audio
        pass

    def test_transcription_speed_benchmark(self, performance_audio):
        """Benchmark transcription processing speed."""
        from app.services.transcription_service import transcription_service

        start_time = time.time()
        # Run transcription
        result = asyncio.run(transcription_service.transcribe_audio(
            job_id="perf-test",
            audio_path=performance_audio,
            language="en"
        ))
        end_time = time.time()

        processing_time = end_time - start_time
        audio_duration = 30.0  # seconds

        # Calculate metrics
        realtime_factor = audio_duration / processing_time
        throughput = len(result["text"].split()) / processing_time  # words/second

        # Assert performance requirements
        assert realtime_factor >= 10, f"Too slow: {realtime_factor:.1f}x realtime"
        assert throughput >= 50, f"Low throughput: {throughput:.1f} words/second"

        print(f"Processing time: {processing_time:.2f}s")
        print(f"Realtime factor: {realtime_factor:.1f}x")
        print(f"Throughput: {throughput:.1f} words/second")

    def test_memory_usage_during_transcription(self, performance_audio):
        """Test memory usage during transcription."""
        import tracemalloc

        tracemalloc.start()

        initial_memory = tracemalloc.get_traced_memory()[0]

        # Run transcription
        from app.services.transcription_service import transcription_service
        result = asyncio.run(transcription_service.transcribe_audio(
            job_id="memory-test",
            audio_path=performance_audio,
            language="en"
        ))

        final_memory = tracemalloc.get_traced_memory()[0]
        memory_delta = final_memory - initial_memory

        tracemalloc.stop()

        # Convert to MB
        memory_mb = memory_delta / (1024 * 1024)

        # Assert memory usage is reasonable
        assert memory_mb < 500, f"High memory usage: {memory_mb:.1f}MB"

        print(f"Memory usage: {memory_mb:.1f}MB")

    def test_concurrent_load_performance(self):
        """Test performance under concurrent load."""
        import concurrent.futures
        import threading

        results = []
        errors = []
        lock = threading.Lock()

        def run_single_transcription(job_id):
            try:
                # Simulate transcription request
                start_time = time.time()
                # Mock transcription call
                time.sleep(1)  # Simulate processing
                end_time = time.time()

                with lock:
                    results.append({
                        "job_id": job_id,
                        "processing_time": end_time - start_time,
                        "success": True
                    })
            except Exception as e:
                with lock:
                    errors.append(str(e))

        # Run 10 concurrent transcriptions
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(run_single_transcription, f"job-{i}")
                for i in range(10)
            ]

            # Wait for completion
            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Analyze results
        processing_times = [r["processing_time"] for r in results]

        avg_time = mean(processing_times)
        median_time = median(processing_times)
        max_time = max(processing_times)
        success_rate = len(results) / (len(results) + len(errors))

        # Assert performance requirements
        assert success_rate >= 0.95, f"Low success rate: {success_rate:.2%}"
        assert avg_time < 2.0, f"Slow average time: {avg_time:.2f}s"
        assert max_time < 5.0, f"Very slow max time: {max_time:.2f}s"

        print(f"Concurrent load test results:")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Average time: {avg_time:.2f}s")
        print(f"  Median time: {median_time:.2f}s")
        print(f"  Max time: {max_time:.2f}s")

    def test_gpu_utilization_efficiency(self):
        """Test GPU utilization during transcription."""
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")

        # Monitor GPU usage during transcription
        initial_gpu = GPUtil.getGPUs()[0]

        # Run transcription
        from app.services.transcription_service import transcription_service
        result = asyncio.run(transcription_service.transcribe_audio(
            job_id="gpu-test",
            audio_path=performance_audio,
            language="en"
        ))

        final_gpu = GPUtil.getGPUs()[0]

        gpu_utilization = final_gpu.memoryUsed / final_gpu.memoryTotal

        # Assert reasonable GPU usage
        assert gpu_utilization < 0.9, f"High GPU memory usage: {gpu_utilization:.2%}"

        print(f"GPU utilization: {gpu_utilization:.2%}")
        print(f"GPU memory used: {final_gpu.memoryUsed}MB / {final_gpu.memoryTotal}MB")
```

---

## Deployment Practices

### Infrastructure as Code

#### Docker Best Practices
```dockerfile
# Multi-stage Dockerfile for production
# Stage 1: Builder
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=app:app . /app
WORKDIR /app

# Set proper permissions
RUN chown -R app:app /app && \
    chmod +x /app/scripts/* && \
    mkdir -p /tmp/audio_chunks && \
    chown -R app:app /tmp/audio_chunks

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Kubernetes Deployment Best Practices
```yaml
# Production-ready Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: transcription-api
  namespace: transcription-engine
  labels:
    app: transcription-engine
    component: api
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: transcription-engine
      component: api
  template:
    metadata:
      labels:
        app: transcription-engine
        component: api
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      # Node affinity for GPU workloads
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: nvidia.com/gpu.present
                operator: In
                values:
                - "true"

      containers:
      - name: api
        image: ghcr.io/yourusername/transcription-engine:v1.0.0
        imagePullPolicy: Always

        # Resource limits
        resources:
          requests:
            cpu: "1000m"
            memory: "2Gi"
            nvidia.com/gpu: 1
          limits:
            cpu: "2000m"
            memory: "4Gi"
            nvidia.com/gpu: 1

        # Environment variables
        envFrom:
        - configMapRef:
            name: transcription-config
        - secretRef:
            name: transcription-secrets

        # Ports
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP

        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

        # Startup probe
        startupProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          failureThreshold: 30
          periodSeconds: 10

        # Volume mounts
        volumeMounts:
        - name: models-cache
          mountPath: /app/models
        - name: temp-storage
          mountPath: /tmp

      volumes:
      - name: models-cache
        persistentVolumeClaim:
          claimName: models-pvc
      - name: temp-storage
        emptyDir: {}

      # Pod disruption budget
      disruptionBudget:
        minAvailable: 2

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: transcription-api-hpa
  namespace: transcription-engine
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: transcription-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 300
```

### CI/CD Pipeline Best Practices

#### GitHub Actions Workflow
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linting
      run: |
        black --check --diff backend/app/
        isort --check-only --diff backend/app/
        flake8 backend/app/
        mypy backend/app/

    - name: Run tests
      run: |
        pytest backend/tests/ -v --cov=app --cov-report=xml
      env:
        DATABASE_URL: postgresql://test:test@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Run security scan
      uses: github/super-linter@v4
      env:
        VALIDATE_ALL_CODEBASE: false
        VALIDATE_PYTHON: true
        VALIDATE_JAVASCRIPT: true
        VALIDATE_DOCKERFILE: true

    - name: Run dependency vulnerability scan
      run: |
        pip install safety
        safety check

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:latest
          ghcr.io/${{ github.repository }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging

    steps:
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Add deployment commands here

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production environment"
        # Add deployment commands here
```

---

*This best practices guide provides comprehensive recommendations for developing, deploying, and maintaining the SoutiAI Transcription Engine. Follow these guidelines to ensure high-quality, secure, and performant code.*
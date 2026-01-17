# API Reference

Complete API documentation for the SoutiAI Transcription Engine.

## Overview

The API provides comprehensive transcription, translation, and analysis capabilities with a focus on Arabic content and real-time processing.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: JWT Bearer token (for authenticated endpoints)

## Core Endpoints

### File Upload & Transcription

#### POST `/upload/file`

Upload and process audio/video files for transcription.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/upload/file" \
  -F "file=@audio.mp3" \
  -F "language=ar" \
  -F "text_sample=أهلاً يا جماعة إحنا هنتكلم عن المشروع ده" \
  -F "enable_translation=true" \
  -F "target_language=en" \
  -F "enable_summary=true" \
  -F "enable_voice_analytics=false"
```

**Parameters**:
- `file` (file): Audio/video file (max 500MB)
- `language` (string): Source language code (default: "ar")
- `text_sample` (string, optional): Text sample for Egyptian dialect detection
- `enable_translation` (boolean): Enable translation (default: true)
- `target_language` (string): Target language for translation (default: "en")
- `enable_summary` (boolean): Enable hierarchical summarization (default: true)
- `summary_length` (string): Summary length ("short", "medium", "long")
- `enable_voice_analytics` (boolean): Enable speaker diarization (default: false)

**Response**:
```json
{
  "job_id": "job_123456789",
  "status": "pending",
  "message": "File uploaded successfully. Processing started.",
  "estimated_time_seconds": 180
}
```

#### POST `/upload/url`

Upload from URL for remote files.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/upload/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/audio.mp3",
    "language": "ar",
    "enable_translation": true
  }'
```

### Job Management

#### GET `/jobs/{job_id}`

Get job status and basic information.

**Response**:
```json
{
  "id": "job_123456789",
  "status": "completed",
  "progress": 100.0,
  "filename": "meeting.mp3",
  "language": "ar",
  "created_at": "2024-01-17T10:00:00Z",
  "started_at": "2024-01-17T10:00:05Z",
  "completed_at": "2024-01-17T10:03:30Z",
  "processing_stats": {
    "transcription_time_seconds": 180,
    "confidence_score": 0.95,
    "gpu_used": true
  }
}
```

#### GET `/jobs`

List jobs with pagination and filtering.

**Query Parameters**:
- `status` (string): Filter by status
- `language` (string): Filter by language
- `limit` (integer): Number of results (default: 20)
- `offset` (integer): Pagination offset (default: 0)

**Response**:
```json
{
  "jobs": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

#### GET `/jobs/{job_id}/results`

Get complete job results including transcript, translation, and analysis.

**Response**:
```json
{
  "transcript": "Full transcript text...",
  "translation": "Full translation text...",
  "summary": "Hierarchical summary object...",
  "voice_analytics": {
    "speaker_segments": [...],
    "meeting_analysis": {...}
  },
  "subtitles_srt": "SRT subtitle content...",
  "subtitles_vtt": "VTT subtitle content...",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Segment text...",
      "confidence": 0.95,
      "speaker": "speaker_1"
    }
  ],
  "processing_stats": {...},
  "dialect_info": {
    "primary_dialect": "cairo",
    "confidence_score": 0.87,
    "regional_features": {...}
  }
}
```

### Real-time Streaming

#### POST `/stream/{session_id}/start`

Start a live streaming transcription session.

**Request**:
```json
{
  "language": "ar",
  "enable_translation": false,
  "text_sample": "أهلاً يا جماعة"
}
```

**Response**:
```json
{
  "session_id": "stream_123",
  "websocket_url": "ws://localhost:8000/api/v1/ws/stream/stream_123",
  "status": "active"
}
```

#### WebSocket `/ws/stream/{session_id}`

Real-time transcription WebSocket endpoint.

**Message Format** (Client → Server):
```json
{
  "type": "audio_data",
  "audio": "base64_encoded_audio_chunk",
  "format": "wav",
  "sample_rate": 16000
}
```

**Message Format** (Server → Client):
```json
{
  "type": "transcription",
  "text": "Live transcription text...",
  "confidence": 0.92,
  "is_final": false,
  "timestamp": 1234567890
}
```

#### GET `/stream/{session_id}/status`

Get streaming session status.

#### POST `/stream/{session_id}/stop`

Stop streaming session.

### RAG Q&A System

#### POST `/qa/{job_id}/setup-qa`

Initialize Q&A system for a completed job.

**Response**:
```json
{
  "status": "ready",
  "documents_count": 25,
  "chunks_count": 150
}
```

#### POST `/qa/{job_id}/ask`

Ask questions about transcript content.

**Request**:
```json
{
  "question": "What were the main action items discussed?",
  "max_answers": 3,
  "include_sources": true
}
```

**Response**:
```json
{
  "answer": "The main action items were...",
  "confidence": 0.89,
  "sources": [
    {
      "text": "Source text snippet...",
      "timestamp": 120.5,
      "relevance_score": 0.95
    }
  ],
  "follow_up_questions": [
    "Can you elaborate on the timeline?",
    "Who is responsible for each item?"
  ]
}
```

### Voice Analytics

#### POST `/voice/{job_id}/analyze`

Perform detailed voice analysis on audio.

**Response**:
```json
{
  "speaker_segments": [
    {
      "speaker": "speaker_1",
      "start": 0.0,
      "end": 45.2,
      "text": "Speaker's transcript...",
      "emotion": "neutral",
      "confidence": 0.92
    }
  ],
  "meeting_analysis": {
    "total_speakers": 3,
    "total_duration": 1800,
    "speaking_time_distribution": {
      "speaker_1": 0.45,
      "speaker_2": 0.35,
      "speaker_3": 0.20
    },
    "conversation_dynamics": {
      "turn_taking_efficiency": 0.78,
      "monologue_ratio": 0.15,
      "engagement_score": 0.82
    }
  }
}
```

#### GET `/voice/models/status`

Check voice analytics model status.

### Translation & Summarization

#### POST `/translate/text`

Translate text content.

**Request**:
```json
{
  "text": "Arabic text to translate...",
  "source_language": "ar",
  "target_language": "en",
  "domain": "general"
}
```

#### POST `/summarize/text`

Generate hierarchical summaries.

**Request**:
```json
{
  "text": "Long text to summarize...",
  "summary_type": "hierarchical",
  "max_length": "medium"
}
```

**Response**:
```json
{
  "level_1_elevator_pitch": "30-second summary...",
  "level_2_key_points": "2-minute summary...",
  "level_3_comprehensive": "5+ minute detailed summary...",
  "metadata": {
    "compression_ratio": 0.15,
    "key_topics": ["topic1", "topic2"]
  }
}
```

### Administrative Endpoints

#### GET `/health`

System health check.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "api": "up",
    "database": "up",
    "redis": "up",
    "celery": "up",
    "models": {
      "whisper": "loaded",
      "translation": "loaded",
      "voice_analytics": "loaded"
    }
  },
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "gpu_available": true,
    "gpu_memory_used": 2048
  }
}
```

#### GET `/metrics`

Prometheus metrics endpoint.

#### POST `/admin/models/reload`

Reload ML models (admin only).

### WebSocket Endpoints

#### `/ws/jobs/{job_id}`

Real-time job progress updates.

**Message Format**:
```json
{
  "type": "progress_update",
  "job_id": "job_123",
  "progress": 65.5,
  "stage": "transcribing",
  "message": "Processing audio segments...",
  "eta_seconds": 45
}
```

#### `/ws/stream/{session_id}`

Real-time streaming transcription.

## Error Handling

### HTTP Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `429`: Rate Limited
- `500`: Internal Server Error
- `503`: Service Unavailable

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "field": "language",
  "suggestion": "Use ISO 639-1 language codes"
}
```

## Rate Limiting

- **Anonymous**: 10 requests/hour
- **Authenticated**: 1000 requests/hour
- **Streaming**: 60 seconds/minute per session

## File Format Support

### Audio Formats
- MP3, WAV, M4A, FLAC, OGG, AAC
- Sample rates: 8kHz - 48kHz
- Channels: Mono/Stereo

### Video Formats
- MP4, AVI, MOV, MKV, FLV, WMV
- Automatic audio extraction

### Size Limits
- Maximum file size: 500MB
- Maximum duration: 8 hours
- Recommended chunk size: <2GB for optimal performance

## Authentication

### JWT Token Authentication

```bash
# Get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/api/v1/jobs"
```

## SDKs and Libraries

### Python Client

```python
from souti_client import SoutiClient

client = SoutiClient(api_key="your_key")

# Upload and transcribe
job = client.upload_file("audio.mp3", language="ar")
result = client.wait_for_completion(job.id)

print(result.transcript)
```

### JavaScript Client

```javascript
import { SoutiClient } from 'souti-sdk';

const client = new SoutiClient({ apiKey: 'your_key' });

// Real-time streaming
const session = await client.start_streaming({
  language: 'ar',
  onTranscription: (text) => console.log(text)
});
```

## Data Models

### Job Status Values
- `pending`: Job created, waiting to start
- `downloading`: Downloading file from URL
- `preprocessing`: Audio extraction and validation
- `transcribing`: Active transcription
- `rag_processing`: Contextual correction
- `translating`: Translation processing
- `summarizing`: Summary generation
- `tts_processing`: Text-to-speech generation
- `completed`: Job finished successfully
- `failed`: Job failed with error
- `cancelled`: Job cancelled by user

### Language Codes
- `ar`: Arabic (with dialect detection)
- `en`: English
- `fr`: French
- `de`: German
- `es`: Spanish
- `zh`: Chinese
- `hi`: Hindi
- `ru`: Russian
- `pt`: Portuguese
- `ja`: Japanese
- `ko`: Korean

### Confidence Scores
- `0.0-0.3`: Low confidence, review recommended
- `0.3-0.7`: Medium confidence, generally accurate
- `0.7-0.9`: High confidence, reliable
- `0.9-1.0`: Very high confidence, excellent accuracy

## Webhooks

Configure webhooks for job completion notifications:

```json
{
  "url": "https://your-app.com/webhook",
  "events": ["job.completed", "job.failed"],
  "secret": "webhook_secret"
}
```

## Best Practices

### For Optimal Results

1. **Provide Text Samples**: Include `text_sample` for Egyptian Arabic dialect detection
2. **Use Appropriate File Formats**: WAV/MP3 preferred for best quality
3. **Chunk Large Files**: Split files >2GB for better performance
4. **Monitor Progress**: Use WebSocket endpoints for real-time updates
5. **Handle Errors**: Implement retry logic with exponential backoff

### Performance Optimization

1. **Concurrent Processing**: Process multiple jobs in parallel
2. **Caching**: Cache frequent translations and summaries
3. **Compression**: Use compressed audio formats to reduce bandwidth
4. **Streaming**: Use real-time streaming for live applications

### Security Considerations

1. **Input Validation**: Validate all file uploads and parameters
2. **Rate Limiting**: Respect API rate limits
3. **Authentication**: Use JWT tokens for sensitive operations
4. **Encryption**: Use HTTPS for all API communications

## Support

- **Documentation**: https://docs.souti.ai
- **API Playground**: https://api.souti.ai/playground
- **Community**: https://discord.gg/souti-ai
- **Enterprise Support**: enterprise@souti.ai</content>
</xai:function_call">API_REFERENCE.md
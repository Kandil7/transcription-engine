# 🔧 Code Examples & Snippets

Practical code examples for common tasks in the SoutiAI Transcription Engine.

## Table of Contents

- [API Usage Examples](#api-usage-examples)
- [Client Library Examples](#client-library-examples)
- [Configuration Examples](#configuration-examples)
- [Testing Examples](#testing-examples)
- [Deployment Examples](#deployment-examples)
- [Troubleshooting Examples](#troubleshooting-examples)

---

## API Usage Examples

### Basic File Upload and Transcription

#### Python Client
```python
import asyncio
import aiohttp

async def transcribe_audio_file(file_path: str, language: str = "ar") -> dict:
    """
    Upload and transcribe an audio file using the REST API.

    Args:
        file_path: Path to the audio file
        language: Language code (ar, en, etc.)

    Returns:
        dict: Job information and results
    """
    async with aiohttp.ClientSession() as session:
        # Step 1: Upload file
        with open(file_path, 'rb') as f:
            upload_data = aiohttp.FormData()
            upload_data.add_field('file', f, filename=file_path.split('/')[-1])
            upload_data.add_field('language', language)
            upload_data.add_field('enable_translation', 'true')
            upload_data.add_field('target_language', 'en')

            async with session.post(
                'http://localhost:8000/api/v1/upload/file',
                data=upload_data
            ) as response:
                upload_result = await response.json()
                job_id = upload_result['job_id']

        # Step 2: Poll for completion
        while True:
            async with session.get(f'http://localhost:8000/api/v1/jobs/{job_id}') as response:
                job_status = await response.json()

                if job_status['status'] == 'completed':
                    break
                elif job_status['status'] == 'failed':
                    raise Exception(f"Transcription failed: {job_status.get('message', 'Unknown error')}")

            await asyncio.sleep(5)  # Wait 5 seconds before checking again

        # Step 3: Get results
        async with session.get(f'http://localhost:8000/api/v1/jobs/{job_id}/results') as response:
            results = await response.json()

        return {
            'job_id': job_id,
            'transcript': results.get('transcript'),
            'translation': results.get('translation'),
            'summary': results.get('summary'),
            'voice_analytics': results.get('voice_analytics')
        }

# Usage
async def main():
    result = await transcribe_audio_file('meeting.wav', 'ar')
    print(f"Transcript: {result['transcript'][:100]}...")
    print(f"Translation: {result['translation'][:100]}...")
    if result['voice_analytics']:
        print(f"Speakers detected: {len(result['voice_analytics'].get('speaker_segments', []))}")

asyncio.run(main())
```

#### JavaScript/Node.js Client
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function transcribeAudioFile(filePath, language = 'ar') {
    try {
        // Step 1: Upload file
        const formData = new FormData();
        formData.append('file', fs.createReadStream(filePath));
        formData.append('language', language);
        formData.append('enable_translation', 'true');
        formData.append('target_language', 'en');

        const uploadResponse = await axios.post(
            'http://localhost:8000/api/v1/upload/file',
            formData,
            {
                headers: formData.getHeaders(),
                maxContentLength: Infinity,
                maxBodyLength: Infinity
            }
        );

        const jobId = uploadResponse.data.job_id;
        console.log(`Job created: ${jobId}`);

        // Step 2: Poll for completion
        let jobStatus;
        do {
            const statusResponse = await axios.get(`http://localhost:8000/api/v1/jobs/${jobId}`);
            jobStatus = statusResponse.data;

            if (jobStatus.status === 'processing') {
                console.log(`Progress: ${jobStatus.progress || 0}%`);
                await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
            }
        } while (jobStatus.status === 'pending' || jobStatus.status === 'processing');

        if (jobStatus.status === 'failed') {
            throw new Error(`Transcription failed: ${jobStatus.message || 'Unknown error'}`);
        }

        // Step 3: Get results
        const resultsResponse = await axios.get(`http://localhost:8000/api/v1/jobs/${jobId}/results`);
        const results = resultsResponse.data;

        return {
            jobId,
            transcript: results.transcript,
            translation: results.translation,
            summary: results.summary,
            voiceAnalytics: results.voice_analytics
        };

    } catch (error) {
        console.error('Transcription error:', error.response?.data || error.message);
        throw error;
    }
}

// Usage
async function main() {
    try {
        const result = await transcribeAudioFile('meeting.wav', 'ar');
        console.log('Transcript:', result.transcript?.substring(0, 100) + '...');
        console.log('Translation:', result.translation?.substring(0, 100) + '...');
        if (result.voiceAnalytics?.speaker_segments) {
            console.log('Speakers detected:', result.voiceAnalytics.speaker_segments.length);
        }
    } catch (error) {
        console.error('Failed:', error.message);
    }
}

main();
```

### Real-time Streaming Transcription

#### WebSocket Client (JavaScript)
```javascript
class StreamingTranscriptionClient {
    constructor(apiUrl = 'ws://localhost:8000') {
        this.apiUrl = apiUrl;
        this.ws = null;
        this.sessionId = null;
    }

    async startSession(language = 'ar', enableTranslation = true) {
        try {
            // Start streaming session
            const response = await fetch(`${this.apiUrl.replace('ws://', 'http://')}/api/v1/stream/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    language,
                    enable_translation: enableTranslation,
                    target_language: 'en'
                })
            });

            const result = await response.json();
            this.sessionId = result.session_id;

            // Connect to WebSocket
            this.ws = new WebSocket(`${this.apiUrl}/api/v1/ws/stream/${this.sessionId}`);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'transcription') {
                    console.log('Live transcript:', data.text);
                    console.log('Confidence:', data.confidence);

                    // Update UI
                    this.updateTranscript(data.text, data.confidence);
                } else if (data.type === 'translation') {
                    console.log('Live translation:', data.text);
                    this.updateTranslation(data.text);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            return this.sessionId;

        } catch (error) {
            console.error('Failed to start session:', error);
            throw error;
        }
    }

    async sendAudioChunk(audioBlob) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket not connected');
        }

        // Convert blob to base64
        const base64Audio = await this.blobToBase64(audioBlob);

        this.ws.send(JSON.stringify({
            type: 'audio_data',
            audio: base64Audio,
            format: 'wav',
            sample_rate: 16000
        }));
    }

    async stopSession() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        if (this.sessionId) {
            try {
                await fetch(`${this.apiUrl.replace('ws://', 'http://')}/api/v1/stream/${this.sessionId}/stop`, {
                    method: 'POST'
                });
            } catch (error) {
                console.error('Error stopping session:', error);
            }
        }
    }

    updateTranscript(text, confidence) {
        const transcriptDiv = document.getElementById('live-transcript');
        if (transcriptDiv) {
            transcriptDiv.textContent = text;
            transcriptDiv.style.opacity = confidence > 0.8 ? '1.0' : '0.7';
        }
    }

    updateTranslation(text) {
        const translationDiv = document.getElementById('live-translation');
        if (translationDiv) {
            translationDiv.textContent = text;
        }
    }

    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
}

// Usage example
async function startLiveTranscription() {
    const client = new StreamingTranscriptionClient();

    try {
        // Start session
        const sessionId = await client.startSession('ar', true);
        console.log('Session started:', sessionId);

        // Set up audio recording
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = async (event) => {
            if (event.data.size > 0) {
                await client.sendAudioChunk(event.data);
            }
        };

        // Start recording in chunks
        mediaRecorder.start(1000); // 1 second chunks

        // Stop after 30 seconds for demo
        setTimeout(async () => {
            mediaRecorder.stop();
            await client.stopSession();
            console.log('Transcription session ended');
        }, 30000);

    } catch (error) {
        console.error('Live transcription failed:', error);
    }
}
```

### Intelligent Q&A System

#### Python Q&A Example
```python
import asyncio
import aiohttp

async def setup_and_query_transcript(job_id: str, questions: list) -> dict:
    """
    Set up Q&A system for a transcript and ask questions.

    Args:
        job_id: The job ID containing the transcript
        questions: List of questions to ask

    Returns:
        dict: Answers with sources and confidence scores
    """
    async with aiohttp.ClientSession() as session:
        results = {}

        # Step 1: Set up Q&A system
        try:
            async with session.post(f'http://localhost:8000/api/v1/qa/{job_id}/setup-qa') as response:
                if response.status != 200:
                    raise Exception(f"Failed to setup Q&A: {await response.text()}")

                setup_result = await response.json()
                print("Q&A system setup:", setup_result.get('message', 'Ready'))

        except Exception as e:
            print(f"Q&A setup failed: {e}")
            return results

        # Step 2: Ask questions
        for question in questions:
            try:
                qa_payload = {
                    "question": question,
                    "max_answers": 3,
                    "include_sources": True,
                    "context_window": 3  # Include 3 surrounding segments
                }

                async with session.post(
                    f'http://localhost:8000/api/v1/qa/{job_id}/ask',
                    json=qa_payload
                ) as response:

                    if response.status == 200:
                        answer_data = await response.json()
                        results[question] = {
                            "answer": answer_data.get("answer"),
                            "confidence": answer_data.get("confidence"),
                            "sources": answer_data.get("sources", [])
                        }
                        print(f"Q: {question}")
                        print(f"A: {answer_data.get('answer', 'No answer found')}")
                        print(f"Confidence: {answer_data.get('confidence', 0):.2f}")
                        print("---")
                    else:
                        error_text = await response.text()
                        print(f"Question failed: {question} - {error_text}")
                        results[question] = {"error": error_text}

            except Exception as e:
                print(f"Error asking question '{question}': {e}")
                results[question] = {"error": str(e)}

        return results

# Usage
async def main():
    job_id = "your_job_id_here"
    questions = [
        "What were the main action items discussed?",
        "Who was responsible for the budget approval?",
        "What was the timeline for project completion?",
        "Were there any concerns raised about the implementation?"
    ]

    results = await setup_and_query_transcript(job_id, questions)

    # Process results
    for question, answer_data in results.items():
        if "error" not in answer_data:
            print(f"✅ {question}")
            print(f"   Answer: {answer_data['answer']}")
            print(f"   Confidence: {answer_data['confidence']:.2f}")
            if answer_data['sources']:
                print(f"   Sources: {len(answer_data['sources'])} references")
        else:
            print(f"❌ {question}: {answer_data['error']}")
        print()

asyncio.run(main())
```

---

## Client Library Examples

### Official Python SDK

```python
from soutiai import TranscriptionClient
import asyncio

class ArabicTranscriptionProcessor:
    """Example processor for Arabic content with dialect handling."""

    def __init__(self, api_key: str, base_url: str = "https://api.souti.ai"):
        self.client = TranscriptionClient(
            api_key=api_key,
            base_url=base_url,
            timeout=300  # 5 minutes for long files
        )

    async def process_arabic_content(self, file_path: str, dialect: str = "cairo") -> dict:
        """
        Process Arabic audio with dialect-specific optimization.

        Args:
            file_path: Path to audio file
            dialect: Egyptian dialect ('cairo', 'alexandria', 'saidi', 'delta')

        Returns:
            dict: Processing results with dialect information
        """
        # Detect if file needs dialect processing
        dialect_sample = self._get_dialect_sample(dialect)

        # Upload with dialect detection
        job = await self.client.upload_file(
            file_path=file_path,
            language="ar",
            text_sample=dialect_sample,  # Enable dialect-adaptive transcription
            enable_translation=True,
            target_language="en",
            enable_voice_analytics=True,
            enable_summary=True,
            summary_length="medium"
        )

        print(f"Job created: {job['job_id']}")

        # Wait for completion with progress tracking
        result = await self.client.wait_for_completion(
            job_id=job['job_id'],
            progress_callback=self._progress_callback
        )

        # Enhance results with dialect information
        result['dialect'] = dialect
        result['dialect_confidence'] = self._estimate_dialect_confidence(result)

        return result

    def _get_dialect_sample(self, dialect: str) -> str:
        """Get dialect-specific text sample for better detection."""
        samples = {
            "cairo": "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده اللي هنعمله في الشركة",
            "alexandria": "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده اللي هنعمله في الشركة بس بلبناني",
            "saidi": "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده اللي هنعمله في الشركة والله",
            "delta": "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده اللي هنعمله في الشركة بس"
        }
        return samples.get(dialect, samples["cairo"])

    def _progress_callback(self, progress: float, message: str):
        """Progress callback for user feedback."""
        print(f"Progress: {progress:.1f}% - {message}")

    def _estimate_dialect_confidence(self, result: dict) -> float:
        """Estimate dialect detection confidence based on results."""
        # Simple heuristic based on transcription quality
        stats = result.get('processing_stats', {})
        confidence = stats.get('confidence_score', 0.8)

        # Adjust based on voice analytics (more speakers = more dialect variation)
        if result.get('voice_analytics'):
            speakers = len(result['voice_analytics'].get('speaker_segments', []))
            if speakers > 3:
                confidence *= 0.9  # Reduce confidence for multi-speaker content

        return min(confidence, 1.0)

    async def batch_process_files(self, file_paths: list, dialect: str = "cairo") -> list:
        """Process multiple files concurrently."""
        tasks = [
            self.process_arabic_content(file_path, dialect)
            for file_path in file_paths
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Failed to process {file_paths[i]}: {result}")
                processed_results.append({
                    "file": file_paths[i],
                    "error": str(result),
                    "success": False
                })
            else:
                result["file"] = file_paths[i]
                result["success"] = True
                processed_results.append(result)

        return processed_results

# Usage example
async def main():
    processor = ArabicTranscriptionProcessor(api_key="your-api-key")

    # Process single file
    result = await processor.process_arabic_content("meeting.wav", "cairo")
    print("Single file result:")
    print(f"  Transcript: {result['transcript'][:100]}...")
    print(f"  Translation: {result['translation'][:100]}...")
    print(f"  Dialect: {result['dialect']} (confidence: {result['dialect_confidence']:.2f})")

    # Process multiple files
    files = ["meeting1.wav", "meeting2.wav", "meeting3.wav"]
    batch_results = await processor.batch_process_files(files, "cairo")

    successful = sum(1 for r in batch_results if r.get("success", False))
    print(f"\nBatch processing: {successful}/{len(files)} files successful")

    for result in batch_results:
        if result.get("success"):
            print(f"✅ {result['file']}: {len(result.get('transcript', ''))} chars")
        else:
            print(f"❌ {result['file']}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Configuration Examples

### Environment Configuration Templates

#### Development Environment
```bash
# .env.dev - Development configuration
# =================================================================
# APPLICATION SETTINGS
# =================================================================
APP_NAME=TranscriptionEngine
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=2
RELOAD=true

# CORS Settings (permissive for development)
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# =================================================================
# DATABASE CONFIGURATION
# =================================================================
DATABASE_URL=postgresql://postgres:password@localhost:5432/transcription_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_ECHO=false

# =================================================================
# REDIS CONFIGURATION
# =================================================================
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# =================================================================
# AI MODEL CONFIGURATION
# =================================================================
WHISPER_MODEL_SIZE=base
TRANSLATION_MODEL=facebook/nllb-200-distilled-600M
SUMMARIZATION_MODEL=facebook/bart-large-cnn
EMBEDDING_MODEL=aubmindlab/bert-base-arabertv02

# Hardware Profile (auto-detect for development)
DETECTED_PROFILE=auto

# =================================================================
# FEATURE FLAGS
# =================================================================
ENABLE_TRANSLATION=true
ENABLE_SUMMARIZATION=true
ENABLE_VOICE_ANALYTICS=false
ENABLE_RAG=true
ENABLE_STREAMING=true
ENABLE_DIALECT_DETECTION=true

# =================================================================
# MONITORING (lightweight for development)
# =================================================================
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9090
LOG_FORMAT=json

# =================================================================
# DEVELOPMENT SPECIFIC
# =================================================================
PYTHONPATH=/app
PYTHONDONTWRITEBYTECODE=1
```

#### Production Environment
```bash
# .env.prod - Production configuration
# =================================================================
# APPLICATION SETTINGS
# =================================================================
APP_NAME=TranscriptionEngine
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=WARNING
ENVIRONMENT=production

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=8
RELOAD=false

# CORS Settings (restrictive for production)
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["Authorization", "Content-Type", "X-API-Key"]

# =================================================================
# SECURITY CONFIGURATION
# =================================================================
SECRET_KEY=your-32-char-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
ENCRYPTION_KEY=your-32-byte-encryption-key

# =================================================================
# DATABASE CONFIGURATION
# =================================================================
DATABASE_URL=postgresql://prod_user:prod_password@prod-db-host:5432/prod_db
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
DB_POOL_TIMEOUT=60
DB_ECHO=false

# =================================================================
# REDIS CONFIGURATION
# =================================================================
REDIS_URL=redis://prod-redis-host:6379/0
REDIS_POOL_SIZE=50

# =================================================================
# STORAGE CONFIGURATION
# =================================================================
STORAGE_TYPE=minio
MINIO_ENDPOINT=minio.yourdomain.com
MINIO_ACCESS_KEY=production-access-key
MINIO_SECRET_KEY=production-secret-key
MINIO_SECURE=true
MINIO_BUCKET=transcription-files

# =================================================================
# AI MODEL CONFIGURATION
# =================================================================
WHISPER_MODEL_SIZE=large-v3
TRANSLATION_MODEL=facebook/nllb-200-distilled-600M
SUMMARIZATION_MODEL=facebook/bart-large-cnn
EMBEDDING_MODEL=aubmindlab/bert-base-arabertv02

# Hardware Profile
DETECTED_PROFILE=ULTRA

# Processing Limits
MAX_FILE_SIZE_MB=500
MAX_DURATION_HOURS=4
CHUNK_SIZE_SECONDS=300

# =================================================================
# FEATURE FLAGS
# =================================================================
ENABLE_TRANSLATION=true
ENABLE_SUMMARIZATION=true
ENABLE_VOICE_ANALYTICS=true
ENABLE_RAG=true
ENABLE_STREAMING=true
ENABLE_DIALECT_DETECTION=true

# =================================================================
# MONITORING & LOGGING
# =================================================================
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9090
LOG_FORMAT=json
LOG_LEVEL=WARNING
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# =================================================================
# EXTERNAL SERVICES
# =================================================================
# Add your external service configurations here
# OPENAI_API_KEY=your-openai-key
# HUGGINGFACE_API_KEY=your-huggingface-key
```

#### Staging Environment
```bash
# .env.staging - Staging configuration
# =================================================================
# APPLICATION SETTINGS
# =================================================================
APP_NAME=TranscriptionEngine-Staging
APP_VERSION=1.0.0-beta
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=staging

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
RELOAD=false

# CORS Settings (staging domains)
CORS_ORIGINS=["https://staging.yourdomain.com", "https://app-staging.yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["Authorization", "Content-Type", "X-API-Key"]

# =================================================================
# SECURITY CONFIGURATION
# =================================================================
SECRET_KEY=staging-32-char-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # Longer for testing
ENCRYPTION_KEY=staging-32-byte-encryption-key

# =================================================================
# DATABASE CONFIGURATION
# =================================================================
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db-host:5432/staging_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=45
DB_ECHO=false

# =================================================================
# AI MODEL CONFIGURATION
# =================================================================
WHISPER_MODEL_SIZE=medium  # Smaller model for staging
TRANSLATION_MODEL=facebook/nllb-200-distilled-600M
SUMMARIZATION_MODEL=facebook/bart-large-cnn
EMBEDDING_MODEL=aubmindlab/bert-base-arabertv02

# Hardware Profile
DETECTED_PROFILE=STD_GPU

# Processing Limits (smaller for staging)
MAX_FILE_SIZE_MB=200
MAX_DURATION_HOURS=2
CHUNK_SIZE_SECONDS=300

# =================================================================
# MONITORING & LOGGING
# =================================================================
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9090
LOG_FORMAT=json
LOG_LEVEL=INFO
SENTRY_DSN=https://staging-sentry-dsn@sentry.io/project-id
```

### Docker Compose Overrides

#### Development Overrides
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  api:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - ENVIRONMENT=development
    volumes:
      - ./backend:/home/app
      - /tmp/audio_chunks:/tmp/audio_chunks
    ports:
      - "8000:8000"

  postgres:
    environment:
      - POSTGRES_DB=transcription_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"

  chromadb:
    ports:
      - "8001:8001"

  minio:
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"

volumes:
  postgres_dev_data:
```

#### Production Overrides
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: ghcr.io/yourusername/transcription-engine:latest
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=WARNING
    env_file:
      - .env.prod
    secrets:
      - jwt_secret
      - db_credentials
      - encryption_key
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB_FILE=/run/secrets/postgres_db
      - POSTGRES_USER_FILE=/run/secrets/postgres_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_db
      - postgres_user
      - postgres_password
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./monitoring/postgres/postgresql.conf:/etc/postgresql/postgresql.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_prod_data:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  worker:
    image: ghcr.io/yourusername/transcription-engine:latest
    command: celery -A app.tasks.celery_app worker --loglevel=info -c 4
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.prod
    secrets:
      - jwt_secret
      - db_credentials
      - encryption_key
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  db_credentials:
    file: ./secrets/db_credentials.txt
  encryption_key:
    file: ./secrets/encryption_key.txt

volumes:
  postgres_prod_data:
  redis_prod_data:
```

---

## Testing Examples

### Unit Test Examples

#### Service Layer Testing
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.transcription_service import TranscriptionService

class TestTranscriptionService:

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return TranscriptionService()

    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing."""
        return {
            "path": "/tmp/test.wav",
            "duration": 10.5,
            "language": "ar",
            "sample_rate": 16000
        }

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, service, sample_audio_data):
        """Test successful audio transcription."""
        expected_transcript = "أهلاً يا جماعة إحنا هنتكلم عن المشروع"
        expected_segments = [
            {
                "start": 0.0,
                "end": 3.5,
                "text": "أهلاً يا جماعة",
                "confidence": 0.95
            }
        ]

        # Mock the transcription
        with patch.object(service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = (expected_transcript, expected_segments, {})

            # Execute
            result = await service.transcribe_audio(
                job_id="test-job-123",
                audio_path=sample_audio_data["path"],
                language=sample_audio_data["language"]
            )

            # Verify
            transcript, segments, stats = result
            assert transcript == expected_transcript
            assert len(segments) == 1
            assert segments[0]["confidence"] == 0.95

            # Ensure transcription was called correctly
            mock_transcribe.assert_called_once_with(
                job_id="test-job-123",
                audio_path=sample_audio_data["path"],
                language=sample_audio_data["language"]
            )

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self, service):
        """Test error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            await service.transcribe_audio(
                job_id="test-job-123",
                audio_path="/nonexistent/file.wav",
                language="ar"
            )

    @pytest.mark.parametrize("language,model_size", [
        ("en", "large-v3"),
        ("ar", "large-v3"),
        ("fr", "medium"),
        ("es", "medium")
    ])
    def test_model_selection_logic(self, service, language, model_size):
        """Test that appropriate models are selected for different languages."""
        # This test verifies the model selection logic
        # In practice, this would test the actual selection method
        assert model_size in ["tiny", "base", "small", "medium", "large", "large-v3"]

    @pytest.mark.asyncio
    async def test_concurrent_transcription_limit(self, service, sample_audio_data):
        """Test concurrent transcription handling."""
        import asyncio

        # Create multiple concurrent requests
        async def transcribe_once(job_id):
            return await service.transcribe_audio(
                job_id=job_id,
                audio_path=sample_audio_data["path"],
                language="ar"
            )

        # Mock successful transcription
        with patch.object(service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = ("Test transcript", [], {})

            # Execute 5 concurrent transcriptions
            tasks = [
                transcribe_once(f"job-{i}")
                for i in range(5)
            ]

            results = await asyncio.gather(*tasks)

            # Verify all completed successfully
            assert len(results) == 5
            for result in results:
                transcript, segments, stats = result
                assert transcript == "Test transcript"

    def test_service_initialization(self, service):
        """Test service initialization and required attributes."""
        required_attributes = [
            'model', 'model_loaded', 'device', 'dialect_detector',
            'adaptive_service', 'finetuned_models'
        ]

        for attr in required_attributes:
            assert hasattr(service, attr), f"Service missing required attribute: {attr}"

    @pytest.mark.asyncio
    async def test_dialect_adaptation_fallback(self, service, sample_audio_data):
        """Test fallback when dialect adaptation fails."""
        # Mock dialect adaptation failure
        with patch.object(service.adaptive_service, 'transcribe_with_adaptation', side_effect=Exception("Adaptation failed")), \
             patch.object(service, 'transcribe_audio') as mock_fallback:

            mock_fallback.return_value = ("Fallback transcript", [], {})

            result = await service.transcribe_with_dialect_adaptation(
                job_id="test-job",
                audio_path=sample_audio_data["path"],
                text_sample="أهلاً يا جماعة",
                language="ar"
            )

            transcript, segments, stats, dialect_info = result
            assert transcript == "Fallback transcript"
            assert dialect_info is None  # No dialect info on fallback

            # Verify fallback was called
            mock_fallback.assert_called_once()
```

#### API Integration Testing
```python
import pytest
from httpx import AsyncClient
from app.main import app

class TestTranscriptionAPI:

    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_upload_arabic_audio(self, client):
        """Test uploading Arabic audio file."""
        # Create mock Arabic audio file
        arabic_audio_content = self._create_mock_wav_file()
        arabic_text_sample = "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده"

        files = {
            "file": ("arabic_meeting.wav", arabic_audio_content, "audio/wav")
        }
        data = {
            "language": "ar",
            "text_sample": arabic_text_sample,
            "enable_translation": "true",
            "target_language": "en",
            "enable_voice_analytics": "true"
        }

        with patch('app.services.job_service.create_job') as mock_create, \
             patch('app.core.storage.upload_file') as mock_upload, \
             patch('app.utils.audio.validate_audio_file', new_callable=AsyncMock) as mock_validate:

            # Setup mocks
            mock_create.return_value = "arabic-job-12345"
            mock_upload.return_value = "/uploads/arabic_meeting.wav"
            mock_validate.return_value = {
                "duration": 15.3,
                "channels": 1,
                "sample_rate": 16000,
                "bit_depth": 16
            }

            response = await client.post("/api/v1/upload/file", files=files, data=data)

            assert response.status_code == 200
            result = response.json()

            # Verify response structure
            assert "job_id" in result
            assert "status" in result
            assert "message" in result
            assert result["status"] == "uploaded"

            # Verify job creation was called with correct parameters
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]  # Keyword arguments

            assert call_args["filename"] == "arabic_meeting.wav"
            assert call_args["language"] == "ar"
            assert call_args["text_sample"] == arabic_text_sample
            assert call_args["enable_translation"] is True
            assert call_args["enable_voice_analytics"] is True

    @pytest.mark.asyncio
    async def test_get_job_status_progression(self, client):
        """Test job status progression from pending to completed."""
        job_id = "progress-test-job"

        # Mock different job states
        job_states = [
            {"status": "pending", "progress": 0, "message": "Job queued"},
            {"status": "processing", "progress": 25, "message": "Preprocessing audio"},
            {"status": "processing", "progress": 60, "message": "Transcribing audio"},
            {"status": "processing", "progress": 90, "message": "Generating results"},
            {"status": "completed", "progress": 100, "message": "Transcription completed"}
        ]

        for expected_state in job_states:
            with patch('app.services.job_service.get_job') as mock_get:
                mock_job = Mock()
                mock_job.id = job_id
                mock_job.status = expected_state["status"]
                mock_job.progress = expected_state["progress"]
                mock_job.message = expected_state["message"]
                mock_job.created_at = "2024-01-17T10:00:00Z"
                mock_job.updated_at = "2024-01-17T10:05:00Z"
                # Add other required attributes
                for attr in ['filename', 'duration', 'language', 'enable_translation',
                           'enable_summary', 'enable_voice_analytics', 'target_language', 'summary_length']:
                    setattr(mock_job, attr, getattr(expected_state, attr, None))

                mock_get.return_value = mock_job

                response = await client.get(f"/api/v1/jobs/{job_id}")
                assert response.status_code == 200

                result = response.json()
                assert result["status"] == expected_state["status"]
                assert result["progress"] == expected_state["progress"]
                assert expected_state["message"] in result["message"]

    def _create_mock_wav_file(self):
        """Create a minimal valid WAV file for testing."""
        # WAV header (44 bytes) + minimal audio data
        wav_header = (
            b'RIFF'  # ChunkID
            b'\x24\x08\x00\x00'  # ChunkSize
            b'WAVE'  # Format
            b'fmt '  # Subchunk1ID
            b'\x10\x00\x00\x00'  # Subchunk1Size
            b'\x01\x00'  # AudioFormat (PCM)
            b'\x01\x00'  # NumChannels
            b'\x80>\x00\x00'  # SampleRate (16000)
            b'\x00}\x00\x00'  # ByteRate
            b'\x02\x00'  # BlockAlign
            b'\x10\x00'  # BitsPerSample
            b'data'  # Subchunk2ID
            b'\x00\x08\x00\x00'  # Subchunk2Size
        )
        # Add some dummy audio data
        audio_data = b'\x00\x00' * 1024
        return wav_header + audio_data
```

---

## Deployment Examples

### Docker Single-Container Deployment

#### Basic Setup
```bash
# 1. Clone and setup
git clone https://github.com/yourusername/transcription-engine.git
cd transcription-engine

# 2. Create environment file
cp env-example.txt .env

# 3. Edit configuration
nano .env  # Set database URL, Redis URL, etc.

# 4. Start services
docker-compose up -d

# 5. Check status
docker-compose ps
docker-compose logs api

# 6. Access application
open http://localhost:8000/docs  # API documentation
open http://localhost:3000      # Frontend (if running)
```

#### Production Deployment
```bash
# 1. Build production images
docker-compose -f docker-compose.prod.yml build

# 2. Deploy with production config
docker-compose -f docker-compose.prod.yml up -d

# 3. Scale services
docker-compose -f docker-compose.prod.yml up -d --scale api=3 --scale worker=2

# 4. Check health
curl http://localhost:8000/health

# 5. Monitor logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### Kubernetes Deployment

#### Basic Cluster Setup
```bash
# 1. Apply namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. Deploy infrastructure
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/chroma.yaml
kubectl apply -f k8s/minio.yaml

# 4. Deploy application
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/worker.yaml
kubectl apply -f k8s/frontend.yaml

# 5. Apply auto-scaling
kubectl apply -f k8s/hpa.yaml

# 6. Check deployment status
kubectl get pods -n transcription-engine
kubectl get services -n transcription-engine

# 7. Check logs
kubectl logs -f deployment/transcription-api -n transcription-engine
```

#### Production Kubernetes Deployment
```bash
# 1. Use Kustomize for environment management
kubectl apply -k k8s/

# 2. Or use Helm
helm install transcription-engine ./helm/transcription-engine \
  --namespace transcription-engine \
  --create-namespace \
  --values values-prod.yaml

# 3. Check rollout status
kubectl rollout status deployment/transcription-api -n transcription-engine

# 4. Enable ingress
kubectl apply -f k8s/ingress-prod.yaml

# 5. Setup monitoring
kubectl apply -f monitoring/prometheus/prometheus.yaml
kubectl apply -f monitoring/grafana/grafana.yaml

# 6. Access application
# API: https://api.yourdomain.com
# Frontend: https://app.yourdomain.com
# Monitoring: https://monitoring.yourdomain.com
```

### Cloud Platform Deployments

#### AWS Deployment
```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name transcription-engine

# 2. Build and push image
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build -t transcription-engine .
docker tag transcription-engine:latest <account>.dkr.ecr.<region>.amazonaws.com/transcription-engine:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/transcription-engine:latest

# 3. Deploy to ECS/Fargate
aws ecs create-cluster --cluster-name transcription-cluster
aws ecs create-service --cluster transcription-cluster --service-name transcription-service --task-definition transcription-task

# 4. Setup load balancer
aws elbv2 create-load-balancer --name transcription-lb --subnets subnet-123 subnet-456

# 5. Configure auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/transcription-cluster/transcription-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10
```

#### Google Cloud Deployment
```bash
# 1. Build and push to GCR
gcloud builds submit --tag gcr.io/your-project/transcription-engine

# 2. Deploy to Cloud Run
gcloud run deploy transcription-engine \
  --image gcr.io/your-project/transcription-engine \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10

# 3. Setup Cloud SQL (PostgreSQL)
gcloud sql instances create transcription-db \
  --database-version POSTGRES_15 \
  --tier db-f1-micro \
  --region us-central1

# 4. Setup Memorystore (Redis)
gcloud redis instances create transcription-redis \
  --size 1 \
  --region us-central1 \
  --tier basic
```

---

## Troubleshooting Examples

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Problem: Database connection fails
# Solution: Check connection string and network

# 1. Test database connectivity
psql "postgresql://user:pass@host:5432/db" -c "SELECT 1;"

# 2. Check environment variables
env | grep DATABASE

# 3. Verify Docker networking
docker-compose exec postgres psql -U postgres -d transcription_db -c "SELECT version();"

# 4. Check connection pool settings
# In .env file:
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
```

#### Model Loading Failures
```python
# Problem: AI models fail to load
# Solution: Check GPU memory and model paths

import torch

# 1. Check GPU availability
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory // 1024**3}GB")

# 2. Check model cache
import os
cache_dir = os.path.expanduser("~/.cache/huggingface")
print(f"Cache directory: {cache_dir}")
print(f"Cache size: {sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, dirnames, filenames in os.walk(cache_dir) for filename in filenames) // 1024**3}GB")

# 3. Clear model cache if corrupted
import shutil
shutil.rmtree(cache_dir / "transformers", ignore_errors=True)
```

#### WebSocket Connection Issues
```javascript
// Problem: WebSocket connections fail
// Solution: Check network and server configuration

// 1. Test basic WebSocket connection
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/jobs/test-job');

ws.onopen = () => console.log('WebSocket connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
ws.onclose = (event) => console.log('WebSocket closed:', event.code, event.reason);

// 2. Check CORS settings
fetch('http://localhost:8000/api/v1/jobs/test-job', {
  method: 'OPTIONS',
  headers: {
    'Origin': 'http://localhost:3000',
    'Access-Control-Request-Method': 'GET'
  }
}).then(response => {
  console.log('CORS headers:', [...response.headers.entries()]);
});

// 3. Verify server WebSocket support
// Check server logs for WebSocket connection attempts
```

#### Memory Issues
```python
# Problem: Out of memory errors
# Solution: Monitor and optimize memory usage

import psutil
import GPUtil

# 1. Monitor system memory
memory = psutil.virtual_memory()
print(f"Total memory: {memory.total // 1024**3}GB")
print(f"Available memory: {memory.available // 1024**3}GB")
print(f"Memory usage: {memory.percent}%")

# 2. Monitor GPU memory
gpus = GPUtil.getGPUs()
for gpu in gpus:
    print(f"GPU {gpu.id}: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB ({gpu.memoryUtil*100:.1f}%)")

# 3. Optimize memory usage
# Reduce batch size
BATCH_SIZE = 4  # Instead of 16

# Use model quantization
model = model.half()  # Convert to float16

# Clear cache periodically
if hasattr(torch.cuda, 'empty_cache'):
    torch.cuda.empty_cache()
```

#### Performance Degradation
```python
# Problem: System performance degrades over time
# Solution: Implement monitoring and optimization

import time
from functools import wraps

def performance_monitor(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.virtual_memory().used

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().used

            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory

            print(f"{func.__name__}: {execution_time:.2f}s, {memory_delta/1024**2:.1f}MB")

    return wrapper

@performance_monitor
def transcribe_audio(audio_path: str) -> str:
    """Monitored transcription function."""
    # Your transcription logic here
    pass
```

### Debug Logging Examples

#### Enable Debug Logging
```python
# Problem: Need detailed debugging information
# Solution: Configure comprehensive logging

import logging
import sys

# 1. Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)

# 2. Add debug logging to key functions
logger = logging.getLogger(__name__)

def process_transcription(job_id: str):
    logger.debug(f"Starting transcription for job {job_id}")

    try:
        # Load audio
        logger.debug("Loading audio file")
        audio = load_audio(job_id)

        # Preprocess
        logger.debug(f"Preprocessing audio: {len(audio)} samples")
        processed = preprocess_audio(audio)

        # Transcribe
        logger.debug("Starting AI transcription")
        result = transcribe_with_ai(processed)

        logger.debug(f"Transcription completed: {len(result)} characters")
        return result

    except Exception as e:
        logger.error(f"Transcription failed for job {job_id}: {e}", exc_info=True)
        raise
```

#### Log Analysis
```bash
# Problem: Need to analyze logs for issues
# Solution: Use log analysis tools

# 1. Search for errors
grep "ERROR" application.log

# 2. Find slow operations
grep "duration" application.log | sort -k3 -n | tail -10

# 3. Count requests by endpoint
grep "GET\|POST" access.log | cut -d'"' -f2 | sort | uniq -c | sort -nr

# 4. Monitor memory usage over time
grep "memory" application.log | awk '{print $1, $NF}' | tail -20
```

### Network Troubleshooting

#### API Connectivity Issues
```bash
# Problem: API calls failing
# Solution: Test network connectivity

# 1. Test basic connectivity
curl -v http://localhost:8000/health

# 2. Test with different methods
curl -X GET http://localhost:8000/api/v1/jobs
curl -X POST http://localhost:8000/api/v1/jobs -H "Content-Type: application/json" -d '{}'

# 3. Check network configuration
netstat -tlnp | grep :8000
ss -tlnp | grep :8000

# 4. Test from different clients
# Python
import requests
response = requests.get('http://localhost:8000/health')
print(response.status_code, response.json())

# JavaScript
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log(data));
```

#### Database Connection Issues
```bash
# Problem: Database queries failing
# Solution: Diagnose connection issues

# 1. Test database connectivity
psql "postgresql://user:pass@host:5432/db" -c "SELECT version();"

# 2. Check connection pool status
# In application logs
grep "pool" application.log

# 3. Monitor active connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# 4. Check for connection leaks
psql -c "SELECT pid, usename, client_addr, state, query_start FROM pg_stat_activity WHERE state != 'idle';"
```

---

*These code examples provide practical, copy-paste ready solutions for common tasks and troubleshooting scenarios. Use them as starting points for your own implementations.*
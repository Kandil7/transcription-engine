# Migration Guide

Step-by-step guides for migrating between versions of the SoutiAI Transcription Engine.

## 📋 Table of Contents

### Version Migrations
- [From 0.x to 1.0.0](#from-0x-to-100)
- [From 1.0.x to 1.1.0](#from-10x-to-110)
- [From 1.1.x to 1.2.0](#from-11x-to-120)

### Component Migrations
- [Database Migrations](#database-migrations)
- [API Migrations](#api-migrations)
- [Configuration Migrations](#configuration-migrations)
- [Deployment Migrations](#deployment-migrations)

### Breaking Changes
- [Authentication Changes](#authentication-changes)
- [API Endpoint Changes](#api-endpoint-changes)
- [Configuration Changes](#configuration-changes)
- [Dependency Changes](#dependency-changes)

---

## From 0.x to 1.0.0

### Overview

Version 1.0.0 is a major release that introduces enterprise-grade features, improved Arabic language support, and breaking changes for better scalability and security.

### Breaking Changes

#### 1. Authentication Required

**Before (0.x):**
```bash
# No authentication required
curl "http://localhost:8000/api/v1/jobs"
```

**After (1.0.0):**
```bash
# JWT authentication required
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/api/v1/jobs"
```

**Migration Steps:**
1. Obtain JWT token from authentication endpoint
2. Update all API calls to include `Authorization` header
3. Implement token refresh logic for long-running operations

#### 2. Configuration Environment Variables

**Before (0.x):**
```bash
# Hard-coded configuration
DATABASE_URL="sqlite:///transcription.db"
REDIS_URL="redis://localhost:6379"
```

**After (1.0.0):**
```bash
# Environment variables required
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export REDIS_URL="redis://host:6379"
export JWT_SECRET_KEY="your-secret-key"
export ENCRYPTION_KEY="your-encryption-key"
```

**Migration Steps:**
1. Create `.env` file with required environment variables
2. Update deployment scripts to set environment variables
3. Use secure random keys for production (see [Configuration Guide](CONFIGURATION.md))

#### 3. Database Schema Changes

**Migration Required:**
```bash
# Run database migrations
cd backend
alembic upgrade head

# Or using Docker
docker-compose exec backend alembic upgrade head
```

**Schema Changes:**
- Added `voice_analytics` JSON column to `jobs` table
- Added `hierarchical_summary` JSON column
- Added `text_sample` column for dialect detection
- Added `target_language` column for translations
- Added `summary_length` column for summary customization

#### 4. API Response Format Changes

**Job Status Response Changes:**
```json
// Before (0.x)
{
  "id": "job_123",
  "status": "completed",
  "progress": 100,
  "transcript": "text here...",
  "created_at": "2024-01-01T00:00:00Z"
}

// After (1.0.0)
{
  "id": "job_123",
  "status": "completed",
  "progress": 100.0,
  "message": "Transcription completed successfully",
  "transcript": "text here...",
  "translation": "translation here...",
  "summary": "summary here...",
  "voice_analytics": {...},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "language": "ar",
  "enable_translation": true,
  "processing_stats": {...}
}
```

### Feature Additions

#### 1. Arabic Dialect Detection
```python
# New feature: Automatic dialect detection
job_data = {
    "filename": "arabic_meeting.wav",
    "language": "ar",
    "text_sample": "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده"  # Cairo dialect sample
}

# System automatically detects Egyptian dialect and routes to optimized model
```

#### 2. Voice Analytics
```python
# New feature: Speaker diarization and emotion detection
response = await client.post("/api/v1/voice/job_123/analyze")
# Returns: speaker segments, meeting analysis, emotion detection
```

#### 3. Hierarchical Summarization
```python
# New feature: Multi-level summaries
summaries = {
    "level_1_elevator_pitch": "Brief 30-second summary",
    "level_2_key_points": "Key points in 2 minutes",
    "level_3_comprehensive": "Detailed 5-minute summary"
}
```

#### 4. Real-time Streaming
```javascript
// New feature: WebSocket streaming
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/stream/session_1');

// Real-time transcription results
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Live transcript:', data.text);
};
```

### Migration Steps

#### Step 1: Backup Data
```bash
# Backup existing database
pg_dump transcription_db > backup_pre_1.0.0.sql

# Backup configuration files
cp .env .env.backup
cp docker-compose.yml docker-compose.backup.yml
```

#### Step 2: Update Dependencies
```bash
# Update Python dependencies
pip install -r requirements.txt

# Update Docker images
docker-compose pull

# Clean up old containers
docker-compose down -v
docker system prune -f
```

#### Step 3: Update Configuration
```bash
# Update environment variables
cat >> .env << EOF
# New required variables for 1.0.0
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql://postgres:password@postgres:5432/transcription_db

# Feature flags
ENABLE_VOICE_ANALYTICS=false
ENABLE_RAG=true
ENABLE_STREAMING=true
ENABLE_DIALECT_DETECTION=true
EOF
```

#### Step 4: Run Database Migrations
```bash
# Run Alembic migrations
alembic upgrade head

# Verify migration success
alembic current

# Check data integrity
psql -d transcription_db -c "SELECT COUNT(*) FROM jobs;"
```

#### Step 5: Update Application Code
```python
# Update API client code
import requests

class TranscriptionClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def upload_file(self, file_path: str, **options):
        """Upload file with authentication."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/api/v1/upload/file",
                files=files,
                data=options
            )
        return response.json()
```

#### Step 6: Update Deployment
```yaml
# Update docker-compose.yml
version: '3.8'
services:
  api:
    image: ghcr.io/kandil7/transcription-engine:1.0.0
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    env_file:
      - .env
```

#### Step 7: Test Migration
```bash
# Start services
docker-compose up -d

# Test authentication
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Test file upload with authentication
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' | jq -r '.access_token')

curl -X POST "http://localhost:8000/api/v1/upload/file" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.wav" \
  -F "language=ar"
```

#### Step 8: Monitor and Verify
```bash
# Check logs for errors
docker-compose logs api

# Verify database migration
docker-compose exec postgres psql -U postgres -d transcription_db -c "SELECT * FROM jobs LIMIT 1;"

# Test new features
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/health"
```

### Rollback Plan

If migration fails, rollback steps:

```bash
# Stop new version
docker-compose down

# Restore backup
psql transcription_db < backup_pre_1.0.0.sql

# Restore old configuration
cp .env.backup .env
cp docker-compose.backup.yml docker-compose.yml

# Start old version
docker-compose up -d
```

---

## From 1.0.x to 1.1.0

### Overview

Version 1.1.0 focuses on performance improvements, additional language support, and enhanced Arabic processing capabilities.

### New Features

#### 1. Enhanced Arabic Language Support
```python
# Support for additional Arabic dialects
supported_dialects = [
    "egyptian_cairo", "egyptian_alexandria", "saudi_riyadh",
    "uae_dubai", "levant_beirut", "morocco_rabat"
]

# Automatic dialect detection with confidence scores
result = await transcription_service.transcribe_with_dialect_adaptation(
    audio_path="meeting.wav",
    language="ar",
    text_sample="كيف الحال يا جماعة"
)
# Returns: transcript, dialect_info, confidence_score
```

#### 2. Performance Optimizations
```python
# Model caching and preloading
model_cache = ModelCache(max_memory_gb=8)
model_cache.preload_model("large-v3-arabic")

# Batch processing for multiple files
batch_processor = BatchTranscriptionProcessor(batch_size=4)
results = await batch_processor.process_batch(audio_files)
```

#### 3. Advanced Voice Analytics
```python
# Enhanced emotion detection
emotions = await voice_analytics_service.analyze_emotions(
    audio_path="meeting.wav",
    enable_sentiment_analysis=True,
    enable_speaker_overlap_detection=True
)

# Meeting insights
insights = await voice_analytics_service.generate_meeting_insights(
    speaker_segments=segments,
    include_participation_metrics=True,
    include_conversation_flow=True
)
```

### Breaking Changes

#### 1. Voice Analytics API Changes
```python
# Before (1.0.x)
response = await client.post("/api/v1/voice/analyze", data=job_data)

// After (1.1.0)
response = await client.post("/api/v1/voice/job_123/analyze")
# Returns enhanced analytics with sentiment and participation metrics
```

#### 2. Configuration Changes
```bash
# New configuration options
ENABLE_ADVANCED_VOICE_ANALYTICS=true
ENABLE_BATCH_PROCESSING=true
MODEL_CACHE_SIZE_GB=8
ARABIC_DIALECT_EXPANSION=true
```

### Migration Steps

1. **Update Configuration**
   ```bash
   echo "ENABLE_ADVANCED_VOICE_ANALYTICS=true" >> .env
   echo "MODEL_CACHE_SIZE_GB=8" >> .env
   ```

2. **Update API Calls**
   ```python
   # Update voice analytics calls
   old: client.post("/api/v1/voice/analyze", data=job_data)
   new: client.post(f"/api/v1/voice/{job_id}/analyze")
   ```

3. **Deploy New Version**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

---

## From 1.1.x to 1.2.0

### Overview

Version 1.2.0 introduces multi-modal processing, GraphQL API, and advanced AI model orchestration.

### Major Changes

#### 1. GraphQL API (Optional)
```graphql
# New GraphQL endpoint alongside REST API
query GetTranscriptionJob($id: ID!) {
  job(id: $id) {
    id
    status
    transcript
    translation
    voiceAnalytics {
      speakers {
        id
        name
        speakingTime
        emotion
      }
      meetingInsights {
        participationScore
        conversationFlow
      }
    }
  }
}
```

#### 2. Multi-Modal Processing
```python
# Video processing with scene detection
video_processor = VideoProcessor(enable_scene_detection=True)
result = await video_processor.process_video(
    video_path="meeting.mp4",
    extract_slides=True,
    generate_chapters=True
)
# Returns: transcript, scene_timestamps, slide_images, chapters
```

#### 3. Advanced AI Orchestration
```python
# Model ensemble for improved accuracy
orchestrator = AIModelOrchestrator([
    "whisper-large-v3",
    "whisper-medium-arabic-finetuned",
    "wav2vec2-arabic"
])

result = await orchestrator.transcribe_with_ensemble(
    audio_path="complex_audio.wav",
    language="ar",
    use_confidence_weighting=True
)
```

### Migration Steps

1. **Enable New Features Gradually**
   ```bash
   # Add to .env (optional)
   ENABLE_GRAPHQL_API=false  # Enable when ready
   ENABLE_MULTIMODAL_PROCESSING=false
   ENABLE_MODEL_ENSEMBLE=false
   ```

2. **Update Client Code (Optional)**
   ```javascript
   // Optional: Use GraphQL for complex queries
   const client = new GraphQLClient('/graphql');
   const query = gql`...`;
   const result = await client.request(query);
   ```

3. **Test New Features**
   ```bash
   # Test in staging environment first
   # Enable features gradually
   # Monitor performance impact
   ```

---

## Database Migrations

### Alembic Migration Scripts

#### Creating New Migrations
```bash
# Generate new migration
alembic revision -m "add_voice_analytics_table"

# Edit migration file
# alembic/versions/xxxxx_add_voice_analytics_table.py
```

#### Common Migration Patterns

**Adding New Columns:**
```python
def upgrade():
    op.add_column('jobs', sa.Column('voice_analytics', sa.JSON(), nullable=True))
    op.add_column('jobs', sa.Column('processing_stats', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('jobs', 'voice_analytics')
    op.drop_column('jobs', 'processing_stats')
```

**Creating New Tables:**
```python
def upgrade():
    op.create_table(
        'voice_analytics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('jobs.id')),
        sa.Column('speakers', sa.JSON()),
        sa.Column('emotions', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True))
    )

def downgrade():
    op.drop_table('voice_analytics')
```

**Data Migrations:**
```python
def upgrade():
    # Migrate existing data
    connection = op.get_bind()

    # Example: Add default values to new columns
    connection.execute(
        sa.text("""
            UPDATE jobs
            SET voice_analytics = '{}',
                processing_stats = '{"migrated": true}'
            WHERE voice_analytics IS NULL
        """)
    )
```

### Database Backup and Recovery

#### Pre-Migration Backup
```bash
# Create backup before migration
pg_dump -U postgres -h localhost transcription_db > backup_$(date +%Y%m%d_%H%M%S).sql

# For large databases, use compressed backup
pg_dump -U postgres -h localhost transcription_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### Post-Migration Verification
```bash
# Verify data integrity
psql -U postgres -d transcription_db -c "
SELECT COUNT(*) as total_jobs FROM jobs;
SELECT COUNT(*) as jobs_with_analytics FROM jobs WHERE voice_analytics IS NOT NULL;
SELECT COUNT(*) as jobs_with_stats FROM jobs WHERE processing_stats IS NOT NULL;
"
```

#### Rollback Procedures
```bash
# Stop application
docker-compose down

# Restore from backup
psql -U postgres -d transcription_db < backup_20240101_120000.sql

# Downgrade migration
alembic downgrade -1

# Restart application
docker-compose up -d
```

---

## API Migrations

### REST API Evolution

#### v1 API Structure
```
GET    /api/v1/jobs                 # List jobs
GET    /api/v1/jobs/{id}            # Get job details
POST   /api/v1/jobs                 # Create job
PUT    /api/v1/jobs/{id}            # Update job
DELETE /api/v1/jobs/{id}            # Delete job
GET    /api/v1/jobs/{id}/results    # Get results

POST   /api/v1/upload/file          # Upload file
GET    /api/v1/files/{id}           # Get file info

WebSocket /api/v1/ws/jobs/{id}      # Job updates
WebSocket /api/v1/ws/stream/{id}    # Streaming

POST   /api/v1/qa/{job_id}/ask      # Q&A
POST   /api/v1/voice/{job_id}/analyze # Voice analytics
POST   /api/v1/translate/text       # Translation
POST   /api/v1/summarize/text       # Summarization
```

#### API Versioning Strategy
- **v1**: Current stable API
- **Headers**: `Accept: application/vnd.transcription.v1+json`
- **Deprecation**: 12-month deprecation period
- **Breaking Changes**: New major version

### Client Library Updates

#### Python Client Migration
```python
# Before (0.x)
from transcription_client import Client

client = Client(api_key="key")
result = client.transcribe("audio.wav", language="ar")

# After (1.0.0)
from transcription_client import TranscriptionClient

client = TranscriptionClient(api_key="key", base_url="https://api.yourdomain.com")
job = client.upload_file("audio.wav", language="ar")
result = client.get_job_results(job["job_id"])
```

#### JavaScript Client Migration
```javascript
// Before (0.x)
const client = new TranscriptionClient({ apiKey: 'key' });
const result = await client.transcribeFile(file);

// After (1.0.0)
const client = new TranscriptionClient({
  apiKey: 'key',
  baseUrl: 'https://api.yourdomain.com'
});

const job = await client.uploadFile(file, { language: 'ar' });
const result = await client.getJobResults(job.jobId);
```

---

## Configuration Migrations

### Environment Variables Evolution

#### Version 1.0.0 Required Variables
```bash
# Core Application
APP_NAME=TranscriptionEngine
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Security (REQUIRED)
JWT_SECRET_KEY=your-32-char-secret-key
ENCRYPTION_KEY=your-32-byte-encryption-key

# Database (REQUIRED)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis (REQUIRED)
REDIS_URL=redis://host:6379/0

# Storage
STORAGE_TYPE=minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

#### Version 1.1.0 New Variables
```bash
# Performance Tuning
MODEL_CACHE_SIZE_GB=8
BATCH_PROCESSING_ENABLED=true
GPU_MEMORY_FRACTION=0.9

# Advanced Features
ENABLE_ADVANCED_VOICE_ANALYTICS=true
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_SPEAKER_OVERLAP_DETECTION=true

# Arabic Enhancements
ARABIC_DIALECT_EXPANSION=true
MSA_FALLBACK_ENABLED=true
```

### Configuration Validation

#### Schema Validation
```python
from pydantic import BaseSettings, validator
import os

class AppConfig(BaseSettings):
    """Validated application configuration."""

    # Required settings
    jwt_secret_key: str
    database_url: str
    redis_url: str

    # Optional with defaults
    debug: bool = False
    max_file_size_mb: int = 500

    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret must be at least 32 characters')
        return v

    @validator('database_url')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'sqlite://')):
            raise ValueError('Invalid database URL format')
        return v

    class Config:
        env_file = '.env'
        case_sensitive = False

# Usage
config = AppConfig()
```

---

## Deployment Migrations

### Docker Compose Evolution

#### From 0.x to 1.0.0
```yaml
# 0.x - Simple setup
version: '3.8'
services:
  app:
    image: transcription-engine:latest
    ports:
      - "8000:8000"

# 1.0.0 - Enterprise setup
version: '3.8'
services:
  api:
    image: ghcr.io/kandil7/transcription-engine:1.0.0
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
    secrets:
      - jwt_secret
      - db_credentials

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: transcription_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio:latest
    volumes:
      - minio_data:/data
```

### Kubernetes Migration

#### Helm Chart Migration
```bash
# Install Helm chart
helm repo add transcription-engine https://charts.yourdomain.com
helm install transcription-engine transcription-engine/transcription-engine

# Upgrade with new values
helm upgrade transcription-engine transcription-engine/transcription-engine \
  --values values-1.0.0.yaml
```

#### Manual Kubernetes Migration
```bash
# Update deployments
kubectl apply -f k8s/api-deployment-1.0.0.yaml
kubectl apply -f k8s/worker-deployment-1.0.0.yaml

# Update configmaps and secrets
kubectl apply -f k8s/configmap-1.0.0.yaml
kubectl apply -f k8s/secret-1.0.0.yaml

# Run database migrations in pod
kubectl exec -it deployment/transcription-api -- alembic upgrade head

# Update ingress
kubectl apply -f k8s/ingress-1.0.0.yaml
```

---

## Breaking Changes Reference

### Authentication Changes

| Version | Change | Impact | Migration |
|---------|--------|--------|-----------|
| 1.0.0 | JWT authentication required | All API calls need auth headers | Add Authorization header to all requests |
| 1.0.0 | API key rotation | Existing keys become invalid | Generate new API keys |
| 1.1.0 | MFA support added | Optional but recommended | Configure MFA in user settings |

### API Endpoint Changes

| Version | Endpoint | Change | Migration |
|---------|----------|--------|-----------|
| 1.0.0 | `/api/v1/jobs/{id}/results` | New endpoint added | Use new endpoint for results |
| 1.0.0 | `/api/v1/voice/analyze` | Endpoint restructured | Change to `/api/v1/voice/{job_id}/analyze` |
| 1.1.0 | `/api/v1/qa/setup` | Parameters changed | Update setup calls with new parameters |

### Configuration Changes

| Version | Variable | Change | Migration |
|---------|----------|--------|-----------|
| 1.0.0 | `SECRET_KEY` | Now required, min 32 chars | Generate secure random key |
| 1.0.0 | `DATABASE_URL` | PostgreSQL required | Migrate from SQLite to PostgreSQL |
| 1.0.0 | `REDIS_URL` | Now required | Set up Redis instance |
| 1.1.0 | `MODEL_CACHE_SIZE_GB` | New performance tuning | Set appropriate cache size |

### Dependency Changes

| Version | Dependency | Change | Migration |
|---------|------------|--------|-----------|
| 1.0.0 | Python | 3.11+ required | Upgrade Python version |
| 1.0.0 | Database | PostgreSQL required | Migrate database |
| 1.0.0 | Cache | Redis required | Set up Redis |
| 1.1.0 | GPU Memory | Increased requirements | Upgrade GPU or reduce batch sizes |

---

## Support and Troubleshooting

### Getting Help

1. **Check Documentation**: Review this migration guide and version-specific docs
2. **Search Issues**: Check GitHub issues for similar migration problems
3. **Community Support**: Ask in GitHub Discussions
4. **Enterprise Support**: Contact support team for priority assistance

### Common Migration Issues

#### Database Migration Failures
```bash
# Check migration status
alembic current

# Fix failed migration
alembic downgrade -1  # Rollback
alembic upgrade head  # Retry

# Manual fix if needed
psql -d transcription_db -f manual_fix.sql
```

#### Authentication Issues
```bash
# Test token generation
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Verify token works
TOKEN=$(...)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/health"
```

#### Configuration Errors
```bash
# Validate configuration
python -c "from app.config import settings; print('Config OK')"

# Check environment variables
env | grep -E "(DATABASE|REDIS|JWT)"

# Test database connection
python -c "from app.db.session import engine; print('DB OK')"
```

### Rollback Procedures

#### Complete Rollback to Previous Version
```bash
# 1. Stop current version
docker-compose down

# 2. Restore database backup
psql transcription_db < backup_pre_migration.sql

# 3. Restore configuration
cp .env.backup .env

# 4. Restore docker-compose
cp docker-compose.backup.yml docker-compose.yml

# 5. Start previous version
docker-compose up -d

# 6. Verify functionality
curl http://localhost:8000/health
```

---

*For additional migration assistance, please refer to the [Troubleshooting Guide](TROUBLESHOOTING.md) or contact support.*
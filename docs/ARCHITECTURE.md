# System Architecture

Comprehensive technical architecture of the SoutiAI Transcription Engine.

## Overview

The Transcription Engine is a distributed, microservices-based system designed for high-performance AI transcription with Arabic language specialization.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Web Frontend  │  │   Mobile Apps   │  │    REST API     │         │
│  │   (React)       │  │   (React Native)│  │   (Postman)     │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API Gateway Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │    Traefik      │  │   Rate Limit    │  │ Authentication  │         │
│  │  Load Balancer  │  │   & Throttle    │  │   (JWT/OAuth)   │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   FastAPI App   │  │   WebSocket     │  │   Background     │         │
│  │   (Sync APIs)   │  │   Server        │  │   Workers        │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Processing Layer                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │Transcription Svc│  │Translation Svc │  │Summarization Svc│         │
│  │                 │  │                 │  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Voice Analytics │  │   RAG Service   │  │ Streaming Svc   │         │
│  │                 │  │                 │  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Data Layer                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  PostgreSQL     │  │   ChromaDB      │  │    Redis        │         │
│  │  (Metadata)     │  │   (Vectors)     │  │  (Cache/Queue)  │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│  ┌─────────────────┐  ┌─────────────────┐                             │
│  │   MinIO/S3      │  │  File System    │                             │
│  │  (Media Files)  │  │  (Temp Files)   │                             │
│  └─────────────────┘  └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Infrastructure Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Kubernetes    │  │    Docker       │  │   Monitoring     │         │
│  │  Orchestration  │  │  Containers     │  │   Stack          │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Client Layer

#### Web Frontend (React)
- **Framework**: React 18 with Material-UI
- **State Management**: React Context + Redux Toolkit
- **Real-time Updates**: WebSocket connections
- **File Upload**: Drag & drop with progress tracking
- **Responsive Design**: Mobile-first approach

**Key Components**:
- `Upload.js`: File upload with dialect detection
- `JobDetails.js`: Results visualization
- `Streaming.js`: Live transcription interface
- `Dashboard.js`: Job management dashboard

#### REST API Clients
- **SDKs**: Python, JavaScript, Go
- **Authentication**: JWT token management
- **Retry Logic**: Exponential backoff
- **Rate Limiting**: Client-side throttling

### 2. API Gateway Layer

#### Traefik Load Balancer
- **Protocol Support**: HTTP/1.1, HTTP/2, WebSocket
- **SSL Termination**: Let's Encrypt integration
- **Service Discovery**: Docker/Kubernetes integration
- **Middleware**: Authentication, CORS, compression

#### Security Layer
- **Authentication**: JWT + OAuth2
- **Authorization**: Role-based access control
- **Rate Limiting**: Distributed rate limiting with Redis
- **Input Validation**: Pydantic models with custom validators

### 3. Application Layer

#### FastAPI Application
- **Framework**: FastAPI with async support
- **Documentation**: Auto-generated OpenAPI/Swagger
- **Middleware**: CORS, logging, error handling
- **Background Tasks**: Integration with Celery

**Core Modules**:
```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── api/v1/              # API endpoints
├── services/            # Business logic
├── db/                  # Database models & session
├── tasks/               # Celery tasks
└── utils/               # Helper utilities
```

#### WebSocket Server
- **Protocol**: RFC 6455 WebSocket
- **Message Types**: JSON-based protocol
- **Connection Management**: Connection pooling
- **Real-time Updates**: Job progress, streaming transcription

### 4. Processing Layer

#### Transcription Service
**Architecture**:
```
TranscriptionService
├── AdaptiveEngine          # Hardware detection & profiling
├── ModelManager           # Model loading & caching
├── AudioProcessor         # Audio preprocessing
├── DialectDetector        # Egyptian dialect detection
└── BatchProcessor         # Parallel processing
```

**Supported Models**:
- **Primary**: Faster-Whisper (large-v3, large-v2, medium)
- **Fine-tuned**: Egyptian dialect models (Cairo, Alexandria, Upper Egypt, Delta)
- **Fallback**: OpenAI Whisper API

#### Translation Service
- **Model**: NLLB-200 (200 languages)
- **Post-processing**: Arabic-specific improvements
- **Caching**: Redis-based translation cache
- **Batch Processing**: Multiple translations in parallel

#### Summarization Service
- **Models**: BART, T5, Pegasus
- **Hierarchical Summaries**: Multi-level summaries
- **Arabic Optimization**: AraBART integration
- **Customization**: Length and style control

#### Voice Analytics Service
```
VoiceAnalyticsService
├── SpeakerDiarization      # PyAnnote-based
├── EmotionDetection        # Wav2Vec2-based
├── AudioSegmentation       # VAD-based
└── MeetingAnalysis         # Statistical analysis
```

#### RAG Service
```
RAGService
├── DocumentProcessor       # Text chunking & embedding
├── VectorStore            # ChromaDB integration
├── Retriever              # Semantic search
└── Generator              # Context-aware Q&A
```

### 5. Data Layer

#### PostgreSQL Database
**Schema Design**:
```sql
-- Jobs table
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    progress FLOAT,
    language VARCHAR(10) DEFAULT 'ar',

    -- Processing options
    enable_translation BOOLEAN DEFAULT TRUE,
    enable_summary BOOLEAN DEFAULT TRUE,
    text_sample TEXT,

    -- Results
    transcript TEXT,
    translation TEXT,
    summary TEXT,
    hierarchical_summary JSONB,
    voice_analytics JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_stats JSONB,
    processing_profile VARCHAR(50)
);

-- Indexes for performance
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_language ON jobs(language);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
```

#### ChromaDB Vector Store
- **Collections**: Separate collections per job
- **Embeddings**: Arabic-optimized sentence transformers
- **Indexing**: HNSW for fast similarity search
- **Persistence**: Local file system with backup

#### Redis Cache/Queue
- **Data Types**: Strings, Hashes, Lists, Sets
- **Use Cases**:
  - Job queue management
  - Translation caching
  - Session management
  - Rate limiting counters

#### MinIO Object Storage
- **Buckets**: Separate buckets for different data types
- **Lifecycle**: Automatic cleanup of temporary files
- **CDN Integration**: CloudFront/S3 for global distribution
- **Encryption**: Server-side encryption

### 6. Infrastructure Layer

#### Docker Containerization
```yaml
# Multi-stage Dockerfile
FROM python:3.11-slim as base
# ... base dependencies

FROM base as builder
# ... build dependencies

FROM base as production
# ... production image
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --no-deps /wheels/*
```

#### Kubernetes Orchestration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: transcription-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: transcription-api
  template:
    spec:
      containers:
      - name: api
        image: souti/transcription:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

#### Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **AlertManager**: Alert routing and management
- **Node Exporter**: System metrics
- **Custom Metrics**: Application-specific monitoring

## Performance Architecture

### Adaptive Resource Management

#### Hardware Profiles
```python
class HardwareProfile:
    ULTRA = {
        "gpu_memory": "24GB+",
        "cpu_cores": "8+",
        "ram": "32GB+",
        "model": "large-v3",
        "batch_size": 8,
        "compute_type": "float16"
    }

    STD_GPU = {
        "gpu_memory": "8GB+",
        "cpu_cores": "4+",
        "ram": "16GB+",
        "model": "large-v2",
        "batch_size": 4,
        "compute_type": "int8_float16"
    }

    CPU_STRONG = {
        "gpu_memory": "0GB",
        "cpu_cores": "8+",
        "ram": "32GB+",
        "model": "medium",
        "batch_size": 2,
        "compute_type": "int8"
    }

    EDGE_WEAK = {
        "gpu_memory": "0GB",
        "cpu_cores": "2+",
        "ram": "8GB+",
        "model": "base",
        "batch_size": 1,
        "compute_type": "int8"
    }
```

#### Dynamic Scaling
- **Horizontal Pod Autoscaling**: Based on CPU/memory usage
- **Queue-based Scaling**: Scale workers based on job queue length
- **Predictive Scaling**: ML-based scaling predictions

### Caching Strategy

#### Multi-level Caching
1. **Application Cache**: Redis for frequently accessed data
2. **Model Cache**: GPU memory for loaded models
3. **File Cache**: Local SSD for recently processed files
4. **CDN Cache**: CloudFront for static assets

#### Cache Invalidation
- **Time-based**: TTL for temporary data
- **Event-based**: Invalidate on model updates
- **Size-based**: LRU eviction for memory constraints

### Data Flow Architecture

#### File Processing Pipeline
```
Upload → Validation → Queue → Worker → Processing → Storage → Notification
     ↓         ↓         ↓       ↓         ↓          ↓         ↓
   File     Format    Redis   Celery    AI Models  MinIO     Webhook
   Type     Check     Queue   Tasks     Inference  S3       Email
```

#### Real-time Streaming Flow
```
Client ↔ WebSocket ↔ Stream Service ↔ Audio Buffer ↔ Model → Results
   ↑           ↑            ↑              ↑            ↑         ↓
Browser    Gateway      Worker        Queue       Inference  Client
```

## Security Architecture

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication
- **OAuth2**: Third-party integration
- **API Keys**: Service-to-service authentication
- **Role-based Access**: Admin, User, Service roles

### Data Protection
- **Encryption at Rest**: AES-256 for database and storage
- **Encryption in Transit**: TLS 1.3 for all communications
- **Input Sanitization**: Comprehensive validation
- **Output Encoding**: XSS prevention

### Network Security
- **Firewall Rules**: Restrictive ingress/egress
- **VPC Isolation**: Network segmentation
- **DDoS Protection**: Cloudflare integration
- **Rate Limiting**: Distributed rate limiting

## Scalability Design

### Horizontal Scaling
- **Stateless Services**: All services can be scaled horizontally
- **Shared Database**: PostgreSQL with read replicas
- **Distributed Cache**: Redis cluster for high availability
- **Load Balancing**: Traefik with session affinity

### Performance Optimization
- **Connection Pooling**: Database and Redis connection pools
- **Async Processing**: Non-blocking I/O operations
- **Memory Management**: GPU memory optimization
- **Batch Processing**: Parallel processing of multiple requests

## Reliability Architecture

### Fault Tolerance
- **Circuit Breakers**: Automatic failure detection
- **Retry Logic**: Exponential backoff with jitter
- **Graceful Degradation**: Fallback to simpler models
- **Health Checks**: Comprehensive health monitoring

### Backup & Recovery
- **Database Backups**: Automated daily backups
- **File Backups**: Cross-region replication
- **Disaster Recovery**: Multi-region failover
- **Point-in-time Recovery**: Database snapshots

## Observability Architecture

### Metrics Collection
- **Application Metrics**: Request latency, error rates
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Job completion rates, accuracy scores
- **Custom Metrics**: Dialect detection confidence, model performance

### Logging Strategy
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Centralized Logging**: ELK stack integration
- **Log Retention**: 30-day retention with compression

### Alerting Rules
```yaml
groups:
- name: transcription.alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical

  - alert: JobQueueBacklog
    expr: celery_queue_length > 100
    for: 10m
    labels:
      severity: warning
```

## Deployment Architecture

### Development Environment
- **Local Development**: Docker Compose with hot reload
- **Testing**: GitHub Actions CI/CD pipeline
- **Staging**: Mirror of production environment

### Production Environment
- **Kubernetes Cluster**: Managed Kubernetes service
- **Load Balancing**: Traefik ingress controller
- **SSL Termination**: Let's Encrypt certificates
- **Monitoring**: Full observability stack

### Configuration Management
- **Environment Variables**: 12-factor app configuration
- **Secrets Management**: Kubernetes secrets or AWS Secrets Manager
- **Feature Flags**: Runtime feature toggling
- **Configuration Validation**: Schema validation on startup

## API Design Principles

### RESTful Design
- **Resource-based URLs**: `/api/v1/jobs/{id}`
- **HTTP Methods**: GET, POST, PUT, DELETE
- **Status Codes**: Standard HTTP status codes
- **Content Negotiation**: JSON by default

### WebSocket Protocol
- **Message Types**: `progress_update`, `transcription`, `error`
- **Connection Lifecycle**: `connect` → `authenticate` → `subscribe` → `disconnect`
- **Error Handling**: Graceful error messages with recovery options

### Versioning Strategy
- **URL Versioning**: `/api/v1/` prefix
- **Backward Compatibility**: API evolution without breaking changes
- **Deprecation Notices**: Advance notice for API changes
- **Migration Guides**: Documentation for API updates

This architecture provides a robust, scalable, and maintainable foundation for the Transcription Engine, designed to handle enterprise workloads while maintaining high performance and reliability.</content>
</xai:function_call">ARCHITECTURE.md
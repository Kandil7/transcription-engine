# SoutiAI Transcription Engine - Project Context

## Project Overview

The SoutiAI Transcription Engine is an enterprise-grade AI transcription, translation, and analysis engine specifically optimized for Arabic content with exceptional accuracy for Egyptian dialects. This comprehensive system combines cutting-edge AI technologies with robust infrastructure to deliver real-time and batch transcription services.

### Key Features
- **Egyptian Arabic Excellence**: 19% Word Error Rate (WER) improvement with dialect detection and fine-tuned models
- **Real-time Streaming**: Guaranteed 2-second latency for live transcription
- **AI-Powered Intelligence**: RAG integration, intelligent Q&A, voice analytics, hierarchical summarization
- **Enterprise-Grade**: Production monitoring, security-first approach, horizontal scaling
- **Multi-language Support**: 200+ language translation with Arabic optimization
- **Modern UI/UX**: Interactive React-based dashboard with timeline, search, and real-time updates

### Technology Stack
- **Backend**: FastAPI + Python 3.11 with async support
- **AI Engine**: Faster-Whisper, NLLB, PyAnnote for state-of-the-art transcription
- **Database**: PostgreSQL + ChromaDB for structured data and vector storage
- **Cache/Queue**: Redis + Celery for high-performance caching and task processing
- **Storage**: MinIO/S3 for scalable object storage
- **Frontend**: React + Material-UI for modern, responsive UI
- **Infrastructure**: Docker + Kubernetes for container orchestration
- **Monitoring**: Prometheus + Grafana for observability

## Project Structure

```
transcription-engine/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── db/            # Database layer
│   │   ├── models/        # Pydantic models
│   │   ├── utils/         # Utilities
│   │   └── core/          # Core functionality
│   ├── tests/             # Test suite
│   ├── scripts/           # Utility scripts
│   ├── requirements.txt   # Production dependencies
│   └── Dockerfile        # Container definition
├── frontend/              # React application
├── docs/                  # Documentation
├── k8s/                   # Kubernetes manifests
├── monitoring/            # Observability stack
├── scripts/               # Deployment scripts
├── docker-compose*.yml    # Docker configurations
└── README.md             # Project documentation
```

## Building and Running

### Quick Start (Docker - Recommended)
```bash
# Clone repository
git clone https://github.com/Kandil7/transcription-engine.git
cd transcription-engine

# Start complete system
docker-compose up -d

# Access services:
# - Frontend Dashboard: http://localhost:3000
# - API & Documentation: http://localhost:8000/docs
# - Monitoring Dashboard: http://localhost:3001 (admin/admin)
# - File Storage: http://localhost:9001 (minioadmin/minioadmin)
```

### Development Setup
```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd frontend
npm install
npm start
```

### Manual Setup (Windows PowerShell)
```powershell
# Run setup script
.\setup_manual.ps1

# Start development server
python start_dev.py
```

## Development Conventions

### Code Quality
- **Formatting**: Black and isort for Python, Prettier for JavaScript
- **Linting**: Flake8 for Python, ESLint for JavaScript
- **Type Checking**: MyPy for Python
- **Testing**: Pytest with 80%+ coverage requirement
- **Pre-commit Hooks**: Automatically run formatting and linting

### Architecture Patterns
- **API Design**: RESTful endpoints following FastAPI best practices
- **Async Processing**: Celery workers for background tasks
- **Caching Strategy**: Multi-level caching with Redis
- **Security**: JWT authentication, rate limiting, input validation
- **Error Handling**: Comprehensive exception handling with structured logging

### Testing Strategy
- **Unit Tests**: Individual functions and classes (70% of test pyramid)
- **Integration Tests**: Component interactions (20% of test pyramid)
- **E2E Tests**: Complete user workflows (10% of test pyramid)
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability assessment

## Key Configuration

### Environment Variables
The system uses extensive configuration through environment variables:

- **Database**: `DATABASE_URL`, connection pooling settings
- **AI Models**: `DETECTED_PROFILE`, `WHISPER_MODEL_SIZE`, dialect detection
- **Security**: `JWT_SECRET_KEY`, rate limiting, encryption
- **Features**: Toggle RAG, voice analytics, streaming, translation
- **Monitoring**: Prometheus, Sentry, health checks

### Hardware Profiles
The system automatically adapts to different hardware configurations:
- **ULTRA**: RTX 4090 (24GB+) - 3-5 min processing for 1-hour video
- **STD_GPU**: RTX 3060 (8GB+) - 7-10 min processing for 1-hour video
- **CPU_STRONG**: High-end CPU - 20-30 min processing for 1-hour video
- **EDGE_WEAK**: Low-end hardware - 45-60 min processing for 1-hour video

## API Usage Examples

### Basic Transcription
```bash
curl -X POST "http://localhost:8000/api/v1/upload/file" \
  -F "file=@meeting.mp3" \
  -F "language=ar"
```

### Egyptian Dialect-Optimized
```bash
curl -X POST "http://localhost:8000/api/v1/upload/file" \
  -F "file=@egyptian_meeting.mp3" \
  -F "language=ar" \
  -F "text_sample=أهلاً يا جماعة إحنا هنتكلم عن المشروع ده" \
  -F "enable_translation=true" \
  -F "target_language=en" \
  -F "enable_voice_analytics=true"
```

### Real-time Streaming
```bash
# Start streaming session
curl -X POST "http://localhost:8000/api/v1/stream/my-session/start" \
  -H "Content-Type: application/json" \
  -d '{"language": "ar", "enable_translation": true}'

# WebSocket connection for real-time updates
# ws://localhost:8000/api/v1/ws/stream/my-session
```

## Development Workflow

### Feature Development
1. Create feature branch: `git checkout -b feature/your-feature-name`
2. Make changes following code quality standards
3. Write tests covering new functionality
4. Run quality checks: `pre-commit run --all-files`
5. Run tests: `pytest tests/ -v --cov=app`
6. Commit with conventional commits: `git commit -m "feat: description"`
7. Push and create pull request

### Testing Commands
```bash
# Backend tests with coverage
cd backend
pytest tests/ -v --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report

# Frontend tests
cd frontend
npm test

# Run all quality checks
pre-commit run --all-files
```

## Infrastructure and Deployment

### Docker Compose Environments
- **Production**: `docker-compose.prod.yml` - Optimized for performance and security
- **Development**: `docker-compose.dev.yml` - Hot reload and development tools
- **Default**: `docker-compose.yml` - Standard development environment

### Kubernetes Deployment
The system includes comprehensive Kubernetes manifests in the `k8s/` directory with:
- Namespace and configuration management
- Database, cache, and storage deployments
- API and worker deployments with auto-scaling
- Monitoring and alerting configurations

### Monitoring and Observability
- **Metrics**: Prometheus with custom application metrics
- **Visualization**: Grafana with pre-built dashboards
- **Alerting**: AlertManager for incident response
- **Logging**: Structured JSON logging with rotation
- **Tracing**: Distributed tracing for performance analysis

## Security and Compliance

### Authentication and Authorization
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Role-based Access**: Viewer, User, Editor, Admin roles with granular permissions
- **API Keys**: Alternative authentication method with rate limiting
- **Rate Limiting**: Distributed rate limiting using Redis

### Data Protection
- **Encryption at Rest**: AES-256 for sensitive data
- **Encryption in Transit**: TLS 1.3 for all communications
- **Input Validation**: Comprehensive validation and sanitization
- **Audit Logging**: Complete request/response logging for compliance

### Compliance Standards
- **GDPR**: Data retention policies, right to be forgotten
- **SOX**: Immutable audit trails, change management
- **Industry-specific**: Configurable compliance settings

## Performance and Scalability

### Benchmarks
- **Accuracy**: 95%+ for Egyptian Arabic, 98% for general content
- **Speed**: 1-hour video in 3-7 minutes (hardware adaptive)
- **Reliability**: 99.9% uptime with enterprise monitoring
- **Scalability**: 1000+ concurrent jobs with horizontal scaling

### Resource Utilization
- **Memory**: 12GB+ for model loading, 200MB per concurrent job
- **Storage**: Original file size + 10% overhead for processed files
- **Compute**: Adaptive based on hardware profile detection

## Troubleshooting

### Common Issues
- **API Not Starting**: Check environment variables and database connectivity
- **Transcription Failing**: Verify model loading and file format compatibility
- **WebSocket Issues**: Check CORS settings and connection handling
- **Performance Issues**: Monitor system resources and queue lengths

### Debugging Strategies
- Use structured logging for traceability
- Enable debug mode for detailed error information
- Monitor system metrics for performance bottlenecks
- Check health endpoints for service status

## Learning Resources

### Documentation Suite
- **API Reference**: Complete REST API with examples
- **Architecture Guide**: System design and data flow
- **Development Guide**: Setup, standards, contributions
- **Configuration Guide**: Environment variables and settings
- **Testing Guide**: Unit, integration, performance testing
- **Troubleshooting**: Issues and solutions
- **Egyptian Dialect Guide**: Arabic optimization techniques
- **Production Deployment**: Enterprise deployment

### Development Path
1. **Week 1**: Environment setup and basic API understanding
2. **Weeks 2-3**: Core development and database integration
3. **Weeks 4-6**: AI integration and async processing
4. **Weeks 7-8**: Advanced features and real-time capabilities
5. **Weeks 9-10**: Production readiness and monitoring
6. **Weeks 11-12**: Independent development and mentoring
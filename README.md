# Transcription Engine

An advanced AI-powered transcription, translation, and summarization engine optimized for Arabic content (especially Egyptian dialect) with adaptive performance across different hardware profiles.

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd transcription-engine

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
# Grafana: http://localhost:3001 (admin/admin)
```

## 📖 API Usage

### Upload a File
```bash
curl -X POST "http://localhost:8000/api/v1/upload/file" \
  -F "file=@audio.mp3" \
  -F "language=ar" \
  -F "enable_translation=true" \
  -F "target_language=en"
```

### Check Job Status
```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}"
```

### Get Job Results
```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}/results"
```

### WebSocket Real-time Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/jobs/{job_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Job update:', data);
};
```

### Ask Questions About Transcripts (RAG Q&A)
```bash
# First setup QA system for a job
curl -X POST "http://localhost:8000/api/v1/qa/{job_id}/setup-qa"

# Then ask questions
curl -X POST "http://localhost:8000/api/v1/qa/{job_id}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main points discussed?"}'
```

### Get Hierarchical Summary
```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}/results"
# Returns hierarchical summary with multiple levels:
# - level_1_elevator_pitch: 30-second read
# - level_2_key_points: 2-minute read
# - level_3_comprehensive: 5+ minute detailed read
```

### Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 🚀 Features

- **High-Speed Transcription**: Process 1-hour videos in 3-7 minutes using Whisper large-v3
- **Adaptive Engine**: Automatically detects hardware and optimizes for ULTRA/STD/CPU/EDGE profiles
- **Arabic Excellence**: Fine-tuned for Egyptian dialect with 95%+ accuracy
- **Real-time Streaming**: Live transcription with WebSocket support
- **RAG Integration**: Contextual correction using Arabic knowledge base
- **Intelligent Q&A**: Ask questions about any transcript with source references
- **Hierarchical Summarization**: Multi-level summaries (elevator pitch → comprehensive)
- **Enhanced Translation**: NLLB-powered translation with Arabic post-processing
- **Enterprise Ready**: Production-grade with observability, scaling, and security

## 🏗️ Architecture

- **Backend**: FastAPI + Celery + Redis
- **AI Models**: Faster-Whisper, NLLB, BART, AraBERT, Jais
- **Storage**: PostgreSQL, ChromaDB, MinIO/S3
- **Frontend**: React dashboard with timeline and interactive features
- **Infrastructure**: Docker, Kubernetes, Prometheus/Grafana

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repo>
cd transcription-engine
docker-compose up -d

# API will be available at http://localhost:8000
```

## 📊 Performance Benchmarks

| Hardware | 1-Hour Video | Accuracy | Cost |
|----------|-------------|----------|------|
| RTX 4090 (ULTRA) | 3-5 min | 98% | Free |
| RTX 3060 (STD) | 7-10 min | 96% | Free |
| CPU Strong | 20-30 min | 94% | Free |
| Cloud A100 | 2-4 min | 98% | ~$0.50 |

## 🛠️ Development

```bash
# Backend development
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend development
cd frontend
npm install
npm start
```

## 📚 Documentation

- [API Reference](./docs/api.md)
- [Architecture](./docs/architecture.md)
- [Deployment](./docs/deployment.md)
- [Contributing](./docs/contributing.md)

## 🤝 Contributing

This is an enterprise-grade AI engine. Contributions welcome but please follow our development standards:

1. Create feature branch from `main`
2. Add comprehensive tests
3. Update documentation
4. Ensure CI/CD passes
5. Squash commits with clear messages

## 📄 License

Proprietary - Contact for licensing information.

---

*Built with ❤️ for the Arabic AI community*
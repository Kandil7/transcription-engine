# 🚀 SoutiAI Transcription Engine - Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Production Configuration](#production-configuration)
7. [Monitoring & Observability](#monitoring--observability)
8. [Scaling Guidelines](#scaling-guidelines)
9. [Troubleshooting](#troubleshooting)

## Overview

The SoutiAI Transcription Engine is a comprehensive, enterprise-grade AI transcription system optimized for Arabic content with Egyptian dialect support. This guide covers deployment options from development to production environments.

## Prerequisites

### System Requirements
- **CPU**: Minimum 4 cores, 8 threads (recommended 8+ cores)
- **RAM**: Minimum 16GB (recommended 32GB+ for GPU acceleration)
- **Storage**: 50GB+ free space for models and temporary files
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Docker**: Version 20.10+ with Docker Compose v2.0+
- **GPU (Optional)**: NVIDIA GPU with 8GB+ VRAM for accelerated processing

### Software Dependencies
- Docker & Docker Compose
- Git
- Python 3.11+ (for local development)

## Deployment Options

### 1. Development Environment
- Hot reloading for backend and frontend
- All services running locally
- Easy debugging and development

### 2. Staging Environment  
- Production-like configuration
- Limited auto-scaling
- Full monitoring stack

### 3. Production Environment
- High availability configuration
- Auto-scaling based on load
- Security-hardened setup
- Backup and disaster recovery

## Docker Compose Deployment

### Quick Start (Development)

```bash
# Clone the repository
git clone https://github.com/Kandil7/transcription-engine.git
cd transcription-engine

# Start the complete system
docker-compose up -d

# Access services:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Monitoring: http://localhost:3000 (admin/admin)
# - File Storage: http://localhost:9001 (minioadmin/minioadmin)
```

### Production Docker Compose

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Create a `.env` file with the following variables:

```env
# General Settings
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/transcription_db

# Redis
REDIS_URL=redis://redis:6379/0

# Storage
STORAGE_TYPE=minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Hardware Profile Detection
GPU_MEMORY_GB=0  # Set to actual GPU memory if available
CPU_CORES=4

# Processing Limits
MAX_FILE_SIZE_MB=500
MAX_DURATION_HOURS=4
CHUNK_SIZE_SECONDS=300
CHUNK_OVERLAP_SECONDS=30

# AI Model Settings
WHISPER_MODEL=large-v3
TRANSLATION_MODEL=facebook/nllb-200-distilled-600M

# Feature Flags
ENABLE_VOICE_ANALYTICS=true
ENABLE_RAG=true
ENABLE_TTS=false
ENABLE_PROMETHEUS=true

# External Services
VECTOR_DB_URL=http://chromadb:8000
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (v1.20+)
- Helm 3.x
- kubectl configured

### Deploy with Helm

```bash
# Add the chart repository
helm repo add soutiai https://kandil7.github.io/transcription-engine

# Install the transcription engine
helm install transcription-engine soutiai/transcription-engine \
  --namespace soutiai \
  --create-namespace \
  --set image.tag=latest \
  --set replicaCount=2 \
  --set resources.requests.cpu=500m \
  --set resources.requests.memory=2Gi \
  --set resources.limits.cpu=2 \
  --set resources.limits.memory=8Gi
```

### Manual Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/manifests/
```

## Production Configuration

### Security Hardening

1. **Secrets Management**:
   ```bash
   # Create secrets from external secret store
   kubectl create secret generic transcription-secrets \
     --from-literal=secret-key=$(openssl rand -hex 32) \
     --from-literal=db-password=your-db-password
   ```

2. **Network Policies**:
   - Restrict traffic between services
   - Allow only necessary ingress/egress rules

3. **Resource Limits**:
   - Set CPU and memory limits for all pods
   - Configure HPA for auto-scaling

### Performance Tuning

1. **Hardware Profile Optimization**:
   - Set `GPU_MEMORY_GB` based on available GPU memory
   - Adjust `CPU_CORES` for optimal processing
   - Configure appropriate model sizes

2. **Database Optimization**:
   - Use connection pooling
   - Configure appropriate indexing
   - Set up read replicas for high-traffic scenarios

3. **Caching Strategy**:
   - Redis for session and result caching
   - CDN for static assets
   - Model caching for frequently accessed models

## Monitoring & Observability

### Metrics Collection
- Prometheus for metrics collection
- Grafana for visualization
- Custom application metrics

### Logging
- Structured JSON logging
- Centralized log aggregation
- Log retention policies

### Health Checks
- Liveness and readiness probes
- Database connectivity checks
- Model loading verification

## Scaling Guidelines

### Horizontal Scaling
- API Gateway: Scale based on request volume
- Workers: Scale based on queue depth
- Frontend: Scale based on concurrent users

### Vertical Scaling
- Increase resource limits for heavy processing
- Use GPU-enabled nodes for accelerated processing
- Optimize model loading and caching

### Auto-Scaling Configuration
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: transcription-workers
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: transcription-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: queue_depth
      target:
        type: AverageValue
        averageValue: "10"
```

## Troubleshooting

### Common Issues

1. **Model Loading Failures**:
   - Check available disk space
   - Verify model download permissions
   - Ensure sufficient RAM for model loading

2. **Database Connection Issues**:
   - Verify database service is running
   - Check connection string format
   - Ensure proper network connectivity

3. **Memory Issues**:
   - Increase container memory limits
   - Reduce concurrent processing
   - Optimize model loading

### Diagnostic Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs api
docker-compose logs worker
docker-compose logs postgres

# Check health endpoints
curl http://localhost:8000/health

# Monitor resource usage
docker stats
```

### Performance Monitoring

Monitor these key metrics:
- API response times
- Job processing duration
- Queue depth
- Memory and CPU utilization
- Database connection pool usage

---

## 🎉 Congratulations!

Your SoutiAI Transcription Engine is now deployed and ready for production use. The system is optimized for Arabic content with special focus on Egyptian dialects, providing industry-leading accuracy and performance.
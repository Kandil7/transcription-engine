# Troubleshooting Guide

Comprehensive troubleshooting guide for common issues with the SoutiAI Transcription Engine.

## Quick Diagnosis

### System Health Check

Run the health check endpoint to identify issues:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
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

### Common Status Issues

- **Service Status**: `"down"` → Service not running
- **Model Status**: `"not loaded"` → Model loading failed
- **Database**: `"down"` → Database connection issue
- **Redis**: `"down"` → Cache/queue connection issue

## Startup Issues

### Docker Compose Fails to Start

**Symptoms**:
- `docker-compose up` fails
- Port already in use errors
- Container exits immediately

**Diagnosis**:
```bash
# Check Docker status
docker ps -a

# View container logs
docker-compose logs

# Check system resources
docker system df
```

**Solutions**:

1. **Port Conflicts**:
```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :5432

# Kill conflicting process
sudo kill -9 <PID>
```

2. **Insufficient Resources**:
```bash
# Check available memory
free -h

# Check Docker resource limits
docker system info
```

3. **Permission Issues**:
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker
```

### Backend Won't Start

**Symptoms**:
- FastAPI server fails to start
- Import errors in logs
- Database connection failures

**Diagnosis**:
```bash
# Check Python environment
cd backend
python --version
pip list | grep fastapi

# Test imports
python -c "from app.main import app; print('Import successful')"

# Check environment variables
env | grep -E "(DATABASE|REDIS|JWT)"
```

**Solutions**:

1. **Missing Dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Database Connection**:
```bash
# Test database connection
python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://user:pass@localhost/db')
    await conn.close()
    print('Database connection successful')
asyncio.run(test())
"
```

3. **Environment Variables**:
```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Required variables
DATABASE_URL=postgresql://user:password@localhost:5432/transcription_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-32-char-secret-key-here
```

### Frontend Build Issues

**Symptoms**:
- React app fails to build
- Module not found errors
- Node.js version issues

**Diagnosis**:
```bash
# Check Node.js version
node --version
npm --version

# Check dependencies
cd frontend
npm ls --depth=0

# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Solutions**:

1. **Node Version**:
```bash
# Install correct Node version
nvm install 18
nvm use 18
```

2. **Build Errors**:
```bash
# Clear build cache
cd frontend
rm -rf build/
npm run build
```

## Runtime Issues

### Transcription Jobs Fail

**Symptoms**:
- Jobs stay in "processing" status
- Transcription fails with errors
- Model loading issues

**Diagnosis**:
```bash
# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}

# View application logs
docker-compose logs api

# Check Celery worker status
docker-compose logs celery_worker

# Test model loading
docker-compose exec api python -c "
from app.services.transcription_service import transcription_service
import asyncio
asyncio.run(transcription_service.load_model())
print('Model loaded successfully')
"
```

**Common Causes & Solutions**:

1. **Model Loading Failure**:
```bash
# Check available memory
free -h

# For GPU issues
nvidia-smi

# Force CPU mode
export DETECTED_PROFILE=CPU_STRONG
docker-compose restart api
```

2. **File Access Issues**:
```bash
# Check file permissions
ls -la data/
ls -la /tmp/

# Fix permissions
chmod 755 data/
chmod 777 /tmp/
```

3. **Audio Format Issues**:
```bash
# Check file format
file /path/to/audio.wav

# Convert audio if needed
ffmpeg -i input.mp4 -acodec pcm_s16le -ar 16000 -ac 1 output.wav
```

### Database Connection Issues

**Symptoms**:
- API returns 500 errors
- Database connection timeouts
- Migration failures

**Diagnosis**:
```bash
# Test database connectivity
docker-compose exec postgres psql -U transcription -d transcription_db -c "SELECT 1;"

# Check connection pool
docker-compose logs postgres

# View database metrics
docker-compose exec postgres psql -U transcription -d transcription_db -c "
SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';
"
```

**Solutions**:

1. **Connection Pool Exhausted**:
```bash
# Increase pool size in .env
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=50

# Restart services
docker-compose restart api
```

2. **Database Disk Full**:
```bash
# Check disk usage
df -h

# Clean up old logs
docker-compose exec postgres /bin/bash -c "
du -sh /var/lib/postgresql/data/*
rm -rf /var/lib/postgresql/data/pg_wal/*
"
```

### Redis/Queue Issues

**Symptoms**:
- Jobs stuck in queue
- Celery worker not processing
- Cache misses

**Diagnosis**:
```bash
# Check Redis connectivity
docker-compose exec redis redis-cli ping

# View queue status
docker-compose exec redis redis-cli LLEN transcription

# Check worker status
docker-compose ps celery_worker
```

**Solutions**:

1. **Queue Backlog**:
```bash
# Scale up workers
docker-compose up -d --scale celery_worker=3

# Clear stuck jobs (CAUTION: loses data)
docker-compose exec redis redis-cli FLUSHALL
```

2. **Worker Crashes**:
```bash
# Check worker logs
docker-compose logs celery_worker

# Restart workers
docker-compose restart celery_worker
```

### Memory Issues

**Symptoms**:
- Out of memory errors
- Service restarts
- Slow performance

**Diagnosis**:
```bash
# Monitor memory usage
docker stats

# Check system memory
free -h

# View application memory usage
docker-compose exec api ps aux --sort=-%mem | head -10
```

**Solutions**:

1. **Increase Memory Limits**:
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

2. **Optimize Model Loading**:
```bash
# Use CPU mode for low memory
export DETECTED_PROFILE=CPU_STRONG

# Reduce batch size
export BATCH_SIZE=1
```

3. **Enable Memory Monitoring**:
```python
# Add to application
import psutil
import gc

def log_memory_usage():
    memory = psutil.virtual_memory()
    logger.info(f"Memory usage: {memory.percent}%")

# Call periodically
```

### GPU Issues

**Symptoms**:
- CUDA errors
- GPU memory issues
- Model loading failures

**Diagnosis**:
```bash
# Check GPU status
nvidia-smi

# Test CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

**Solutions**:

1. **CUDA Version Mismatch**:
```bash
# Check CUDA version
nvcc --version
python -c "import torch; print(torch.version.cuda)"

# Install correct PyTorch version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

2. **GPU Memory Issues**:
```bash
# Clear GPU memory
python -c "import torch; torch.cuda.empty_cache()"

# Use smaller model
export WHISPER_MODEL_SIZE=base
```

3. **Driver Issues**:
```bash
# Update NVIDIA drivers
sudo apt update
sudo apt install nvidia-driver-XXX

# Reboot system
sudo reboot
```

## Performance Issues

### Slow Transcription

**Symptoms**:
- Transcription takes longer than expected
- High CPU/GPU usage
- Memory spikes

**Diagnosis**:
```bash
# Benchmark transcription speed
time curl -X POST http://localhost:8000/api/v1/upload/file \
  -F "file=@test.wav" \
  -F "language=ar"

# Monitor system during transcription
docker stats
nvidia-smi -l 1
```

**Optimization Solutions**:

1. **Hardware Profile**:
```bash
# Check detected profile
curl http://localhost:8000/api/v1/health | jq .system

# Force better profile
export DETECTED_PROFILE=ULTRA
docker-compose restart api
```

2. **Model Optimization**:
```bash
# Use faster model
export WHISPER_MODEL_SIZE=medium

# Enable optimizations
export WHISPER_COMPUTE_TYPE=int8_float16
```

3. **Caching**:
```bash
# Enable translation caching
export ENABLE_TRANSLATION_CACHE=true

# Preload models
curl http://localhost:8000/api/v1/health
```

### High Latency

**Symptoms**:
- API response times >1 second
- WebSocket delays
- Streaming interruptions

**Diagnosis**:
```bash
# Test API latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health

# Monitor network
docker network ls
docker network inspect transcription-engine_default
```

**Solutions**:

1. **Database Query Optimization**:
```sql
-- Add indexes for performance
CREATE INDEX CONCURRENTLY idx_jobs_status_created ON jobs(status, created_at DESC);
CREATE INDEX CONCURRENTLY idx_jobs_user_progress ON jobs(user_id, progress) WHERE status = 'processing';
```

2. **Connection Pooling**:
```bash
# Optimize database pool
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
DB_POOL_TIMEOUT=60
```

3. **Caching Strategy**:
```bash
# Enable Redis caching
REDIS_CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

## Network Issues

### Connection Timeouts

**Symptoms**:
- API calls timeout
- WebSocket disconnects
- File upload failures

**Diagnosis**:
```bash
# Test connectivity
curl -v http://localhost:8000/api/v1/health

# Check network configuration
docker network ls
iptables -L

# Test with different timeouts
curl --connect-timeout 5 http://localhost:8000/api/v1/health
```

**Solutions**:

1. **Nginx/Reverse Proxy**:
```nginx
# nginx.conf
upstream api_backend {
    server api:8000;
    keepalive 32;
}

server {
    listen 80;
    client_max_body_size 500M;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}
```

2. **Docker Network**:
```bash
# Restart network
docker-compose down
docker network prune
docker-compose up -d
```

### CORS Issues

**Symptoms**:
- Frontend can't connect to API
- CORS preflight errors
- Authentication failures

**Diagnosis**:
```bash
# Test CORS headers
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS http://localhost:8000/api/v1/upload/file -v
```

**Solutions**:

1. **Update CORS Settings**:
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Frontend Configuration**:
```javascript
// Update API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

## Security Issues

### Authentication Failures

**Symptoms**:
- Login doesn't work
- API returns 401 errors
- Token validation fails

**Diagnosis**:
```bash
# Test JWT token
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/jobs

# Check JWT secret
echo $JWT_SECRET_KEY | wc -c  # Should be >32

# Validate token format
python -c "
import jwt
token = 'YOUR_TOKEN'
try:
    payload = jwt.decode(token, 'YOUR_SECRET', algorithms=['HS256'])
    print('Token valid:', payload)
except Exception as e:
    print('Token invalid:', e)
"
```

**Solutions**:

1. **JWT Secret**:
```bash
# Generate secure secret
JWT_SECRET_KEY=$(openssl rand -hex 32)
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env
```

2. **Token Expiration**:
```python
# Check token expiry
import jwt
token = "YOUR_TOKEN"
payload = jwt.decode(token, options={"verify_signature": False})
print("Expires:", payload.get("exp"))
```

### File Upload Security

**Symptoms**:
- Uploads rejected
- Security warnings
- Malware detection

**Diagnosis**:
```bash
# Test file upload
curl -X POST http://localhost:8000/api/v1/upload/file \
  -F "file=@test.wav" \
  -F "language=ar"

# Check file validation logs
docker-compose logs api | grep "validation"
```

**Solutions**:

1. **File Type Validation**:
```python
# Check allowed MIME types
ALLOWED_MIME_TYPES = {
    'audio/wav', 'audio/mpeg', 'audio/mp4', 'video/mp4'
}

def validate_file_type(file):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")
```

2. **Size Limits**:
```python
# Check file size
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

if file.size > MAX_FILE_SIZE:
    raise HTTPException(status_code=413, detail="File too large")
```

## Monitoring & Alerting

### Setting Up Alerts

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
      description: "Error rate is {{ $value }} errors per second"

  - alert: JobProcessingStuck
    expr: celery_active_tasks == 0 AND celery_queue_length > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Job processing may be stuck"
      description: "No active tasks but {{ $value }} jobs in queue"
```

### Log Analysis

```bash
# Search for errors
docker-compose logs api | grep ERROR

# Monitor performance
docker-compose logs api | grep "transcription.*took"

# Check for memory leaks
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemPerc}}"
```

## Recovery Procedures

### Database Recovery

```bash
# Backup database
docker-compose exec postgres pg_dump -U transcription transcription_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U transcription transcription_db < backup.sql

# Recreate indexes
docker-compose exec postgres psql -U transcription transcription_db -c "
REINDEX DATABASE transcription_db;
ANALYZE;
"
```

### Service Recovery

```bash
# Restart all services
docker-compose down
docker-compose up -d

# Restart specific service
docker-compose restart api

# Force recreate containers
docker-compose up -d --force-recreate
```

### Data Recovery

```bash
# Recover files from MinIO
mc mirror transcription-bucket backup/

# Restore from backup
mc cp backup/ transcription-bucket/ --recursive

# Verify data integrity
find data/ -name "*.wav" -exec file {} \; | grep -v "WAVE audio"
```

## Getting Help

### Debug Information

When reporting issues, include:

```bash
# System information
uname -a
docker --version
docker-compose --version

# Service status
docker-compose ps

# Recent logs
docker-compose logs --tail=100

# Health check
curl http://localhost:8000/api/v1/health

# Configuration (redacted)
env | grep -v SECRET | grep -v KEY
```

### Support Resources

- **GitHub Issues**: https://github.com/Kandil7/transcription-engine/issues
- **Documentation**: https://docs.souti.ai/troubleshooting
- **Community Discord**: https://discord.gg/souti-ai
- **Enterprise Support**: enterprise@souti.ai

### Emergency Contacts

- **Critical Issues**: Response within 1 hour
- **Production Downtime**: Response within 15 minutes
- **Security Issues**: Response within 30 minutes

This troubleshooting guide covers the most common issues. For complex problems, please provide detailed logs and system information when seeking help.</content>
</xai:function_call">TROUBLESHOOTING.md
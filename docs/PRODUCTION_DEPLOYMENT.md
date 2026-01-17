# Production Deployment Guide

This guide covers deploying the Transcription Engine to production with enterprise-grade monitoring, security, and scalability.

## Prerequisites

- **Server Requirements**:
  - Ubuntu 20.04+ or CentOS 7+
  - 8GB RAM minimum (16GB recommended)
  - 4 CPU cores minimum
  - 100GB SSD storage
  - NVIDIA GPU (optional, for faster processing)

- **Software Requirements**:
  - Docker 20.10+
  - Docker Compose 2.0+
  - Git
  - curl/wget
  - SSL certificate (Let's Encrypt will be used)

## Quick Production Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/Kandil7/transcription-engine.git
cd transcription-engine
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env.prod

# Edit with your production values
nano .env.prod
```

**Required Environment Variables**:
```bash
# Application
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here
DOMAIN=your-domain.com

# Database
POSTGRES_PASSWORD=secure-postgres-password

# Redis
REDIS_PASSWORD=secure-redis-password

# MinIO Storage
MINIO_ACCESS_KEY=your-minio-key
MINIO_SECRET_KEY=your-minio-secret

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password

# Email Alerts
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=admin@yourcompany.com
```

### 3. Domain Configuration

Update your DNS to point to your server:
```
api.your-domain.com     -> server-ip
your-domain.com         -> server-ip
grafana.your-domain.com -> server-ip
prometheus.your-domain.com -> server-ip
```

### 4. SSL Certificate Setup

The system uses Let's Encrypt for automatic SSL certificates. Ensure your domain points to the server before deployment.

### 5. Deploy

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh deploy
```

### 6. Verify Deployment

```bash
# Check service status
./scripts/deploy.sh status

# Check logs
./scripts/deploy.sh logs

# Test API health
curl -k https://api.your-domain.com/health

# Access services
# Frontend: https://your-domain.com
# API: https://api.your-domain.com/docs
# Grafana: https://grafana.your-domain.com
# Prometheus: https://prometheus.your-domain.com
```

## Architecture Overview

```
Internet
    ↓
[Traefik Reverse Proxy] (SSL Termination, Load Balancing)
    ↓
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)    API Gateway (FastAPI)   WebSocket     │
│  ↕️ CORS, Security   ↕️ Auth, Rate Limit    ↕️ Real-time    │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                     Processing Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Celery Workers (GPU/CPU)    Task Queue (Redis)            │
│  ↕️ AI Processing          ↕️ Async Tasks                │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                             │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL    ChromaDB      MinIO         Redis Cache     │
│  ↕️ Metadata   ↕️ Vectors    ↕️ Files      ↕️ Sessions     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                     Monitoring Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Prometheus   Grafana      AlertManager    Node Exporter   │
│  ↕️ Metrics   ↕️ Dashboards ↕️ Alerts      ↕️ System       │
└─────────────────────────────────────────────────────────────┘
```

## Security Features

### Authentication & Authorization
- **JWT Token Authentication**: Secure API access
- **API Key Authentication**: For integrations
- **Role-based Access Control**: User permissions

### Network Security
- **SSL/TLS Encryption**: End-to-end encryption
- **Security Headers**: XSS, CSRF, Clickjacking protection
- **Rate Limiting**: DDoS protection (50 req/min average, 100 burst)
- **CORS Configuration**: Controlled cross-origin access

### Data Protection
- **Input Validation**: Sanitized file uploads
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: Content Security Policy
- **Secure Headers**: Comprehensive HTTP security

## Monitoring & Alerting

### Metrics Collected
- **Application Metrics**: Request rate, response time, error rate
- **System Metrics**: CPU, memory, disk, network usage
- **Business Metrics**: Job completion rate, processing time
- **AI Metrics**: Model performance, GPU utilization

### Alert Rules
- **Critical**: API down, database unreachable, disk full
- **Warning**: High CPU/memory usage, job failures, slow responses
- **Info**: Deployment events, configuration changes

### Dashboards
- **Main Dashboard**: System overview and key metrics
- **API Dashboard**: Request patterns and performance
- **Jobs Dashboard**: Processing pipeline metrics
- **Infrastructure**: System resources and containers

## Scaling Configuration

### Horizontal Scaling
```yaml
# Scale API instances
docker-compose up -d --scale api=3

# Scale workers
docker-compose up -d --scale worker-gpu=2
docker-compose up -d --scale worker-cpu=4
```

### Resource Limits
```yaml
# GPU Worker
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
    limits:
      memory: 4G
      cpus: '2.0'
```

### Load Balancing
- **Traefik**: Automatic load balancing across instances
- **Redis**: Distributed task queue
- **PostgreSQL**: Connection pooling

## Backup & Recovery

### Database Backup
```bash
# Daily database backup
0 2 * * * docker exec postgres pg_dump -U postgres transcription_db > backup_$(date +\%Y\%m\%d).sql
```

### File Storage Backup
```bash
# MinIO bucket backup
mc mirror --overwrite local/transcription-engine s3/backup/transcription-engine
```

### Configuration Backup
```bash
# Environment and config backup
cp .env.prod backup/
cp docker-compose.prod.yml backup/
```

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
./scripts/deploy.sh logs

# Check resource usage
docker stats

# Restart services
docker-compose restart
```

#### SSL Certificate Issues
```bash
# Check Traefik logs
docker logs traefik

# Renew certificates manually
docker exec traefik traefik certificates
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart memory-intensive services
docker-compose restart worker-gpu
```

### Performance Optimization

#### GPU Optimization
- Use latest NVIDIA drivers
- Enable GPU persistence mode
- Monitor GPU utilization in Grafana

#### Database Optimization
- Regular VACUUM operations
- Index optimization
- Connection pooling

#### Cache Optimization
- Redis memory limits
- Cache TTL configuration
- Cache hit rate monitoring

## Maintenance

### Regular Tasks
```bash
# Update images
docker-compose pull

# Clean up old images
docker image prune -f

# Update SSL certificates
# Handled automatically by Traefik

# Backup data
./scripts/backup.sh
```

### Monitoring Health
- Check Grafana dashboards daily
- Review alert history weekly
- Monitor performance trends monthly

## Support

For production support and issues:

1. Check logs: `./scripts/deploy.sh logs`
2. Review metrics in Grafana
3. Check alerts in AlertManager
4. Review documentation and runbooks
5. Contact the development team

## Security Checklist

- [ ] Environment variables secured
- [ ] SSL certificates valid
- [ ] Firewall configured
- [ ] API keys rotated regularly
- [ ] Backups tested
- [ ] Monitoring alerts configured
- [ ] Access logs reviewed
- [ ] Dependencies updated

---

This deployment provides enterprise-grade reliability, security, and scalability for production use.
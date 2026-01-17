#!/bin/bash

# Transcription Engine Production Deployment Script
# This script handles deployment to production environment

set -e

# Configuration
DOCKER_REGISTRY="ghcr.io/kandil7"
IMAGE_NAME="transcription-engine"
ENV_FILE=".env.prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if .env.prod file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found. Please create it with production values."
        log_info "You can copy .env.example to $ENV_FILE and fill in the values."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Build and push Docker images
build_and_push() {
    log_info "Building and pushing Docker images..."

    # Build backend image
    log_info "Building backend image..."
    docker build -t $DOCKER_REGISTRY/$IMAGE_NAME:latest-backend ./backend
    docker push $DOCKER_REGISTRY/$IMAGE_NAME:latest-backend

    # Build frontend image
    log_info "Building frontend image..."
    docker build -t $DOCKER_REGISTRY/$IMAGE_NAME:latest-frontend ./frontend
    docker push $DOCKER_REGISTRY/$IMAGE_NAME:latest-frontend

    log_success "Images built and pushed successfully"
}

# Deploy to production
deploy_production() {
    log_info "Deploying to production..."

    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' $ENV_FILE | xargs)
    fi

    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f docker-compose.prod.yml pull

    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30

    # Run health checks
    log_info "Running health checks..."
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        exit 1
    fi

    # Run database migrations (if needed)
    log_info "Running database migrations..."
    docker-compose -f docker-compose.prod.yml exec -T api python -c "
import asyncio
from app.db.session import init_db
asyncio.run(init_db())
print('Database initialized')
"

    log_success "Production deployment completed successfully"
}

# Rollback deployment
rollback() {
    log_warning "Rolling back deployment..."

    # Get previous image tag
    PREVIOUS_TAG=$(docker images $DOCKER_REGISTRY/$IMAGE_NAME --format "{{.Repository}}:{{.Tag}}" | head -2 | tail -1)

    if [ -n "$PREVIOUS_TAG" ]; then
        log_info "Rolling back to $PREVIOUS_TAG"

        # Update docker-compose to use previous image
        sed -i "s|image: $DOCKER_REGISTRY/$IMAGE_NAME:latest|image: $PREVIOUS_TAG|" docker-compose.prod.yml

        # Restart services
        docker-compose -f docker-compose.prod.yml up -d

        log_success "Rollback completed"
    else
        log_error "No previous image found for rollback"
        exit 1
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy     Deploy to production"
    echo "  build      Build and push images only"
    echo "  rollback   Rollback to previous version"
    echo "  logs       Show service logs"
    echo "  status     Show service status"
    echo "  cleanup    Clean up unused Docker resources"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 logs api"
    echo "  $0 status"
}

# Show service status
show_status() {
    log_info "Service Status:"
    docker-compose -f docker-compose.prod.yml ps

    echo ""
    log_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Show logs
show_logs() {
    SERVICE=${2:-""}
    if [ -n "$SERVICE" ]; then
        log_info "Showing logs for $SERVICE..."
        docker-compose -f docker-compose.prod.yml logs -f $SERVICE
    else
        log_info "Showing all service logs..."
        docker-compose -f docker-compose.prod.yml logs --tail=100
    fi
}

# Cleanup Docker resources
cleanup() {
    log_info "Cleaning up unused Docker resources..."

    # Remove unused images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    # Remove unused networks
    docker network prune -f

    log_success "Cleanup completed"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        check_prerequisites
        build_and_push
        deploy_production
        ;;
    "build")
        check_prerequisites
        build_and_push
        ;;
    "rollback")
        rollback
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$@"
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        usage
        exit 1
        ;;
esac

log_success "Script completed successfully!"
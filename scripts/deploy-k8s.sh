#!/bin/bash

# =================================================================
# Transcription Engine Kubernetes Deployment Script
# =================================================================
# This script handles complete Kubernetes deployment of the Transcription Engine

set -e

# Configuration
NAMESPACE="transcription-engine"
DOCKER_REGISTRY="ghcr.io/kandil7"
IMAGE_TAG=${IMAGE_TAG:-"latest"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi

    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"

    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        kubectl apply -f k8s/namespace.yaml
        log_success "Namespace created"
    else
        log_warning "Namespace already exists"
    fi
}

# Build and push images
build_and_push_images() {
    log_info "Building and pushing Docker images..."

    # Backend image
    log_info "Building backend image..."
    docker build -t $DOCKER_REGISTRY/transcription-engine:$IMAGE_TAG ./backend
    docker push $DOCKER_REGISTRY/transcription-engine:$IMAGE_TAG
    log_success "Backend image pushed"

    # Frontend image
    log_info "Building frontend image..."
    docker build -t $DOCKER_REGISTRY/transcription-frontend:$IMAGE_TAG ./frontend
    docker push $DOCKER_REGISTRY/transcription-frontend:$IMAGE_TAG
    log_success "Frontend image pushed"
}

# Deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure components..."

    # RBAC
    log_info "Applying RBAC..."
    kubectl apply -f k8s/rbac.yaml

    # ConfigMap and Secret
    log_info "Applying ConfigMap and Secret..."
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secret.yaml

    # PostgreSQL
    log_info "Deploying PostgreSQL..."
    kubectl apply -f k8s/postgres.yaml

    # Redis
    log_info "Deploying Redis..."
    kubectl apply -f k8s/redis.yaml

    # ChromaDB
    log_info "Deploying ChromaDB..."
    kubectl apply -f k8s/chroma.yaml

    # MinIO
    log_info "Deploying MinIO..."
    kubectl apply -f k8s/minio.yaml

    log_success "Infrastructure deployed"
}

# Deploy application
deploy_application() {
    log_info "Deploying application components..."

    # API
    log_info "Deploying API..."
    kubectl apply -f k8s/api.yaml

    # Workers
    log_info "Deploying workers..."
    kubectl apply -f k8s/worker.yaml

    # Frontend
    log_info "Deploying frontend..."
    kubectl apply -f k8s/frontend.yaml

    # HPA
    log_info "Deploying auto-scaling..."
    kubectl apply -f k8s/hpa.yaml

    log_success "Application deployed"
}

# Wait for deployments to be ready
wait_for_deployments() {
    log_info "Waiting for deployments to be ready..."

    # List of deployments to wait for
    deployments=(
        "postgres"
        "redis"
        "chroma"
        "minio"
        "transcription-api"
        "transcription-worker"
        "transcription-frontend"
    )

    for deployment in "${deployments[@]}"; do
        log_info "Waiting for $deployment..."
        kubectl wait --for=condition=available --timeout=600s deployment/$deployment -n $NAMESPACE
    done

    log_success "All deployments are ready"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    # Run alembic migrations in the API pod
    kubectl exec -n $NAMESPACE deployment/transcription-api -- python -c "
import asyncio
from app.db.session import init_db
asyncio.run(init_db())
print('Database initialized')
"

    log_success "Database migrations completed"
}

# Health check
health_check() {
    log_info "Running health checks..."

    # API health check
    api_pod=$(kubectl get pods -n $NAMESPACE -l app=transcription-engine,component=api -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n $NAMESPACE $api_pod -- curl -f http://localhost:8000/api/v1/health

    # Worker health check
    worker_pod=$(kubectl get pods -n $NAMESPACE -l app=transcription-engine,component=worker -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n $NAMESPACE $worker_pod -- celery -A app.tasks.celery_app inspect ping

    log_success "Health checks passed"
}

# Display deployment information
show_deployment_info() {
    log_success "Deployment completed successfully!"
    echo
    echo "================================================================="
    echo "🎉 Transcription Engine Deployed Successfully!"
    echo "================================================================="
    echo
    echo "📊 Deployment Summary:"
    echo "  • Namespace: $NAMESPACE"
    echo "  • API Replicas: $(kubectl get deployment transcription-api -n $NAMESPACE -o jsonpath='{.spec.replicas}')"
    echo "  • Worker Replicas: $(kubectl get deployment transcription-worker -n $NAMESPACE -o jsonpath='{.spec.replicas}')"
    echo "  • Frontend Replicas: $(kubectl get deployment transcription-frontend -n $NAMESPACE -o jsonpath='{.spec.replicas}')"
    echo
    echo "🌐 Service Endpoints:"
    echo "  • API: https://api.yourdomain.com"
    echo "  • Frontend: https://app.yourdomain.com"
    echo "  • MinIO Console: https://minio.yourdomain.com"
    echo
    echo "📈 Monitoring:"
    echo "  • Prometheus: kubectl port-forward svc/prometheus 9090:9090 -n monitoring"
    echo "  • Grafana: kubectl port-forward svc/grafana 3000:80 -n monitoring"
    echo "  • AlertManager: kubectl port-forward svc/alertmanager 9093:9093 -n monitoring"
    echo
    echo "🔧 Management Commands:"
    echo "  • View logs: kubectl logs -f deployment/transcription-api -n $NAMESPACE"
    echo "  • Scale API: kubectl scale deployment transcription-api --replicas=5 -n $NAMESPACE"
    echo "  • Update image: kubectl set image deployment/transcription-api api=$DOCKER_REGISTRY/transcription-engine:v2.0.0 -n $NAMESPACE"
    echo
    echo "================================================================="
}

# Main deployment function
deploy() {
    echo "================================================================="
    echo "🚀 Deploying Transcription Engine to Kubernetes"
    echo "================================================================="

    check_prerequisites
    create_namespace
    build_and_push_images
    deploy_infrastructure
    deploy_application
    wait_for_deployments
    run_migrations
    health_check
    show_deployment_info
}

# Main undeploy function
undeploy() {
    log_info "Undeploying Transcription Engine..."

    # Delete all resources
    kubectl delete namespace $NAMESPACE --ignore-not-found=true

    log_success "Transcription Engine undeployed"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "undeploy")
        undeploy
        ;;
    "build")
        build_and_push_images
        ;;
    "infrastructure")
        deploy_infrastructure
        ;;
    "application")
        deploy_application
        ;;
    *)
        echo "Usage: $0 [deploy|undeploy|build|infrastructure|application]"
        echo "  deploy        - Full deployment (default)"
        echo "  undeploy      - Remove all resources"
        echo "  build         - Build and push images only"
        echo "  infrastructure- Deploy infrastructure only"
        echo "  application  - Deploy application only"
        exit 1
        ;;
esac
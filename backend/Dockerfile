# =================================================================
# Multi-stage Dockerfile for SoutiAI Transcription Engine
# =================================================================

# Base stage with system dependencies
FROM nvidia/cuda:12.1-devel-ubuntu22.04 AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-distutils \
    python3.11-dev \
    ffmpeg \
    git \
    curl \
    build-essential \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install pip separately for Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Create app user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

# =================================================================
# Production stage
# =================================================================
FROM base AS production

# Install pip separately to avoid conflicts
RUN python3.11 -m pip install --upgrade pip

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/audio_chunks /tmp/models /app/logs /app/data /app/models

# Set permissions
RUN chown -R app:app /app /tmp/audio_chunks /tmp/models

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =================================================================
# CPU-only stage (fallback for systems without GPU)
# =================================================================
FROM ubuntu:22.04 AS cpu-base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-distutils \
    python3.11-dev \
    ffmpeg \
    git \
    curl \
    build-essential \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install pip separately for Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Create app user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

FROM cpu-base AS cpu-production

# Install pip separately to avoid conflicts
RUN python3.11 -m pip install --upgrade pip

# Copy requirements and install Python dependencies (CPU version)
COPY requirements.txt .
# Temporarily modify requirements to use CPU-only PyTorch
RUN sed -i 's|https://download.pytorch.org/whl/cu121|https://download.pytorch.org/whl/cpu|g' requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/audio_chunks /tmp/models /app/logs /app/data /app/models

# Set permissions
RUN chown -R app:app /app /tmp/audio_chunks /tmp/models

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =================================================================
# Development stage
# =================================================================
FROM base AS development

# Install pip separately to avoid conflicts
RUN python3.11 -m pip install --upgrade pip

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/audio_chunks /tmp/models /app/logs /app/data /app/models

# Set permissions
RUN chown -R app:app /app /tmp/audio_chunks /tmp/models

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Expose port
EXPOSE 8000

# Run development server with hot reload
CMD ["python", "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
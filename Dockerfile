# Multi-stage build for AI Asset Rebalancing System
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge
# Optimized for Rocky Linux server environment

# Stage 1: Frontend Build (React + TypeScript + Vite)
FROM node:18-alpine AS frontend-builder

# Set working directory
WORKDIR /app

# Copy package files for dependency caching
COPY package.json package-lock.json ./

# Install ALL dependencies (including devDependencies for build tools like Vite)
RUN npm config set registry https://registry.npmjs.org/ && \
    npm ci --silent --no-audit --no-fund

# Copy frontend source code
COPY . .

# Build React application for production
RUN npm run build

# Stage 2: Backend Runtime (Python FastAPI)
FROM python:3.11-slim AS backend-runtime

# Set environment variables for package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Update package sources and install system dependencies with retry logic
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install build dependencies separately if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy frontend build artifacts
COPY --from=frontend-builder /app/dist ./frontend/dist/

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chmod 755 /app/logs /app/data

# Set final environment variables
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port
EXPOSE $PORT

# Start FastAPI server (serves both API and frontend static files)
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
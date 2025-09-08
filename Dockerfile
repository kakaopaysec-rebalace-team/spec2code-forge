# Multi-stage build for AI Asset Rebalancing System
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge

# Stage 1: Frontend Build (React + TypeScript + Vite)
FROM node:18-alpine as frontend-builder

# Set working directory
WORKDIR /app

# Copy package files for dependency caching
COPY package.json package-lock.json ./

# Install dependencies with clean install
RUN npm ci --only=production --silent

# Copy frontend source code
COPY . .

# Build React application for production
RUN npm run build

# Stage 2: Backend Runtime (Python FastAPI)
FROM python:3.11-slim as backend-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy frontend build artifacts
COPY --from=frontend-builder /app/dist ./frontend/dist/

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port
EXPOSE $PORT

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Start FastAPI server (serves both API and frontend static files)
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
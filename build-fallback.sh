#!/bin/bash

# AI Asset Rebalancing System - Fallback Build Script
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge
# For environments with strict network restrictions

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-system"

echo "🔄 Fallback Docker Build - Rocky Linux"
echo "Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 현재 디렉토리 확인
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile을 찾을 수 없습니다."
    exit 1
fi

# 로컬에서 프론트엔드 빌드 먼저 시도
echo "🔨 로컬에서 프론트엔드 빌드 시도..."
if command -v npm &> /dev/null; then
    echo "   npm이 설치되어 있습니다. 로컬 빌드 진행..."
    
    # 의존성 설치
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
        echo "   의존성 설치 중..."
        npm install --silent --no-audit --no-fund
    fi
    
    # 빌드
    echo "   프론트엔드 빌드 중..."
    npm run build
    
    if [ -d "dist" ]; then
        echo "   ✅ 로컬 빌드 성공! dist 디렉토리 생성됨"
        
        # 간소화된 Dockerfile 생성
        cat > Dockerfile.fallback << 'EOF'
# Simplified Dockerfile using pre-built frontend
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY backend/requirements.txt ./backend/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy pre-built frontend
COPY dist ./frontend/dist/

# Create directories
RUN mkdir -p /app/logs /app/data

# Environment variables
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

EXPOSE $PORT

CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
EOF
        
        echo "   간소화된 Dockerfile.fallback 생성"
        
        # 기존 이미지 정리
        if [ "$(docker images -q ${IMAGE_NAME})" ]; then
            echo "   기존 이미지 삭제 중..."
            docker rmi ${IMAGE_NAME} || true
        fi
        
        # 간소화된 이미지 빌드
        echo "   간소화된 이미지 빌드 중..."
        docker build -f Dockerfile.fallback -t ${IMAGE_NAME} .
        
        echo "   ✅ Fallback 빌드 성공!"
        
        # 정리
        rm Dockerfile.fallback
        
    else
        echo "   ❌ 로컬 빌드 실패"
        exit 1
    fi
    
else
    echo "   ❌ npm이 설치되지 않아 로컬 빌드를 할 수 없습니다."
    echo "   다음 방법 중 하나를 선택하세요:"
    echo ""
    echo "   1. Node.js 설치:"
    echo "      sudo dnf install nodejs npm"
    echo ""
    echo "   2. 미리 빌드된 이미지 사용:"
    echo "      docker pull your-registry/ai-rebalancing:latest"
    echo ""
    echo "   3. 다른 환경에서 빌드 후 이미지 내보내기/가져오기:"
    echo "      docker save ai-rebalancing-system > ai-rebalancing.tar"
    echo "      docker load < ai-rebalancing.tar"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Fallback 빌드 완료!"
echo "   이미지: ${IMAGE_NAME}"
echo "   다음 단계: ./deploy.sh 또는 직접 컨테이너 실행"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
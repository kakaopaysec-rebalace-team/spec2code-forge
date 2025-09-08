#!/bin/bash

# AI Asset Rebalancing System - Direct Deployment (No Container Build)
# 컨테이너 내부 빌드를 피하고 로컬에서 빌드 후 복사하는 방식

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-direct"
PORT="80"
INTERNAL_PORT="8000"

echo "🚀 AI Asset Rebalancing - Direct 배포 방식"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Docker 환경 확인
echo "🔍 Docker 환경 확인..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다"
    exit 1
fi
echo "   ✅ Docker 준비 완료"

# 2. 기존 리소스 정리
echo ""
echo "🧹 기존 리소스 정리..."
docker stop ${APP_NAME} 2>/dev/null || true
docker rm ${APP_NAME} 2>/dev/null || true
docker rmi ${IMAGE_NAME} 2>/dev/null || true
echo "   ✅ 기존 리소스 정리 완료"

# 3. 로컬 프론트엔드 빌드 확인
echo ""
echo "📦 프론트엔드 빌드 확인..."
if [ ! -d "dist" ] || [ ! "$(ls -A dist/)" ]; then
    echo "   ⚠️ 빌드된 프론트엔드 없음 - 직접 빌드 시도"
    
    # Node.js 확인
    if command -v npm &> /dev/null; then
        echo "   📦 npm으로 프론트엔드 빌드 중..."
        npm install 2>/dev/null && npm run build 2>/dev/null && echo "   ✅ 로컬 빌드 성공" || {
            echo "   ❌ 로컬 빌드 실패"
            echo ""
            echo "🛠️ 수동 빌드 필요:"
            echo "   npm install"
            echo "   npm run build"
            echo "   그 후 다시 이 스크립트 실행"
            exit 1
        }
    else
        echo "   ❌ Node.js/npm 없음 - 수동 빌드 필요"
        exit 1
    fi
else
    echo "   ✅ 빌드된 프론트엔드 발견"
fi

# 4. 간단한 Dockerfile 생성 (오프라인)
echo ""
echo "🐳 간단한 Dockerfile 생성..."
cat > Dockerfile.simple << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 최소 의존성만 설치 (오프라인 환경 대응)
RUN pip install --no-cache-dir fastapi==0.104.0 uvicorn==0.24.0 || \
    pip install --no-cache-dir fastapi uvicorn || \
    echo "기본 패키지 설치 실패, 계속 진행"

# 백엔드 복사
COPY backend/ ./backend/

# 프론트엔드 복사 (로컬 빌드)
COPY dist ./frontend/dist/

# 디렉토리 생성
RUN mkdir -p /app/logs /app/data

# 환경변수
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

# 포트 노출
EXPOSE 8000

# 시작 명령
CMD ["python", "-c", "import uvicorn; from backend.app import app; uvicorn.run(app, host='0.0.0.0', port=8000)"]
EOF

echo "   ✅ 간단한 Dockerfile 생성 완료"

# 5. 이미지 빌드
echo ""
echo "🔨 Docker 이미지 빌드..."
if docker build -f Dockerfile.simple -t ${IMAGE_NAME} . ; then
    echo "   ✅ Docker 빌드 성공"
else
    echo "   ❌ Docker 빌드 실패 - Dockerfile.offline 시도"
    
    if docker build -f Dockerfile.offline -t ${IMAGE_NAME} . ; then
        echo "   ✅ 오프라인 Dockerfile로 빌드 성공"
    else
        echo "   ❌ 모든 빌드 방법 실패"
        echo ""
        echo "🔄 로컬 서버로 대체 실행..."
        ./start.sh
        exit 0
    fi
fi

# 6. 컨테이너 실행
echo ""
echo "🚀 컨테이너 실행..."
docker run -d \
    --name ${APP_NAME} \
    --publish ${PORT}:${INTERNAL_PORT} \
    --restart unless-stopped \
    --volume "$(pwd)/data:/app/data:rw" \
    --volume "$(pwd)/logs:/app/logs:rw" \
    ${IMAGE_NAME}

# 7. 실행 확인
echo ""
echo "✅ 배포 완료!"
sleep 5

if docker ps | grep -q ${APP_NAME}; then
    echo "   ✅ 컨테이너 실행 중"
    
    SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 Direct 배포 완료!"
    echo ""
    echo "🌐 접속 정보:"
    echo "   • 웹사이트: http://${SERVER_IP}/"
    echo "   • 로컬: http://localhost/"
    echo ""
    echo "🛠️ 관리 명령어:"
    echo "   • 로그 확인: docker logs -f ${APP_NAME}"
    echo "   • 재시작: docker restart ${APP_NAME}"
    echo "   • 중지: docker stop ${APP_NAME}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "   ❌ 컨테이너 실행 실패"
    echo "   로그: $(docker logs ${APP_NAME} 2>&1 | tail -5)"
fi

# 정리
rm -f Dockerfile.simple
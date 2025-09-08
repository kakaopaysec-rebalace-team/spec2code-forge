#!/bin/bash

# AI Asset Rebalancing System - Offline Deployment Script  
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge
# For Rocky Linux servers with network restrictions or DNS issues

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-system"
PORT="80"
INTERNAL_PORT="8000"

echo "🔒 AI Asset Rebalancing System - 오프라인 배포"
echo "Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 현재 디렉토리 확인
if [ ! -f "Dockerfile.offline" ]; then
    echo "❌ Dockerfile.offline을 찾을 수 없습니다. 프로젝트 루트 디렉토리에서 실행하세요."
    exit 1
fi

# Node.js 설치 확인
if ! command -v node &> /dev/null; then
    echo "❌ Node.js가 설치되지 않았습니다."
    echo "   Rocky Linux에서 Node.js 설치:"
    echo "   sudo dnf install nodejs npm"
    exit 1
fi

echo "✅ Node.js 확인: $(node --version)"
echo "✅ npm 확인: $(npm --version)"

# Git 상태 확인
echo ""
echo "📋 Git 상태 확인..."
echo "   현재 브랜치: $(git branch --show-current)"
echo "   최신 커밋: $(git log --oneline -1)"

# 환경 변수 파일 확인
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env 파일이 없습니다."
    if [ -f ".env.example" ]; then
        echo "   .env.example을 복사하여 .env 생성..."
        cp .env.example .env
        echo "   ✅ .env 파일이 생성되었습니다. API 키를 설정하세요."
    else
        echo "   수동으로 .env 파일을 생성하세요."
    fi
fi

# 기존 컨테이너 정리
echo ""
echo "🧹 기존 컨테이너 정리..."
if [ "$(docker ps -aq -f name=${APP_NAME})" ]; then
    echo "   기존 컨테이너 중지 및 삭제 중..."
    docker stop ${APP_NAME} || true
    docker rm ${APP_NAME} || true
fi

if [ "$(docker images -q ${IMAGE_NAME})" ]; then
    echo "   기존 이미지 삭제 중..."
    docker rmi ${IMAGE_NAME} || true
fi

# 로컬에서 프론트엔드 빌드
echo ""
echo "🔨 로컬에서 프론트엔드 빌드..."

# 기존 빌드 정리
if [ -d "node_modules" ]; then
    echo "   기존 node_modules 정리..."
    rm -rf node_modules
fi

if [ -d "dist" ]; then
    echo "   기존 dist 정리..."
    rm -rf dist
fi

# npm 의존성 설치
echo "   npm 의존성 설치 중..."
npm install --silent --no-audit --no-fund

# 프론트엔드 빌드
echo "   프론트엔드 빌드 실행 중..."
npm run build

# 빌드 결과 확인
if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo "   ❌ 프론트엔드 빌드 실패!"
    echo "   dist 디렉토리나 index.html이 생성되지 않았습니다."
    exit 1
fi

echo "   ✅ 프론트엔드 빌드 성공!"
echo "   빌드된 파일 수: $(find dist -type f | wc -l)"

# Docker 이미지 빌드 (오프라인 모드)
echo ""
echo "🐳 Docker 이미지 빌드 (오프라인 모드)..."
docker build \
    --file Dockerfile.offline \
    --tag ${IMAGE_NAME} \
    --no-cache \
    .

echo "   ✅ Docker 이미지 빌드 완료!"

# 컨테이너 실행
echo ""
echo "🚀 컨테이너 시작..."

# 환경 변수 파일 옵션
ENV_OPTION=""
if [ -f ".env" ]; then
    ENV_OPTION="--env-file .env"
    echo "   .env 파일을 사용합니다."
fi

# 데이터 디렉토리 생성
mkdir -p ./data ./logs
chmod 755 ./data ./logs

# 컨테이너 실행
docker run -d \
    --name ${APP_NAME} \
    --publish ${PORT}:${INTERNAL_PORT} \
    ${ENV_OPTION} \
    --restart unless-stopped \
    --memory="2g" \
    --cpus="2.0" \
    --volume "$(pwd)/data:/app/data:rw" \
    --volume "$(pwd)/logs:/app/logs:rw" \
    --log-driver=json-file \
    --log-opt max-size=100m \
    --log-opt max-file=3 \
    ${IMAGE_NAME}

# 배포 확인
echo ""
echo "📊 배포 상태 확인..."
sleep 10

if docker ps --format "{{.Names}}" | grep -q "^${APP_NAME}$"; then
    echo "   ✅ 컨테이너 정상 실행 중!"
    
    # 서비스 응답 확인 (curl 대신 Python 사용)
    echo "   서비스 응답 확인 중..."
    sleep 5
    
    # Python으로 HTTP 요청 테스트
    if python3 -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:${PORT}/', timeout=10)
    print('✅ HTTP 응답 정상:', response.getcode())
except Exception as e:
    print('❌ HTTP 응답 실패:', str(e))
    exit(1)
" 2>/dev/null; then
        echo "   ✅ 웹 서비스 정상 작동!"
    else
        echo "   ⚠️  웹 서비스 응답 확인 실패 (하지만 컨테이너는 실행 중)"
    fi
    
else
    echo "   ❌ 컨테이너 실행 실패!"
    echo "   로그 확인: docker logs ${APP_NAME}"
    exit 1
fi

# 서버 정보 수집
SERVER_IP="localhost"
if command -v hostname &>/dev/null; then
    SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
fi

# 결과 요약
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 오프라인 배포 완료!"
echo ""
echo "🌐 접속 정보:"
echo "   • Frontend: http://${SERVER_IP}:${PORT}/"
echo "   • Local: http://localhost:${PORT}/"
echo "   • API 테스트: http://${SERVER_IP}:${PORT}/docs"
echo ""
echo "🛠️  관리 명령어:"
echo "   • 실시간 로그: docker logs -f ${APP_NAME}"
echo "   • 컨테이너 상태: docker ps"
echo "   • 컨테이너 중지: docker stop ${APP_NAME}"
echo "   • 컨테이너 재시작: docker restart ${APP_NAME}"
echo "   • 리소스 사용량: docker stats ${APP_NAME}"
echo ""
echo "📋 배포된 기능:"
echo "   • 7개 보유 종목 표시 (실제 DB 데이터)"
echo "   • 20개 전략 목록 (실제 DB 데이터)"
echo "   • '$999,993' 포트폴리오 가치"
echo "   • '모든 전략 펼치기' 버튼으로 확장/축소"
echo "   • 실제 데이터 기반 결과 차트"
echo ""
echo "⚠️  오프라인 배포 특징:"
echo "   • 헬스체크 없음 (네트워크 도구 불필요)"
echo "   • 로컬 빌드 + 단순한 Docker 이미지"
echo "   • 네트워크 의존성 최소화"
echo ""
echo "🔍 문제 발생 시:"
echo "   • 컨테이너 로그: docker logs ${APP_NAME}"
echo "   • 컨테이너 내부 접속: docker exec -it ${APP_NAME} /bin/bash"
echo "   • Python 직접 실행: docker exec ${APP_NAME} python -m uvicorn backend.app:app --host 0.0.0.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
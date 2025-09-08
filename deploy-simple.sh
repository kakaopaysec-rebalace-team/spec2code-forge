#!/bin/bash

# AI Asset Rebalancing System - 단순 Docker 배포 스크립트
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge
# Docker Compose 없이 기본 Docker 명령어만 사용

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-system"
PORT="8080"

echo "🚀 AI Asset Rebalancing System - 단순 Docker 배포"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 현재 디렉토리 확인
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile을 찾을 수 없습니다."
    exit 1
fi

# 최신 소스 가져오기
echo "📥 최신 소스 가져오기..."
git pull origin main

# 기존 컨테이너 중지 및 삭제
echo ""
echo "🧹 기존 컨테이너 정리..."
if [ "$(docker ps -aq -f name=$APP_NAME)" ]; then
    echo "   기존 컨테이너 중지 중..."
    docker stop $APP_NAME || true
    echo "   기존 컨테이너 삭제 중..."
    docker rm $APP_NAME || true
fi

# 기존 이미지 삭제 (선택사항)
if [ "$(docker images -q $IMAGE_NAME)" ]; then
    echo "   기존 이미지 삭제 중..."
    docker rmi $IMAGE_NAME || true
fi

# 이미지 빌드
echo ""
echo "🔨 Docker 이미지 빌드..."
docker build --no-cache -t $IMAGE_NAME .

# 컨테이너 실행
echo ""
echo "🚀 컨테이너 시작..."

# 환경 변수 파일 확인
ENV_OPTION=""
if [ -f ".env" ]; then
    ENV_OPTION="--env-file .env"
    echo "   .env 파일을 사용합니다."
else
    echo "   ⚠️  .env 파일이 없습니다. 기본 설정으로 실행합니다."
fi

# 컨테이너 실행
docker run -d \
    --name $APP_NAME \
    -p $PORT:8000 \
    $ENV_OPTION \
    --restart unless-stopped \
    $IMAGE_NAME

# 상태 확인
echo ""
echo "📊 배포 상태 확인..."
sleep 5

if docker ps | grep -q $APP_NAME; then
    echo "✅ 배포 성공!"
    echo ""
    echo "🌐 접속 정보:"
    echo "   • Frontend: http://localhost:$PORT"
    echo "   • API 문서: http://localhost:$PORT/docs"
    echo ""
    echo "🛠️  관리 명령어:"
    echo "   • 로그 확인: docker logs -f $APP_NAME"
    echo "   • 컨테이너 중지: docker stop $APP_NAME"
    echo "   • 컨테이너 재시작: docker restart $APP_NAME"
    echo "   • 컨테이너 삭제: docker rm -f $APP_NAME"
else
    echo "❌ 배포 실패!"
    echo "로그를 확인하세요: docker logs $APP_NAME"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 배포 완료!"
#!/bin/bash

# AI Asset Rebalancing System - Docker Deployment Script
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge

set -e

echo "🚀 AI Asset Rebalancing System - Docker 배포 시작"
echo "Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 현재 디렉토리 확인
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile을 찾을 수 없습니다. 프로젝트 루트 디렉토리에서 실행하세요."
    exit 1
fi

# Docker Compose 버전 확인
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "✅ docker-compose 사용"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "✅ docker compose 사용"
else
    echo "⚠️  Docker Compose를 찾을 수 없습니다. 기본 Docker 명령어를 사용합니다."
fi

# Git 상태 확인
echo "📋 Git 상태 확인..."
git status --porcelain

# 최신 소스 가져오기
echo ""
echo "📥 최신 소스 가져오기..."
git pull origin main

# 환경 변수 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
    echo "   cp .env.example .env"
    echo "   # .env 파일을 편집하여 필요한 API 키를 설정하세요"
fi

# Docker Compose 사용 가능한 경우
if [ ! -z "$DOCKER_COMPOSE_CMD" ]; then
    echo ""
    echo "🧹 기존 컨테이너 정리 (Docker Compose)..."
    $DOCKER_COMPOSE_CMD down --remove-orphans || true
    
    echo ""
    echo "🔨 Docker 이미지 빌드 (Docker Compose)..."
    $DOCKER_COMPOSE_CMD build --no-cache
    
    echo ""
    echo "🚀 컨테이너 시작 (Docker Compose)..."
    $DOCKER_COMPOSE_CMD up -d
    
    # 상태 확인
    echo ""
    echo "📊 배포 상태 확인..."
    sleep 5
    
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
        echo "✅ 배포 성공!"
        echo ""
        echo "🌐 접속 정보:"
        echo "   • Frontend: http://localhost:8080"
        echo "   • Backend API: http://localhost:8080/api"
        echo "   • API 문서: http://localhost:8080/docs"
        echo ""
        echo "📝 로그 확인:"
        echo "   $DOCKER_COMPOSE_CMD logs -f"
    else
        echo "❌ 배포 실패. 로그를 확인하세요:"
        echo "   $DOCKER_COMPOSE_CMD logs"
        exit 1
    fi

else
    # Docker Compose가 없는 경우 기본 Docker 명령어 사용
    echo ""
    echo "🧹 기존 컨테이너 정리 (기본 Docker)..."
    
    # 기존 컨테이너 중지 및 삭제
    if [ "$(docker ps -aq -f name=ai-rebalancing)" ]; then
        docker stop ai-rebalancing || true
        docker rm ai-rebalancing || true
    fi
    
    # 기존 이미지 삭제
    if [ "$(docker images -q ai-rebalancing-system)" ]; then
        docker rmi ai-rebalancing-system || true
    fi
    
    echo ""
    echo "🔨 Docker 이미지 빌드 (기본 Docker)..."
    docker build --no-cache -t ai-rebalancing-system .
    
    echo ""
    echo "🚀 컨테이너 시작 (기본 Docker)..."
    
    # 환경 변수 파일 옵션 설정
    ENV_FILE_OPTION=""
    if [ -f ".env" ]; then
        ENV_FILE_OPTION="--env-file .env"
    fi
    
    # 컨테이너 실행
    docker run -d \
        --name ai-rebalancing \
        -p 8080:8000 \
        $ENV_FILE_OPTION \
        --restart unless-stopped \
        ai-rebalancing-system
    
    # 상태 확인
    echo ""
    echo "📊 배포 상태 확인..."
    sleep 5
    
    if docker ps | grep -q "ai-rebalancing"; then
        echo "✅ 배포 성공!"
        echo ""
        echo "🌐 접속 정보:"
        echo "   • Frontend: http://localhost:8080"
        echo "   • Backend API: http://localhost:8080/api"
        echo "   • API 문서: http://localhost:8080/docs"
        echo ""
        echo "📝 로그 확인:"
        echo "   docker logs -f ai-rebalancing"
    else
        echo "❌ 배포 실패. 로그를 확인하세요:"
        echo "   docker logs ai-rebalancing"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 배포 완료!"
echo ""
echo "🛠️  유용한 명령어:"
if [ ! -z "$DOCKER_COMPOSE_CMD" ]; then
    echo "   • 로그 확인: $DOCKER_COMPOSE_CMD logs -f"
    echo "   • 중지: $DOCKER_COMPOSE_CMD down"
    echo "   • 재시작: $DOCKER_COMPOSE_CMD restart"
else
    echo "   • 로그 확인: docker logs -f ai-rebalancing"
    echo "   • 중지: docker stop ai-rebalancing"
    echo "   • 재시작: docker restart ai-rebalancing"
fi
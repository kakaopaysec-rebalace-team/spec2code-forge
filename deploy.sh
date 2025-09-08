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

# 기존 컨테이너 정리
echo ""
echo "🧹 기존 컨테이너 정리..."
docker-compose down --remove-orphans || true
docker system prune -f

# 이미지 빌드 (캐시 없이)
echo ""
echo "🔨 Docker 이미지 빌드..."
docker-compose build --no-cache

# 컨테이너 시작
echo ""
echo "🚀 컨테이너 시작..."
docker-compose up -d

# 상태 확인
echo ""
echo "📊 배포 상태 확인..."
sleep 5

if docker-compose ps | grep -q "Up"; then
    echo "✅ 배포 성공!"
    echo ""
    echo "🌐 접속 정보:"
    echo "   • Frontend: http://localhost:8080"
    echo "   • Backend API: http://localhost:8080/api"
    echo "   • API 문서: http://localhost:8080/docs"
    echo ""
    echo "📝 로그 확인:"
    echo "   docker-compose logs -f"
else
    echo "❌ 배포 실패. 로그를 확인하세요:"
    echo "   docker-compose logs"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 배포 완료!"
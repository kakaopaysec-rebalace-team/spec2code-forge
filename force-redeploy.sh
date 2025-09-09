#!/bin/bash

# AI Asset Rebalancing System - Force Redeploy Script
# 강제 재배포 스크립트 - 캐시 완전 삭제 후 새로 빌드

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-system"

echo "🔄 AI Asset Rebalancing System - 강제 재배포"
echo "Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 현재 상태 확인
echo "📋 현재 배포 상태 확인..."
if docker ps -q -f name=${APP_NAME} >/dev/null; then
    echo "   기존 컨테이너 발견: ${APP_NAME}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep ${APP_NAME}
else
    echo "   기존 컨테이너 없음"
fi

# 2. 최신 소스 받기
echo ""
echo "📥 최신 소스 받기..."
git fetch origin main
git reset --hard origin/main
echo "   ✅ 최신 코드로 업데이트 완료"

# 3. 완전 정리
echo ""
echo "🧹 Docker 환경 완전 정리..."

# 기존 컨테이너 강제 정지 및 삭제
if docker ps -aq -f name=${APP_NAME} >/dev/null 2>&1; then
    echo "   기존 ${APP_NAME} 컨테이너 강제 삭제 중..."
    docker stop ${APP_NAME} 2>/dev/null || true
    docker rm -f ${APP_NAME} 2>/dev/null || true
fi

# 기존 이미지 삭제
if docker images -q ${IMAGE_NAME} >/dev/null 2>&1; then
    echo "   기존 ${IMAGE_NAME} 이미지 삭제 중..."
    docker rmi -f ${IMAGE_NAME} 2>/dev/null || true
fi

# 모든 <none> 이미지 삭제
echo "   dangling 이미지 정리 중..."
docker image prune -f

# Docker 빌드 캐시 삭제
echo "   Docker 빌드 캐시 정리 중..."
docker builder prune -f

# 시스템 전체 정리
echo "   Docker 시스템 전체 정리 중..."
docker system prune -f --volumes

# 4. 로컬 빌드 캐시 정리
echo ""
echo "🗂️  로컬 빌드 캐시 정리..."
if [ -d "node_modules" ]; then
    echo "   node_modules 삭제 중..."
    rm -rf node_modules
fi

if [ -d "dist" ]; then
    echo "   dist 디렉토리 삭제 중..."
    rm -rf dist
fi

if [ -d ".vite" ]; then
    echo "   Vite 캐시 삭제 중..."
    rm -rf .vite
fi

# npm 캐시 정리
if command -v npm >/dev/null 2>&1; then
    echo "   npm 캐시 정리 중..."
    npm cache clean --force
fi

# 5. 환경 변수 확인
echo ""
echo "⚙️  환경 변수 확인..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "   .env.example을 복사하여 .env 생성..."
        cp .env.example .env
        echo "   ⚠️  .env 파일을 편집하여 API 키를 설정하세요!"
    else
        echo "   ⚠️  .env 파일이 없습니다. 수동으로 생성하세요."
    fi
else
    echo "   ✅ .env 파일 존재"
fi

# 6. 완전 새로 빌드
echo ""
echo "🔨 Docker 이미지 완전 새로 빌드..."
docker build \
    --no-cache \
    --pull \
    --rm \
    -t ${IMAGE_NAME} \
    .

echo "   ✅ 이미지 빌드 완료!"

# 7. 컨테이너 실행
echo ""
echo "🚀 새 컨테이너 시작..."

# 환경 변수 파일 옵션
ENV_OPTION=""
if [ -f ".env" ]; then
    ENV_OPTION="--env-file .env"
fi

# 데이터 디렉토리 준비
mkdir -p ./data ./logs
chmod 755 ./data ./logs

# 새 컨테이너 실행
docker run -d \
    --name ${APP_NAME} \
    --publish 80:8000 \
    ${ENV_OPTION} \
    --restart unless-stopped \
    --memory="2g" \
    --cpus="2.0" \
    --volume "$(pwd)/data:/app/data:rw" \
    --volume "$(pwd)/logs:/app/logs:rw" \
    --health-cmd="curl -f http://localhost:8000/health || exit 1" \
    --health-interval=30s \
    --health-timeout=10s \
    --health-retries=3 \
    --health-start-period=60s \
    --log-driver=json-file \
    --log-opt max-size=100m \
    --log-opt max-file=3 \
    ${IMAGE_NAME}

# 8. 배포 확인
echo ""
echo "📊 배포 확인..."
sleep 15

if docker ps --format "{{.Names}}" | grep -q "^${APP_NAME}$"; then
    echo "   ✅ 컨테이너 정상 실행 중!"
    
    # 헬스 체크
    echo "   헬스 체크 대기 중..."
    for i in {1..10}; do
        if docker exec ${APP_NAME} curl -f http://localhost:8000/health &>/dev/null; then
            echo "   ✅ 헬스 체크 통과!"
            break
        elif [ $i -eq 10 ]; then
            echo "   ⚠️  헬스 체크 실패, 하지만 배포는 완료됨"
        else
            echo "   헬스 체크 대기 중... ($i/10)"
            sleep 3
        fi
    done
    
    # 버전 확인 (프론트엔드에서 특정 키워드 검색)
    echo ""
    echo "🔍 배포된 버전 확인..."
    sleep 5
    
    FRONTEND_CHECK=$(curl -s http://localhost/ 2>/dev/null || echo "error")
    if echo "$FRONTEND_CHECK" | grep -qi "rebalancing\|strategy\|portfolio"; then
        echo "   ✅ 업데이트된 버전 확인 완료!"
    else
        echo "   ⚠️  버전 확인 실패, 수동 확인 필요"
    fi
    
else
    echo "   ❌ 컨테이너 실행 실패!"
    echo "   로그 확인: docker logs ${APP_NAME}"
    exit 1
fi

# 9. 결과 요약
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 강제 재배포 완료!"
echo ""
echo "🌐 접속 정보:"
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
echo "   • Frontend: http://$SERVER_IP/"
echo "   • API 문서: http://$SERVER_IP:8003/docs"
echo "   • 헬스 체크: http://$SERVER_IP:8003/health"
echo ""
echo "🛠️  관리 명령어:"
echo "   • 실시간 로그: docker logs -f ${APP_NAME}"
echo "   • 컨테이너 상태: docker ps"
echo "   • 컨테이너 내부 접속: docker exec -it ${APP_NAME} /bin/bash"
echo ""
echo "⚠️  브라우저 캐시 삭제:"
echo "   • Chrome/Edge: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)"
echo "   • Firefox: Ctrl+F5 (Windows) / Cmd+Shift+R (Mac)"
echo "   • 또는 시크릿/프라이빗 모드에서 접속"
echo ""
echo "📋 최신 기능 확인:"
echo "   1. 리밸런싱 시작 페이지에서 실제 DB 데이터 표시"
echo "   2. '모든 전략 펼치기' 버튼으로 전략 목록 확장/축소"
echo "   3. 결과 페이지에서 실제 데이터 기반 차트 표시"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
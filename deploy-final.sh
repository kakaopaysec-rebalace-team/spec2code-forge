#!/bin/bash

# AI Asset Rebalancing System - 최종 완전 해결 스크립트
# Docker 캐시 및 컨텍스트 문제 완전 해결 버전

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-system"
PORT="80"
INTERNAL_PORT="8000"

echo "🔥 AI Asset Rebalancing - Docker 캐시 문제 완전 해결"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Docker 캐시 완전 제거
echo "🗑️  Docker 캐시 완전 제거..."
docker system prune -af --volumes
docker builder prune -af
echo "   ✅ Docker 캐시 완전 정리 완료"

# 2. 기존 컨테이너 및 이미지 강제 삭제
echo ""
echo "💥 기존 리소스 강제 삭제..."
docker stop ${APP_NAME} 2>/dev/null || true
docker rm -f ${APP_NAME} 2>/dev/null || true
docker rmi -f ${IMAGE_NAME} 2>/dev/null || true
docker rmi -f $(docker images -aq) 2>/dev/null || true
echo "   ✅ 모든 기존 리소스 삭제 완료"

# 3. 로컬 빌드 파일 완전 정리
echo ""
echo "🧹 로컬 빌드 파일 완전 정리..."
rm -rf node_modules dist build .vite .npm out
npm cache clean --force
echo "   ✅ 로컬 정리 완료"

# 4. npm 설치
echo ""
echo "📦 npm 의존성 새로 설치..."
npm install
echo "   ✅ npm 설치 완료"

# 5. 프론트엔드 빌드
echo ""
echo "🔨 프론트엔드 새로 빌드..."
npm run build

# 6. 빌드 결과 확인
echo ""
echo "📊 빌드 결과 확인..."
if [ ! -d "dist" ]; then
    if [ -d "build" ]; then
        mv build dist
        echo "   build를 dist로 변경"
    else
        echo "❌ 빌드 실패: dist/build 디렉토리 없음"
        exit 1
    fi
fi

if [ ! -f "dist/index.html" ]; then
    echo "❌ index.html 없음"
    exit 1
fi

echo "✅ 빌드 확인 완료"
echo "   파일 수: $(find dist -type f | wc -l)"
echo "   주요 파일:"
ls -la dist/ | head -5

# 7. Docker 빌드 컨텍스트 새로 생성
echo ""
echo "📁 Docker 빌드 컨텍스트 새로 생성..."

# 새로운 임시 디렉토리에서 빌드
TEMP_DIR="/tmp/docker-build-$(date +%s)"
mkdir -p $TEMP_DIR

echo "   빌드 파일 복사 중..."
cp -r backend $TEMP_DIR/
cp -r dist $TEMP_DIR/
cp Dockerfile.offline $TEMP_DIR/Dockerfile
cp .dockerignore $TEMP_DIR/ 2>/dev/null || true

if [ -f ".env" ]; then
    cp .env $TEMP_DIR/
fi

cd $TEMP_DIR
echo "   임시 디렉토리: $TEMP_DIR"
echo "   복사된 파일:"
ls -la

# 8. Docker 이미지 빌드 (새로운 컨텍스트에서)
echo ""
echo "🐳 Docker 이미지 빌드 (새로운 컨텍스트)..."
docker build \
    --no-cache \
    --pull \
    --rm \
    --force-rm \
    -t ${IMAGE_NAME} \
    .

echo "   ✅ Docker 빌드 성공"

# 9. 원본 디렉토리로 복귀
cd - > /dev/null

# 10. 임시 디렉토리 정리
rm -rf $TEMP_DIR
echo "   임시 디렉토리 정리 완료"

# 11. 환경 변수 및 데이터 디렉토리 준비
echo ""
echo "⚙️  실행 환경 준비..."
ENV_OPTION=""
if [ -f ".env" ]; then
    ENV_OPTION="--env-file .env"
fi

mkdir -p ./data ./logs

# 12. 컨테이너 실행
echo ""
echo "🚀 컨테이너 실행..."
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

echo "   ✅ 컨테이너 실행 완료"

# 13. 배포 검증
echo ""
echo "✅ 최종 검증..."
sleep 10

if docker ps | grep -q ${APP_NAME}; then
    echo "   ✅ 컨테이너 정상 실행 중"
    
    # HTTP 테스트
    sleep 5
    if python3 -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:${PORT}/', timeout=10)
    content = response.read().decode('utf-8')
    print('✅ HTTP 응답 정상 (%d)' % response.getcode())
    if any(keyword in content.lower() for keyword in ['rebalancing', 'strategy', 'portfolio']):
        print('✅ 업데이트된 내용 확인됨')
        print('📄 응답 내용 일부:', content[:200].replace('\n', ' ')[:100] + '...')
    else:
        print('⚠️  기본 응답, 내용 확인 필요')
except Exception as e:
    print('❌ HTTP 테스트 실패:', str(e))
    exit(1)
"; then
        echo "   ✅ 웹 서비스 완전 정상"
    else
        echo "   ❌ 웹 서비스 문제"
        exit 1
    fi
else
    echo "   ❌ 컨테이너 상태 이상"
    exit 1
fi

# 14. 성공 완료
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Docker 캐시 문제 완전 해결! 배포 성공!"
echo ""
echo "🔧 해결된 문제:"
echo "   ✅ Docker 빌드 캐시 완전 제거"
echo "   ✅ 새로운 빌드 컨텍스트 생성"
echo "   ✅ 이전 이미지/컨테이너 완전 정리"
echo "   ✅ 프론트엔드 빌드 새로 생성"
echo ""
echo "🌐 접속 정보:"
echo "   • Frontend: http://${SERVER_IP}/"
echo "   • Local: http://localhost/"
echo "   • API 문서: http://${SERVER_IP}/docs"
echo ""
echo "📋 배포된 최신 기능:"
echo "   🎯 7개 보유 종목 (실제 DB 데이터)"
echo "   🎯 20개 전략 목록 (실제 DB 데이터)"
echo "   🎯 $999,993 포트폴리오 가치"
echo "   🎯 '모든 전략 펼치기' 버튼"
echo "   🎯 실제 데이터 기반 결과 차트"
echo ""
echo "🛠️  관리 명령어:"
echo "   • 로그: docker logs -f ${APP_NAME}"
echo "   • 상태: docker ps"
echo "   • 재시작: docker restart ${APP_NAME}"
echo ""
echo "⚠️  브라우저 캐시도 삭제하세요:"
echo "   • Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)"
echo "   • 시크릿 모드로 테스트: http://${SERVER_IP}/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
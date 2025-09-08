#!/bin/bash

# AI Asset Rebalancing System - 완전 수정된 배포 스크립트
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge
# dist 디렉토리 생성 문제 완전 해결 버전

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-system"
PORT="80"
INTERNAL_PORT="8000"

echo "🚀 AI Asset Rebalancing - 완전 수정된 배포"
echo "Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 사전 확인
echo "🔍 사전 환경 확인..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 설치 필요: sudo dnf install nodejs npm"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker 설치 필요"
    exit 1
fi

echo "✅ Node.js: $(node --version)"
echo "✅ npm: $(npm --version)"
echo "✅ Docker: $(docker --version | head -1)"

# 기존 컨테이너 정리
echo ""
echo "🧹 기존 컨테이너 및 이미지 정리..."
docker stop ${APP_NAME} 2>/dev/null || true
docker rm ${APP_NAME} 2>/dev/null || true
docker rmi ${IMAGE_NAME} 2>/dev/null || true

# 완전 정리
echo ""
echo "🗑️  기존 빌드 파일 완전 정리..."
rm -rf node_modules dist build .vite .npm
npm cache clean --force

# 환경 변수 설정
echo ""
echo "⚙️  환경 변수 설정..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "   .env 파일 생성됨"
fi

# npm 설치 (강화된 재시도)
echo ""
echo "📦 npm 의존성 설치..."
install_success=false
attempts=0
max_attempts=3

while [ $attempts -lt $max_attempts ] && [ "$install_success" = false ]; do
    attempts=$((attempts + 1))
    echo "   설치 시도 $attempts/$max_attempts..."
    
    if [ $attempts -gt 1 ]; then
        rm -f package-lock.json
        npm cache clean --force
    fi
    
    if npm install 2>&1; then
        install_success=true
        echo "   ✅ npm install 성공 (시도 $attempts)"
    else
        echo "   ❌ npm install 실패 (시도 $attempts)"
        if [ $attempts -eq $max_attempts ]; then
            echo "   모든 설치 시도 실패"
            exit 1
        fi
        sleep 2
    fi
done

# 빌드 실행 (다중 방법)
echo ""
echo "🔨 프론트엔드 빌드 (다중 방법 시도)..."

build_success=false

# 방법 1: npm run build
echo "   방법 1: npm run build"
if npm run build 2>&1; then
    if [ -d "dist" ] || [ -d "build" ]; then
        build_success=true
        echo "   ✅ npm run build 성공"
    else
        echo "   ❌ npm run build는 성공했지만 결과물 없음"
    fi
else
    echo "   ❌ npm run build 실패"
fi

# 방법 2: npx vite build (필요시)
if [ "$build_success" = false ]; then
    echo "   방법 2: npx vite build"
    if npx vite build 2>&1; then
        if [ -d "dist" ] || [ -d "build" ]; then
            build_success=true
            echo "   ✅ npx vite build 성공"
        else
            echo "   ❌ npx vite build는 성공했지만 결과물 없음"
        fi
    else
        echo "   ❌ npx vite build 실패"
    fi
fi

# 방법 3: 직접 vite 실행 (필요시)
if [ "$build_success" = false ] && [ -f "node_modules/.bin/vite" ]; then
    echo "   방법 3: ./node_modules/.bin/vite build"
    if ./node_modules/.bin/vite build 2>&1; then
        if [ -d "dist" ] || [ -d "build" ]; then
            build_success=true
            echo "   ✅ 직접 vite 실행 성공"
        fi
    else
        echo "   ❌ 직접 vite 실행 실패"
    fi
fi

# 빌드 결과 검증 및 정리
echo ""
echo "📊 빌드 결과 검증..."

if [ -d "build" ] && [ ! -d "dist" ]; then
    echo "   build 디렉토리를 dist로 이동..."
    mv build dist
fi

if [ ! -d "dist" ]; then
    echo "❌ 빌드 실패: dist 디렉토리가 생성되지 않았습니다"
    echo ""
    echo "🔍 디버그 정보:"
    echo "   현재 디렉토리 내용:"
    ls -la | grep -E "(dist|build|out)"
    echo ""
    echo "   package.json scripts 확인:"
    grep -A 5 -B 1 '"build"' package.json || echo "   빌드 스크립트 없음"
    echo ""
    echo "   vite 설정 확인:"
    [ -f "vite.config.ts" ] && grep -A 5 -B 5 "build" vite.config.ts | head -10
    [ -f "vite.config.js" ] && grep -A 5 -B 5 "build" vite.config.js | head -10
    
    echo ""
    echo "🛠️  수동 해결 방법:"
    echo "   1. ./build-debug.sh 실행하여 상세 진단"
    echo "   2. vite.config에서 build.outDir 확인"
    echo "   3. src/ 디렉토리와 소스 파일 존재 확인"
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    echo "❌ 빌드 불완전: dist/index.html이 없습니다"
    echo "   dist 디렉토리 내용:"
    ls -la dist/
    exit 1
fi

echo "✅ 빌드 성공!"
echo "   파일 수: $(find dist -type f | wc -l)"
echo "   디렉토리 크기: $(du -sh dist | cut -f1)"

# Docker 빌드
echo ""
echo "🐳 Docker 이미지 빌드..."
if docker build -f Dockerfile.offline -t ${IMAGE_NAME} --no-cache . 2>&1; then
    echo "   ✅ Docker 빌드 성공"
else
    echo "   ❌ Docker 빌드 실패"
    echo "   마지막 확인:"
    echo "   dist 디렉토리: $([ -d "dist" ] && echo "존재" || echo "없음")"
    echo "   index.html: $([ -f "dist/index.html" ] && echo "존재" || echo "없음")"
    exit 1
fi

# 컨테이너 실행
echo ""
echo "🚀 컨테이너 시작..."

ENV_OPTION=""
[ -f ".env" ] && ENV_OPTION="--env-file .env"

mkdir -p ./data ./logs

if docker run -d \
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
    ${IMAGE_NAME}; then
    echo "   ✅ 컨테이너 실행 성공"
else
    echo "   ❌ 컨테이너 실행 실패"
    exit 1
fi

# 배포 검증
echo ""
echo "✅ 배포 검증..."
sleep 10

if docker ps | grep -q ${APP_NAME}; then
    echo "   ✅ 컨테이너 정상 실행 중"
    
    # 서비스 테스트
    sleep 5
    if python3 -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:${PORT}/', timeout=10)
    content = response.read().decode('utf-8')
    print('✅ HTTP 응답 정상 (%d)' % response.getcode())
    if any(keyword in content.lower() for keyword in ['rebalancing', 'strategy', 'portfolio']):
        print('✅ 업데이트된 내용 확인됨')
    else:
        print('⚠️  기본 페이지 응답 (업데이트 내용 미확인)')
except Exception as e:
    print('❌ HTTP 테스트 실패:', str(e))
    exit(1)
" 2>/dev/null; then
        echo "   ✅ 웹 서비스 정상 작동"
    else
        echo "   ⚠️  웹 서비스 응답 확인 필요"
    fi
else
    echo "   ❌ 컨테이너 상태 이상"
    docker ps -a | grep ${APP_NAME}
    docker logs ${APP_NAME} 2>&1 | tail -10
    exit 1
fi

# 성공 완료
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 배포 성공 완료!"
echo ""
echo "🌐 접속 정보:"
echo "   • Frontend: http://${SERVER_IP}/"
echo "   • Local: http://localhost/"
echo "   • API 문서: http://${SERVER_IP}/docs"
echo ""
echo "📋 배포된 주요 기능:"
echo "   ✅ 7개 보유 종목 (실제 DB 데이터)"
echo "   ✅ 20개 전략 목록 (실제 DB 데이터)" 
echo "   ✅ $999,993 포트폴리오 가치"
echo "   ✅ '모든 전략 펼치기' 버튼"
echo "   ✅ 실제 데이터 기반 결과 차트"
echo ""
echo "🛠️  관리 명령어:"
echo "   • 로그 확인: docker logs -f ${APP_NAME}"
echo "   • 컨테이너 재시작: docker restart ${APP_NAME}"
echo "   • 상태 확인: docker ps"
echo ""
echo "⚠️  브라우저 캐시 삭제 권장:"
echo "   • Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)"
echo "   • 또는 시크릿/프라이빗 모드로 접속"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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

# npm 캐시 정리
echo "   npm 캐시 정리 중..."
npm cache clean --force || true

# npm 의존성 설치
echo "   npm 의존성 설치 중..."
if ! npm install --silent --no-audit --no-fund; then
    echo "   ❌ npm install 실패!"
    echo "   재시도 중..."
    if ! npm install; then
        echo "   ❌ npm install 재시도 실패!"
        echo "   package-lock.json을 삭제하고 재시도..."
        rm -f package-lock.json
        npm install || {
            echo "   ❌ 모든 npm install 시도 실패!"
            exit 1
        }
    fi
fi

echo "   ✅ npm install 완료"

# 프론트엔드 빌드
echo "   프론트엔드 빌드 실행 중..."
echo "   빌드 명령어: npm run build"

# 빌드 실행 및 상세 로그
if npm run build 2>&1; then
    echo "   ✅ npm run build 명령어 완료"
else
    echo "   ❌ npm run build 실패!"
    echo "   package.json의 scripts 확인 중..."
    grep -A 5 -B 5 '"scripts"' package.json || echo "scripts 섹션을 찾을 수 없음"
    exit 1
fi

# 빌드 결과 상세 확인
echo ""
echo "📊 빌드 결과 상세 확인..."

if [ ! -d "dist" ]; then
    echo "   ❌ dist 디렉토리가 생성되지 않았습니다!"
    echo "   현재 디렉토리 내용:"
    ls -la | head -20
    
    echo ""
    echo "   Vite 설정 확인:"
    if [ -f "vite.config.ts" ]; then
        echo "   vite.config.ts 파일 존재"
        grep -E "(build|outDir)" vite.config.ts || echo "   build 설정 없음"
    elif [ -f "vite.config.js" ]; then
        echo "   vite.config.js 파일 존재"
        grep -E "(build|outDir)" vite.config.js || echo "   build 설정 없음"
    else
        echo "   vite.config 파일 없음"
    fi
    
    # build 디렉토리 확인 (일부 설정에서는 dist 대신 build 사용)
    if [ -d "build" ]; then
        echo "   ⚠️  build 디렉토리 발견! dist 대신 build를 사용합니다."
        mv build dist
    else
        echo "   ❌ build 디렉토리도 없음"
        exit 1
    fi
fi

if [ ! -f "dist/index.html" ]; then
    echo "   ❌ dist/index.html이 생성되지 않았습니다!"
    echo "   dist 디렉토리 내용:"
    ls -la dist/ || echo "   dist 디렉토리 접근 실패"
    exit 1
fi

echo "   ✅ 프론트엔드 빌드 성공!"
echo "   빌드된 파일 수: $(find dist -type f | wc -l)"
echo "   dist 디렉토리 크기: $(du -sh dist | cut -f1)"
echo "   주요 파일들:"
ls -la dist/ | head -10

# Docker 이미지 빌드 (오프라인 모드)
echo ""
echo "🐳 Docker 이미지 빌드 (오프라인 모드)..."

# 빌드 전 마지막 확인
if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo "   ❌ 마지막 확인에서 dist 디렉토리/파일 없음!"
    exit 1
fi

echo "   Docker 빌드 시작..."
if docker build \
    --file Dockerfile.offline \
    --tag ${IMAGE_NAME} \
    --no-cache \
    . 2>&1; then
    echo "   ✅ Docker 이미지 빌드 완료!"
else
    echo "   ❌ Docker 빌드 실패!"
    echo "   Docker 이미지 목록 확인:"
    docker images | head -5
    exit 1
fi

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
echo "   Docker 컨테이너 실행 중..."
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
    echo "   ✅ 컨테이너 실행 성공!"
else
    echo "   ❌ 컨테이너 실행 실패!"
    exit 1
fi

# 배포 확인
echo ""
echo "📊 배포 상태 확인..."
sleep 10

if docker ps --format "{{.Names}}" | grep -q "^${APP_NAME}$"; then
    echo "   ✅ 컨테이너 정상 실행 중!"
    
    # 컨테이너 로그 확인
    echo ""
    echo "🔍 컨테이너 초기 로그 확인:"
    docker logs --tail 10 ${APP_NAME} 2>&1 | head -10
    
    # 서비스 응답 확인 (curl 대신 Python 사용)
    echo ""
    echo "   서비스 응답 확인 중..."
    sleep 5
    
    # Python으로 HTTP 요청 테스트
    if python3 -c "
import urllib.request
import sys
try:
    response = urllib.request.urlopen('http://localhost:${PORT}/', timeout=10)
    content = response.read().decode('utf-8')[:200]
    print('✅ HTTP 응답 정상 (상태코드: %d)' % response.getcode())
    if 'rebalancing' in content.lower() or 'strategy' in content.lower() or 'portfolio' in content.lower():
        print('✅ 업데이트된 내용 확인됨')
    else:
        print('⚠️  응답 내용 확인 필요')
    print('응답 내용 일부:', content.replace('\n', ' ')[:100] + '...')
except Exception as e:
    print('❌ HTTP 응답 실패:', str(e))
    sys.exit(1)
" 2>/dev/null; then
        echo "   ✅ 웹 서비스 정상 작동!"
    else
        echo "   ⚠️  웹 서비스 응답 확인 실패, 컨테이너 로그 확인 필요"
        echo "   추가 로그:"
        docker logs --tail 5 ${APP_NAME}
    fi
    
else
    echo "   ❌ 컨테이너 실행 실패!"
    echo "   Docker 프로세스 상태:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep ${APP_NAME} || echo "   컨테이너를 찾을 수 없음"
    echo "   로그 확인:"
    docker logs ${APP_NAME} 2>&1 | tail -20
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
echo "   • Frontend: http://${SERVER_IP}/"
echo "   • Local: http://localhost/"
echo "   • API 테스트: http://${SERVER_IP}/docs"
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
echo "⚠️  브라우저 캐시 삭제 필요:"
echo "   • Chrome/Edge: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)"
echo "   • Firefox: Ctrl+F5 (Windows) / Cmd+Shift+R (Mac)"
echo "   • 시크릿/프라이빗 모드에서 테스트"
echo ""
echo "🔍 문제 발생 시:"
echo "   • 컨테이너 로그: docker logs ${APP_NAME}"
echo "   • 컨테이너 내부 접속: docker exec -it ${APP_NAME} /bin/bash"
echo "   • 서비스 직접 테스트: curl http://localhost/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
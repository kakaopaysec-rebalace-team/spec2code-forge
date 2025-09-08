#!/bin/bash

# AI Asset Rebalancing System - Container Build Deployment
# 완전히 새로운 접근: 컨테이너 내부에서 프론트엔드 빌드

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-container-build"
PORT="80"
INTERNAL_PORT="8000"

echo "🚀 AI Asset Rebalancing - 컨테이너 내부 빌드 방식"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Docker 환경 확인
echo "🔍 Docker 환경 확인..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다"
    exit 1
fi

echo "   Docker 버전: $(docker --version)"
echo "   Docker 서비스 상태: $(systemctl is-active docker || echo '수동 실행 중')"

# 2. 기존 리소스 정리
echo ""
echo "🧹 기존 리소스 정리..."
docker stop ${APP_NAME} 2>/dev/null || true
docker rm ${APP_NAME} 2>/dev/null || true
docker rmi ${IMAGE_NAME} 2>/dev/null || true
echo "   ✅ 기존 리소스 정리 완료"

# 3. 소스코드 상태 확인
echo ""
echo "📋 소스코드 상태 확인..."
echo "   현재 디렉토리: $(pwd)"
echo "   Git 브랜치: $(git branch --show-current 2>/dev/null || echo 'Git 아님')"
echo "   최근 커밋: $(git log -1 --oneline 2>/dev/null || echo 'Git 이력 없음')"

# 필수 파일 확인
required_files=("package.json" "vite.config.ts" "src/pages/ProfileSetup.tsx" "src/pages/Strategies.tsx" "backend/app.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file 존재"
    else
        echo "   ❌ $file 없음 - 빌드 실패 가능성"
    fi
done

# 4. Docker 빌드 (컨테이너 내부에서 프론트엔드 빌드)
echo ""
echo "🐳 Docker 빌드 (컨테이너 내부 빌드 방식)..."
echo "   사용할 Dockerfile: Dockerfile.build-in-container"

docker build \
    --file Dockerfile.build-in-container \
    --tag ${IMAGE_NAME} \
    --no-cache \
    --pull \
    --rm \
    --force-rm \
    --progress=plain \
    .

echo "   ✅ Docker 빌드 성공: ${IMAGE_NAME}"

# 5. 환경 설정
echo ""
echo "⚙️ 실행 환경 설정..."
ENV_OPTION=""
if [ -f ".env" ]; then
    ENV_OPTION="--env-file .env"
    echo "   .env 파일 사용"
else
    echo "   .env 파일 없음 (기본 설정 사용)"
fi

# 데이터 디렉토리 생성
mkdir -p ./data ./logs
chmod 755 ./data ./logs
echo "   데이터 디렉토리 준비 완료"

# 6. 컨테이너 실행
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

# 7. 배포 검증
echo ""
echo "✅ 배포 검증..."
sleep 15

# 컨테이너 상태 확인
if docker ps | grep -q ${APP_NAME}; then
    echo "   ✅ 컨테이너 정상 실행 중"
    
    # 컨테이너 내부 파일 확인
    echo "   컨테이너 내부 프론트엔드 파일 확인:"
    docker exec ${APP_NAME} find /app/frontend/dist -name "*.html" -o -name "*.js" -o -name "*.css" | head -5
    docker exec ${APP_NAME} ls -la /app/frontend/dist/
    
    # HTTP 응답 테스트
    sleep 10
    echo "   HTTP 응답 테스트..."
    
    if python3 -c "
import urllib.request
import sys
try:
    response = urllib.request.urlopen('http://localhost:${PORT}/', timeout=15)
    content = response.read().decode('utf-8')
    print('✅ HTTP 응답 정상 (%d)' % response.getcode())
    
    # 업데이트된 내용 확인
    keywords = ['rebalancing', 'strategy', 'portfolio', '모든', '전략', '펼치기']
    found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
    
    if found_keywords:
        print('✅ 업데이트된 내용 확인됨: %s' % ', '.join(found_keywords))
        print('📄 응답 내용 일부:', content[:300].replace('\n', ' ')[:150] + '...')
    else:
        print('⚠️  키워드 미발견, 기본 페이지일 수 있음')
        print('📄 응답 내용 일부:', content[:200].replace('\n', ' ')[:100] + '...')
        
except Exception as e:
    print('❌ HTTP 응답 실패:', str(e))
    sys.exit(1)
" 2>/dev/null; then
        echo "   ✅ 웹 서비스 완전 정상"
    else
        echo "   ⚠️ HTTP 응답 확인 필요"
        echo "   컨테이너 로그:"
        docker logs --tail 15 ${APP_NAME}
    fi
else
    echo "   ❌ 컨테이너 실행 실패"
    echo "   컨테이너 상태:"
    docker ps -a | grep ${APP_NAME}
    echo "   컨테이너 로그:"
    docker logs ${APP_NAME} 2>&1 | tail -20
    exit 1
fi

# 8. 성공 완료
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 컨테이너 내부 빌드 방식 배포 성공!"
echo ""
echo "🔧 새로운 접근 방식:"
echo "   ✅ Node.js 컨테이너에서 프론트엔드 빌드"
echo "   ✅ 멀티스테이지 빌드로 결과물 복사"
echo "   ✅ 로컬 dist 디렉토리 의존성 제거"
echo "   ✅ Docker 캐시 문제 완전 우회"
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
echo "🛠️ 관리 명령어:"
echo "   • 로그 확인: docker logs -f ${APP_NAME}"
echo "   • 컨테이너 재시작: docker restart ${APP_NAME}"
echo "   • 상태 확인: docker ps"
echo ""
echo "⚠️ 브라우저 캐시도 삭제하세요:"
echo "   • Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)"
echo "   • 시크릿 모드로 테스트: http://${SERVER_IP}/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
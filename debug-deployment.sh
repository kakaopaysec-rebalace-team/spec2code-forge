#!/bin/bash

# AI Asset Rebalancing System - Deployment Debug Script
# 배포 상태 및 버전 확인 스크립트

echo "🔍 AI Asset Rebalancing System - 배포 상태 진단"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-system"

# 1. Git 상태 확인
echo "📋 Git 상태 확인:"
echo "   현재 브랜치: $(git branch --show-current)"
echo "   최신 커밋: $(git log --oneline -1)"
echo "   작업 디렉토리 상태:"
git status --porcelain | head -10

# 2. Docker 컨테이너 상태 확인
echo ""
echo "🐳 Docker 컨테이너 상태:"
if docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q ${APP_NAME}; then
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep ${APP_NAME}
    
    # 컨테이너 내부 파일 확인
    echo ""
    echo "📁 컨테이너 내부 파일 확인:"
    if docker exec ${APP_NAME} ls -la /app/frontend/dist/ 2>/dev/null; then
        echo "   ✅ 프론트엔드 빌드 파일 존재"
        
        # index.html 확인 (수정된 버전인지 확인)
        echo ""
        echo "📄 프론트엔드 index.html 내용 일부:"
        docker exec ${APP_NAME} head -20 /app/frontend/dist/index.html 2>/dev/null | grep -E "(title|Rebalancing|Strategy)" || echo "   index.html에서 키워드를 찾을 수 없음"
        
    else
        echo "   ❌ 프론트엔드 빌드 파일 없음"
    fi
    
    # 백엔드 파일 확인
    echo ""
    echo "📄 백엔드 주요 파일 확인:"
    docker exec ${APP_NAME} ls -la /app/backend/ 2>/dev/null | grep -E "(app\.py|database_manager\.py)" || echo "   백엔드 파일 확인 실패"
    
else
    echo "   ❌ ${APP_NAME} 컨테이너를 찾을 수 없음"
    echo "   현재 실행 중인 컨테이너:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
fi

# 3. Docker 이미지 확인
echo ""
echo "🖼️  Docker 이미지 상태:"
docker images | grep -E "${IMAGE_NAME}|REPOSITORY" || echo "   ${IMAGE_NAME} 이미지를 찾을 수 없음"

# 4. 포트 확인
echo ""
echo "🌐 포트 사용 상황:"
ss -tlnp | grep -E ":80[0-9][0-9]|:800[0-9]" || echo "   8000-8099 포트 범위에서 사용 중인 포트 없음"

# 5. 백엔드 API 응답 확인
echo ""
echo "🔌 백엔드 API 응답 확인:"
if curl -s http://localhost:8080/health >/dev/null 2>&1; then
    echo "   ✅ 헬스 체크 응답 정상"
    
    # 사용자 보유 종목 확인 (리밸런싱 관련 기능)
    echo "   보유 종목 API 테스트:"
    HOLDINGS_RESPONSE=$(curl -s http://localhost:8080/user-holdings 2>/dev/null || echo "error")
    if [[ "$HOLDINGS_RESPONSE" == *"error"* ]]; then
        echo "     ❌ /user-holdings API 응답 실패"
    else
        echo "     ✅ /user-holdings API 응답 정상"
        echo "     응답 내용 일부: $(echo "$HOLDINGS_RESPONSE" | head -1 | cut -c1-100)..."
    fi
    
    # 전략 목록 확인
    echo "   전략 목록 API 테스트:"
    STRATEGIES_RESPONSE=$(curl -s http://localhost:8080/strategies 2>/dev/null || echo "error")
    if [[ "$STRATEGIES_RESPONSE" == *"error"* ]]; then
        echo "     ❌ /strategies API 응답 실패"
    else
        echo "     ✅ /strategies API 응답 정상"
        echo "     응답 내용 일부: $(echo "$STRATEGIES_RESPONSE" | head -1 | cut -c1-100)..."
    fi
    
else
    echo "   ❌ 백엔드 응답 없음 (http://localhost:8080/health)"
fi

# 6. 프론트엔드 접속 확인
echo ""
echo "🌐 프론트엔드 접속 확인:"
FRONTEND_RESPONSE=$(curl -s http://localhost:8080/ 2>/dev/null | head -10 || echo "error")
if [[ "$FRONTEND_RESPONSE" == *"error"* ]]; then
    echo "   ❌ 프론트엔드 응답 없음"
else
    echo "   ✅ 프론트엔드 응답 있음"
    
    # HTML 내용에서 업데이트된 내용 확인
    if echo "$FRONTEND_RESPONSE" | grep -qi "rebalancing\|strategy\|portfolio"; then
        echo "     ✅ 리밸런싱 관련 키워드 발견 (업데이트된 버전일 가능성)"
    else
        echo "     ⚠️  리밸런싱 관련 키워드 없음 (이전 버전일 가능성)"
    fi
fi

# 7. 로컬 소스 파일 확인
echo ""
echo "📂 로컬 소스 파일 확인:"
if [ -f "src/pages/Rebalancing.tsx" ]; then
    echo "   ✅ Rebalancing.tsx 존재"
    if grep -q "showAllStrategies\|모든 전략 펼치기" src/pages/Rebalancing.tsx 2>/dev/null; then
        echo "     ✅ 업데이트된 기능 확인 (전략 펼치기 기능)"
    else
        echo "     ⚠️  업데이트된 기능 미확인"
    fi
else
    echo "   ❌ Rebalancing.tsx 파일 없음"
fi

if [ -f "src/pages/Results.tsx" ]; then
    echo "   ✅ Results.tsx 존재"
    if grep -q "실제 데이터\|getUserHoldings\|getAllStrategies" src/pages/Results.tsx 2>/dev/null; then
        echo "     ✅ 데이터베이스 연동 기능 확인"
    else
        echo "     ⚠️  데이터베이스 연동 기능 미확인"
    fi
else
    echo "   ❌ Results.tsx 파일 없음"
fi

# 8. 빌드된 파일 확인 (dist 디렉토리)
echo ""
echo "📦 로컬 빌드 파일 확인:"
if [ -d "dist" ]; then
    echo "   ✅ dist 디렉토리 존재"
    echo "   빌드 시간: $(stat -c '%y' dist 2>/dev/null || stat -f '%Sm' dist 2>/dev/null || echo '확인불가')"
    
    if [ -f "dist/index.html" ]; then
        if grep -q "rebalancing\|strategy" dist/index.html 2>/dev/null; then
            echo "   ✅ 빌드된 파일에 업데이트 내용 포함"
        else
            echo "   ⚠️  빌드된 파일에 업데이트 내용 미확인"
        fi
    fi
else
    echo "   ❌ dist 디렉토리 없음 (빌드되지 않음)"
fi

# 9. 권장 해결 방법
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 문제 해결 권장 사항:"

# Docker 이미지 재빌드가 필요한지 확인
if docker exec ${APP_NAME} ls -la /app/frontend/dist/ 2>/dev/null | grep -q index.html; then
    echo "   1. 컨테이너 내부에 빌드 파일이 있지만 이전 버전일 가능성"
    echo "      → 강제 재빌드 권장: ./deploy.sh"
    echo ""
    echo "   2. 브라우저 캐시 문제일 가능성"
    echo "      → 브라우저에서 Ctrl+Shift+R 또는 Cmd+Shift+R로 강력 새로고침"
    echo "      → 시크릿/프라이빗 브라우징 모드에서 테스트"
else
    echo "   1. 컨테이너 내부에 빌드 파일이 없음"
    echo "      → 즉시 재배포 필요: ./deploy.sh"
fi

echo ""
echo "   3. 즉시 해결 방법:"
echo "      docker stop ${APP_NAME} && docker rm ${APP_NAME}"
echo "      ./deploy.sh"
echo ""
echo "   4. 디버그용 명령어:"
echo "      docker logs -f ${APP_NAME}  # 실시간 로그 확인"
echo "      docker exec -it ${APP_NAME} /bin/bash  # 컨테이너 내부 접속"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
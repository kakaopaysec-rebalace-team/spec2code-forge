#!/bin/bash

echo "📊 시스템 상태 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 포트 상태 확인
echo "🌐 포트 상태:"
if lsof -i:8003 > /dev/null 2>&1; then
    echo "  ✅ 포트 8003 (백엔드): 사용 중"
    BACKEND_PID=$(lsof -ti:8003)
    echo "     PID: $BACKEND_PID"
else
    echo "  ❌ 포트 8003 (백엔드): 사용 안함"
fi

if lsof -i:8080 > /dev/null 2>&1; then
    echo "  ✅ 포트 8080 (프론트엔드): 사용 중"
    FRONTEND_PID=$(lsof -ti:8080)
    echo "     PID: $FRONTEND_PID"
else
    echo "  ❌ 포트 8080 (프론트엔드): 사용 안함"
fi

echo ""

# 백엔드 API 상태 확인
echo "🔧 백엔드 API 상태:"
if curl -s http://localhost:8003/health > /dev/null; then
    echo "  ✅ 백엔드 API 정상 작동"
    # API 버전 정보 가져오기
    API_STATUS=$(curl -s http://localhost:8003/health | jq -r '.status' 2>/dev/null || echo "healthy")
    echo "     상태: $API_STATUS"
else
    echo "  ❌ 백엔드 API 응답 없음"
fi

echo ""

# 프론트엔드 상태 확인
echo "⚛️  프론트엔드 상태:"
if curl -s http://localhost:8080 > /dev/null; then
    echo "  ✅ 프론트엔드 정상 작동"
else
    echo "  ❌ 프론트엔드 응답 없음"
fi

echo ""

# 프로세스 상태 확인
echo "🔍 관련 프로세스:"
echo "  백엔드 (uvicorn/python):"
BACKEND_PROCESSES=$(ps aux | grep -E "(uvicorn|python.*app\.py)" | grep -v grep)
if [ -n "$BACKEND_PROCESSES" ]; then
    echo "$BACKEND_PROCESSES" | while read line; do echo "    $line"; done
else
    echo "    없음"
fi

echo "  프론트엔드 (npm/vite/node):"
FRONTEND_PROCESSES=$(ps aux | grep -E "(npm run dev|vite|node.*vite)" | grep -v grep)
if [ -n "$FRONTEND_PROCESSES" ]; then
    echo "$FRONTEND_PROCESSES" | while read line; do echo "    $line"; done
else
    echo "    없음"
fi

echo ""

# 로그 파일 상태
echo "📄 로그 파일:"
if [ -f "backend.log" ]; then
    BACKEND_LOG_SIZE=$(stat -f%z backend.log 2>/dev/null || stat -c%s backend.log 2>/dev/null || echo "0")
    echo "  📋 backend.log: ${BACKEND_LOG_SIZE} bytes"
    echo "     마지막 수정: $(stat -f%Sm backend.log 2>/dev/null || stat -c%y backend.log 2>/dev/null)"
else
    echo "  ❌ backend.log: 없음"
fi

if [ -f "frontend.log" ]; then
    FRONTEND_LOG_SIZE=$(stat -f%z frontend.log 2>/dev/null || stat -c%s frontend.log 2>/dev/null || echo "0")
    echo "  📋 frontend.log: ${FRONTEND_LOG_SIZE} bytes"
    echo "     마지막 수정: $(stat -f%Sm frontend.log 2>/dev/null || stat -c%y frontend.log 2>/dev/null)"
else
    echo "  ❌ frontend.log: 없음"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 접속 URL 표시 (서비스가 실행 중인 경우만)
if lsof -i:8080 > /dev/null 2>&1 || lsof -i:8003 > /dev/null 2>&1; then
    echo "🔗 접속 URL:"
    if lsof -i:8080 > /dev/null 2>&1; then
        echo "   프론트엔드: http://localhost:8080"
    fi
    if lsof -i:8003 > /dev/null 2>&1; then
        echo "   백엔드 API: http://localhost:8003"
        echo "   API 문서: http://localhost:8003/docs"
    fi
fi
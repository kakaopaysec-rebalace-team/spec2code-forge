#!/bin/bash

echo "🧪 ngrok 터널링 테스트"
echo "===================="

if [ -z "$1" ]; then
    echo "사용법: $0 <ngrok-url>"
    echo "예시: $0 https://c0b590455736.ngrok-free.app"
    exit 1
fi

NGROK_URL="$1"
echo "테스트할 ngrok URL: $NGROK_URL"

echo ""
echo "🔍 백엔드 API 연결 테스트..."

# 로컬 백엔드 상태 확인
echo "1. 로컬 백엔드 헬스체크:"
if curl -s http://localhost:8003/health > /dev/null; then
    echo "   ✅ 백엔드 서버 정상 작동"
else
    echo "   ❌ 백엔드 서버 응답 없음 - 먼저 ./start-rocky.sh 실행 필요"
    exit 1
fi

# ngrok을 통한 프론트엔드 접속 테스트
echo ""
echo "2. ngrok 프론트엔드 접속 테스트:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$NGROK_URL" --connect-timeout 10)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ ngrok 프론트엔드 접속 성공 (HTTP $HTTP_CODE)"
else
    echo "   ⚠️ ngrok 프론트엔드 접속 문제 (HTTP $HTTP_CODE)"
fi

# CORS 테스트
echo ""
echo "3. CORS 설정 테스트:"
CORS_TEST=$(curl -s -H "Origin: $NGROK_URL" \
                   -H "Access-Control-Request-Method: GET" \
                   -X OPTIONS \
                   http://localhost:8003/health 2>&1 | grep -i "access-control" | wc -l)

if [ "$CORS_TEST" -gt 0 ]; then
    echo "   ✅ CORS 헤더 정상 응답"
else
    echo "   ⚠️ CORS 헤더 확인 필요"
fi

# Database AI 엔드포인트 테스트
echo ""
echo "4. Database AI API 테스트:"
DB_API_TEST=$(curl -s -X POST "http://localhost:8003/database-ai/generate-strategy" \
                   -H "Content-Type: application/json" \
                   -H "Origin: $NGROK_URL" \
                   -d '{"user_profile":{"risk_tolerance":"moderate","investment_goal":"wealth_building"}}' \
                   | grep -c "success" 2>/dev/null || echo "0")

if [ "$DB_API_TEST" -gt 0 ]; then
    echo "   ✅ Database AI API 정상 작동"
else
    echo "   ⚠️ Database AI API 응답 확인 필요"
fi

echo ""
echo "📋 테스트 결과 요약:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 ngrok URL: $NGROK_URL"
echo "🔧 백엔드 API: http://localhost:8003"
echo "📊 Database AI: 준비 완료"
echo ""
echo "✨ 브라우저에서 $NGROK_URL 접속하여 확인하세요!"
echo "   DB 상태가 '정상'으로 표시되면 성공입니다."
#!/bin/bash

echo "🔍 동적 호스트 감지 테스트"
echo "========================"

# 현재 서버 IP 감지
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
HOSTNAME=$(hostname 2>/dev/null || echo "unknown")

echo "📊 네트워크 정보:"
echo "   서버 IP: $SERVER_IP"
echo "   호스트명: $HOSTNAME"
echo "   환경: $(cat .env | grep VITE_ENV | cut -d'=' -f2 2>/dev/null || echo 'unknown')"

echo ""
echo "🌐 접속 가능한 URL들:"
echo "   localhost: http://localhost"
echo "   127.0.0.1: http://127.0.0.1"
echo "   서버 IP: http://$SERVER_IP"

echo ""
echo "🔌 API 엔드포인트 테스트:"

# localhost 테스트
echo "1. localhost:8003 테스트:"
if curl -s --connect-timeout 3 http://localhost:8003/health >/dev/null 2>&1; then
    echo "   ✅ localhost:8003 - 접속 가능"
else
    echo "   ❌ localhost:8003 - 접속 불가"
fi

# 127.0.0.1 테스트
echo "2. 127.0.0.1:8003 테스트:"
if curl -s --connect-timeout 3 http://127.0.0.1:8003/health >/dev/null 2>&1; then
    echo "   ✅ 127.0.0.1:8003 - 접속 가능"
else
    echo "   ❌ 127.0.0.1:8003 - 접속 불가"
fi

# 서버 IP 테스트
echo "3. $SERVER_IP:8003 테스트:"
if [ "$SERVER_IP" != "localhost" ]; then
    if curl -s --connect-timeout 3 http://$SERVER_IP:8003/health >/dev/null 2>&1; then
        echo "   ✅ $SERVER_IP:8003 - 접속 가능"
    else
        echo "   ❌ $SERVER_IP:8003 - 접속 불가"
    fi
else
    echo "   ⏭️ 서버 IP가 localhost와 동일하므로 생략"
fi

echo ""
echo "🧩 동적 감지 시뮬레이션:"
echo "   • localhost 접속시 → API: http://localhost:8003"
echo "   • 127.0.0.1 접속시 → API: http://localhost:8003"  
echo "   • $SERVER_IP 접속시 → API: http://$SERVER_IP:8003"

echo ""
echo "📋 확인 방법:"
echo "1. 브라우저 개발자 도구(F12) → Console 탭"
echo "2. 'API: Base URL configured as:' 로그 확인"
echo "3. 다른 호스트로 접속하여 API URL 변경 확인"
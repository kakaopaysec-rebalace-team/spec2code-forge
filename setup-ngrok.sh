#!/bin/bash

echo "🌐 ngrok 터널링 환경 설정"
echo "=========================="

# ngrok URL 입력받기
if [ -z "$1" ]; then
    echo "사용법: $0 <ngrok-url>"
    echo "예시: $0 https://c0b590455736.ngrok-free.app"
    exit 1
fi

NGROK_URL="$1"
echo "설정할 ngrok URL: $NGROK_URL"

# .env 파일 생성 (ngrok 환경용)
echo "📝 ngrok용 .env 파일 생성 중..."
cat > .env << EOF
# ngrok Tunnel Configuration
VITE_API_URL=http://localhost:8003
VITE_ENV=development
VITE_NGROK_URL=$NGROK_URL
EOF

echo "✅ .env 파일 생성 완료:"
cat .env

echo ""
echo "🔧 백엔드 CORS 설정 확인..."
if grep -q "allow_origins.*\*" backend/app.py; then
    echo "✅ 백엔드 CORS 설정이 ngrok을 지원합니다."
else
    echo "⚠️ 백엔드 CORS 설정 업데이트가 필요할 수 있습니다."
fi

echo ""
echo "📋 ngrok 사용 시 주의사항:"
echo "1. 백엔드 서버가 localhost:8003에서 실행 중이어야 합니다."
echo "2. ngrok이 프론트엔드(포트 80 또는 8080)를 터널링해야 합니다."
echo "3. CORS 설정으로 인해 첫 접속 시 약간의 지연이 있을 수 있습니다."

echo ""
echo "🚀 사용 순서:"
echo "1. 로컬 서버 시작: ./start-rocky.sh"
echo "2. 별도 터미널에서 ngrok 실행: ngrok http 80"
echo "3. 제공된 ngrok URL로 접속"

echo ""
echo "🌐 예상 접속 URL: $NGROK_URL"
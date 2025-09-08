#!/bin/bash

echo "🔧 Rocky Linux 환경 설정 중..."

# 서버 IP 자동 감지
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "감지된 서버 IP: $SERVER_IP"

# .env 파일 생성
echo "📝 .env 파일 생성 중..."
cat > .env << EOF
# Frontend API Configuration for Rocky Linux
VITE_API_URL=http://$SERVER_IP:8003
VITE_ENV=production
EOF

echo "✅ .env 파일 생성 완료:"
cat .env

# 프론트엔드 재빌드 필요 알림
echo ""
echo "⚠️ 환경변수 변경으로 인한 재빌드가 필요합니다:"
echo "   rm -rf dist node_modules"
echo "   npm install"
echo "   npm run build"
echo ""
echo "🚀 또는 start-rocky.sh 스크립트를 다시 실행하세요!"
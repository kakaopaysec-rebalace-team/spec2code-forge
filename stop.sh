#!/bin/bash

echo "🛑 프로세스 종료 중..."

# 포트 기반으로 프로세스 종료
echo "📡 포트 기반 프로세스 종료 중..."
lsof -ti:8003 | xargs kill -9 2>/dev/null || echo "포트 8003에 실행 중인 프로세스가 없습니다."
lsof -ti:8080 | xargs kill -9 2>/dev/null || echo "포트 8080에 실행 중인 프로세스가 없습니다."

# 프로세스 이름 기반 종료
echo "🔄 프로세스 이름 기반 종료 중..."
pkill -f "npm run dev" 2>/dev/null || echo "npm run dev 프로세스가 없습니다."
pkill -f "vite" 2>/dev/null || echo "vite 프로세스가 없습니다."
pkill -f "uvicorn" 2>/dev/null || echo "uvicorn 프로세스가 없습니다."
pkill -f "python.*app.py" 2>/dev/null || echo "Python app.py 프로세스가 없습니다."

# Node.js 프로세스 종료 (프론트엔드)
echo "🌐 Node.js 프로세스 종료 중..."
pkill -f "node.*vite" 2>/dev/null || echo "Node.js vite 프로세스가 없습니다."

# Python 백엔드 프로세스 종료  
echo "🐍 Python 백엔드 프로세스 종료 중..."
pkill -f "python.*start_backend.py" 2>/dev/null || echo "start_backend.py 프로세스가 없습니다."

# 대기 시간
sleep 2

# 실행 중인 관련 프로세스 확인
echo "📋 현재 실행 중인 관련 프로세스 확인:"
echo "포트 8003 (백엔드):"
lsof -i:8003 2>/dev/null || echo "  ✅ 포트 8003 사용 중인 프로세스 없음"
echo "포트 8080 (프론트엔드):"
lsof -i:8080 2>/dev/null || echo "  ✅ 포트 8080 사용 중인 프로세스 없음"

echo "✅ 프로세스 종료 완료!!!!"
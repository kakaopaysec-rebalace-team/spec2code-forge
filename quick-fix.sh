#!/bin/bash

# Quick Fix for Missing Dependencies
echo "🚀 Quick Fix 실행 중..."

cd backend
source venv/bin/activate || { python3 -m venv venv && source venv/bin/activate; }

# 가장 중요한 누락 패키지들만 빠르게 설치
echo "📦 핵심 패키지 설치..."
pip install aiohttp aiosqlite psutil anthropic lxml httpx >/dev/null 2>&1

echo "✅ Quick Fix 완료!"
echo "🔄 서버 재시작: ./restart.sh"
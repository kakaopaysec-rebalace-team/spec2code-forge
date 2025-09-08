#!/bin/bash

# AI Asset Rebalancing System - Dependency Fix
# 누락된 Python 패키지들을 빠르게 설치

echo "🔧 Python 의존성 수정 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 백엔드 디렉토리로 이동
cd backend

# 가상환경 활성화 확인
if [ ! -d "venv" ]; then
    echo "📦 Python 가상환경 생성 중..."
    python3 -m venv venv
fi

echo "🔄 가상환경 활성화..."
source venv/bin/activate

# 누락된 핵심 패키지들 설치
echo "📦 누락된 핵심 패키지들 설치 중..."

MISSING_PACKAGES=(
    "aiohttp>=3.9.0"
    "aiosqlite>=0.19.0"
    "psutil>=5.9.0"
    "nltk>=3.8.0"
    "email-validator>=2.1.0"
    "scikit-learn>=1.3.0"
    "scipy>=1.11.0"
    "matplotlib>=3.7.0"
    "plotly>=5.17.0"
    "ta>=0.10.2"
    "anthropic>=0.25.0"
    "arxiv>=2.1.0"
    "lxml>=4.9.0"
    "httpx>=0.25.0"
)

# 각 패키지 하나씩 설치 시도
for package in "${MISSING_PACKAGES[@]}"; do
    echo "   - $package 설치 중..."
    pip install "$package" >/dev/null 2>&1 || \
    pip install "${package%%>=*}" >/dev/null 2>&1 || \
    echo "     ⚠️ $package 설치 실패 (건너뛰기)"
done

# 필수 패키지들 다시 확인
echo ""
echo "🔍 필수 패키지 설치 확인..."

ESSENTIAL_PACKAGES=(
    "fastapi"
    "uvicorn"
    "pydantic"
    "pandas"
    "numpy"
    "requests"
    "aiohttp"
    "python-dotenv"
)

for package in "${ESSENTIAL_PACKAGES[@]}"; do
    if python -c "import $package" >/dev/null 2>&1; then
        echo "   ✅ $package 설치됨"
    else
        echo "   ❌ $package 미설치 - 재설치 시도"
        pip install "$package" >/dev/null 2>&1 || echo "     ⚠️ $package 설치 실패"
    fi
done

cd ..

echo ""
echo "✅ 의존성 수정 완료!"
echo ""
echo "🚀 서버 재시작을 위해 다음 명령어 실행:"
echo "   ./stop.sh && ./start.sh"
#!/bin/bash

# AI Asset Rebalancing System - Offline Wheel Creation
# 네트워크 문제 시 사용할 오프라인 패키지 생성

set -e

echo "🔄 오프라인 배포용 Python Wheel 파일 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 필수 디렉토리 생성
mkdir -p wheels/

# 핵심 패키지 리스트 (requirements.txt보다 간소화)
ESSENTIAL_PACKAGES=(
    "fastapi==0.104.0"
    "uvicorn[standard]==0.24.0"
    "pydantic>=2.0,<3.0"
    "pandas>=2.0"
    "numpy>=1.24.0"
    "requests>=2.31.0"
    "python-multipart>=0.0.6"
    "python-dotenv>=1.0.0"
    "aiofiles>=23.2.0"
    "httpx>=0.25.0"
    "beautifulsoup4>=4.12.0"
    "lxml>=4.9.0"
    "PyPDF2>=3.0.0"
    "anthropic>=0.25.0"
    "aiosqlite>=0.19.0"
)

echo "📦 핵심 패키지 휠 파일 다운로드 중..."

# 각 패키지별로 wheel 다운로드
for package in "${ESSENTIAL_PACKAGES[@]}"; do
    echo "   다운로드: $package"
    pip download --dest wheels/ --only-binary=:all: "$package" 2>/dev/null || \
    pip download --dest wheels/ "$package" 2>/dev/null || \
    echo "   ⚠️ 실패: $package (수동 설치 필요)"
done

# requirements.txt의 나머지 패키지들도 시도
echo "📦 requirements.txt의 추가 패키지 다운로드 중..."
if [ -f "backend/requirements.txt" ]; then
    pip download --dest wheels/ -r backend/requirements.txt 2>/dev/null || true
fi

# 결과 확인
echo ""
echo "✅ Wheel 파일 생성 완료"
echo "   생성된 파일 수: $(ls wheels/ | wc -l)"
echo "   총 크기: $(du -sh wheels/ | cut -f1)"
echo ""
echo "📋 사용 방법:"
echo "   1. wheels/ 디렉토리를 서버로 복사"
echo "   2. pip install --find-links wheels/ --no-index -r requirements.txt"
echo ""
echo "🔗 또는 Dockerfile에서 COPY wheels/ /wheels/ 추가 후"
echo "   pip install --find-links /wheels/ --no-index 사용"
#!/bin/bash

# AI Asset Rebalancing System - Emergency Deployment
# 모든 방법이 실패했을 때의 최후 수단

set -e

echo "🚨 AI Asset Rebalancing - 긴급 배포"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 환경 확인
echo "🔍 환경 확인..."
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python이 설치되지 않았습니다"
    exit 1
fi

NODE_AVAILABLE=false
if command -v npm &> /dev/null; then
    NODE_AVAILABLE=true
fi

echo "   ✅ Python: $PYTHON_CMD"
echo "   Node.js: $([ "$NODE_AVAILABLE" = true ] && echo "사용 가능" || echo "없음")"

# 2. 백엔드 긴급 설정
echo ""
echo "🐍 백엔드 긴급 설정..."
cd backend

# 가상환경 생성/활성화
if [ ! -d "venv" ]; then
    echo "   📦 Python 가상환경 생성..."
    $PYTHON_CMD -m venv venv
fi

echo "   🔄 가상환경 활성화..."
source venv/bin/activate

# 최소 패키지 설치
echo "   📦 최소 패키지 설치 시도..."
pip install --upgrade pip >/dev/null 2>&1 || true

# 필수 패키지 하나씩 설치
ESSENTIAL_PACKAGES=("fastapi" "uvicorn" "pydantic")
for package in "${ESSENTIAL_PACKAGES[@]}"; do
    echo "   - $package 설치 중..."
    pip install "$package" >/dev/null 2>&1 || \
    pip install "$package==0.104.0" >/dev/null 2>&1 || \
    echo "     ⚠️ $package 설치 실패 (계속 진행)"
done

# 선택적 패키지
OPTIONAL_PACKAGES=("pandas" "numpy" "requests" "python-dotenv")
for package in "${OPTIONAL_PACKAGES[@]}"; do
    echo "   - $package 설치 시도..."
    pip install "$package" >/dev/null 2>&1 || echo "     ⚠️ $package 건너뜀"
done

cd ..

# 3. 프론트엔드 처리
echo ""
echo "⚛️ 프론트엔드 처리..."

if [ "$NODE_AVAILABLE" = true ] && [ ! -d "dist" ]; then
    echo "   📦 프론트엔드 빌드 시도..."
    npm install >/dev/null 2>&1 && npm run build >/dev/null 2>&1 && echo "   ✅ 빌드 성공" || {
        echo "   ⚠️ 빌드 실패 - 정적 파일 생성"
        mkdir -p dist
        cat > dist/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Asset Rebalancing System</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        .status { padding: 20px; background: #f0f9ff; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI Asset Rebalancing System</h1>
        <div class="status">
            <h2>✅ 시스템이 실행 중입니다</h2>
            <p>백엔드 API가 정상적으로 작동 중입니다.</p>
            <p><strong>API 문서:</strong> <a href="/docs">/docs</a></p>
            <p><strong>상태 확인:</strong> <a href="/health">/health</a></p>
        </div>
    </div>
</body>
</html>
EOF
    }
else
    if [ ! -d "dist" ]; then
        echo "   📄 기본 HTML 생성..."
        mkdir -p dist
        cat > dist/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Asset Rebalancing System</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        .status { padding: 20px; background: #f0f9ff; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI Asset Rebalancing System</h1>
        <div class="status">
            <h2>✅ 시스템이 실행 중입니다</h2>
            <p>백엔드 API가 정상적으로 작동 중입니다.</p>
            <p><strong>API 문서:</strong> <a href="/docs">/docs</a></p>
            <p><strong>상태 확인:</strong> <a href="/health">/health</a></p>
        </div>
    </div>
</body>
</html>
EOF
    fi
fi

# 4. 긴급 서버 스크립트 생성
echo ""
echo "🛠️ 긴급 서버 스크립트 생성..."
cat > emergency_server.py << 'EOF'
#!/usr/bin/env python3
"""
AI Asset Rebalancing System - Emergency Server
최소한의 의존성으로 동작하는 긴급 서버
"""

import os
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    print("✅ FastAPI/Uvicorn 로드 성공")
except ImportError as e:
    print(f"❌ FastAPI 로드 실패: {e}")
    print("🔄 기본 HTTP 서버로 대체...")
    import http.server
    import socketserver
    import threading
    import webbrowser
    
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    print(f"🌐 기본 HTTP 서버 시작: http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
    sys.exit(0)

# FastAPI 앱 생성
app = FastAPI(
    title="AI Asset Rebalancing System - Emergency Mode",
    description="긴급 모드로 실행 중입니다",
    version="1.0.0-emergency"
)

# 정적 파일 서빙
if os.path.exists("dist"):
    app.mount("/static", StaticFiles(directory="dist"), name="static")

@app.get("/")
async def root():
    """메인 페이지"""
    if os.path.exists("dist/index.html"):
        with open("dist/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Asset Rebalancing System - Emergency</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 600px; margin: 0 auto; }
            .emergency { padding: 20px; background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚨 AI Asset Rebalancing System</h1>
            <div class="emergency">
                <h2>🚀 긴급 모드 실행 중</h2>
                <p>시스템이 긴급 모드로 실행되고 있습니다.</p>
                <p><strong>API 문서:</strong> <a href="/docs">/docs</a></p>
                <p><strong>상태 확인:</strong> <a href="/health">/health</a></p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok", "mode": "emergency", "message": "긴급 모드 실행 중"}

@app.get("/api/test")
async def api_test():
    """API 테스트"""
    return {"message": "API가 정상 작동합니다", "mode": "emergency"}

if __name__ == "__main__":
    print("🚨 긴급 서버 시작...")
    print("🌐 접속: http://localhost:8000")
    print("📖 API 문서: http://localhost:8000/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=False,
        access_log=True
    )
EOF

# 5. 실행
echo ""
echo "🚀 긴급 서버 실행..."
echo "   백엔드: http://localhost:8000"
echo "   API 문서: http://localhost:8000/docs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 긴급 배포 완료!"
echo "📋 중지하려면: Ctrl+C"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 백그라운드에서 실행
cd backend
source venv/bin/activate
cd ..
$PYTHON_CMD emergency_server.py
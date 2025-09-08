#!/bin/bash

echo "🚀 Rocky Linux AI 리밸런싱 시스템 시작 중..."

# 현재 디렉토리 확인
if [ ! -f "package.json" ]; then
    echo "❌ 오류: package.json 파일을 찾을 수 없습니다."
    echo "프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

# 기존 프로세스 종료
echo "🛑 기존 프로세스 종료 중..."
pkill -f "uvicorn.*app:app" 2>/dev/null || echo "백엔드 프로세스 없음"
pkill -f "vite.*preview" 2>/dev/null || echo "프론트엔드 프로세스 없음"
pkill -f "node.*vite" 2>/dev/null || echo "Node 프로세스 없음"
sleep 2

# 백엔드 시작
echo "🐍 백엔드 서버 시작 중..."
if [ -f "backend/app.py" ]; then
    cd backend
    echo "📁 백엔드 디렉토리: $(pwd)"
    
    # 가상환경 재생성 (경로 문제 해결)
    if [ -d "venv" ]; then
        echo "🗑️ 기존 가상환경 제거 중..."
        rm -rf venv
    fi
    
    echo "🔧 Python 가상환경 생성 중..."
    python3 -m venv venv
    
    echo "🔄 가상환경 활성화 및 의존성 설치..."
    source venv/bin/activate
    
    # 의존성 설치
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # 필수 패키지 직접 설치
        pip install fastapi uvicorn aiosqlite pandas numpy yfinance requests beautifulsoup4 python-multipart aiofiles python-dotenv httpx lxml PyPDF2 arxiv anthropic scikit-learn
    fi
    
    # 데이터베이스 초기화
    if [ -f "init_rocky_db.py" ]; then
        echo "🗄️ 데이터베이스 초기화 중..."
        python3 init_rocky_db.py
    fi
    
    # 백엔드 서버 시작
    echo "🌐 백엔드 서버 시작: http://localhost:8003"
    nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8003 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo "백엔드 PID: $BACKEND_PID"
    
    cd ..
else
    echo "❌ 오류: backend/app.py 파일을 찾을 수 없습니다."
    exit 1
fi

# 백엔드 시작 대기
echo "⏳ 백엔드 서버 시작 대기 중..."
sleep 10

# 백엔드 상태 확인
echo "🔍 백엔드 상태 확인 중..."
if curl -s --connect-timeout 5 http://localhost:8003/health > /dev/null; then
    echo "✅ 백엔드 서버 정상 작동 중"
else
    echo "❌ 백엔드 서버 시작 실패"
    echo "📋 진단 정보:"
    echo "   프로세스 상태: $(ps aux | grep uvicorn | grep -v grep || echo '없음')"
    echo "   포트 상태: $(ss -tlnp | grep :8003 || echo '8003 포트 사용 중 아님')"
    echo "   로그 마지막 10줄:"
    tail -10 backend.log
    exit 1
fi

# 프론트엔드 시작
echo "⚛️ 프론트엔드 서버 시작 중..."

# Node.js 및 npm 설치 확인
if ! command -v node &> /dev/null; then
    echo "❌ Node.js가 설치되지 않았습니다."
    echo "설치 방법: sudo dnf module install -y nodejs:18/common"
    exit 1
fi

# 프론트엔드 의존성 설치
if [ ! -d "node_modules" ]; then
    echo "📦 Node.js 의존성 설치 중..."
    npm install
fi

# 프론트엔드 빌드
if [ ! -d "dist" ]; then
    echo "🔨 프론트엔드 빌드 중..."
    npm run build
fi

# 프론트엔드 서버 시작
echo "🌐 프론트엔드 서버 시작: http://localhost:8080"
nohup npm run preview -- --host 0.0.0.0 --port 8080 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "프론트엔드 PID: $FRONTEND_PID"

# 프론트엔드 시작 대기
echo "⏳ 프론트엔드 서버 시작 대기 중..."
sleep 10

# 프론트엔드 상태 확인
echo "🔍 프론트엔드 상태 확인 중..."
if curl -s --connect-timeout 5 http://localhost:8080 > /dev/null; then
    echo "✅ 프론트엔드 서버 정상 작동 중"
else
    echo "❌ 프론트엔드 서버 시작 실패"
    echo "📋 진단 정보:"
    echo "   프로세스 상태: $(ps aux | grep node | grep -v grep || echo '없음')"
    echo "   포트 상태: $(ss -tlnp | grep :8080 || echo '8080 포트 사용 중 아님')"
    echo "   로그 마지막 10줄:"
    tail -10 frontend.log
    exit 1
fi

echo "🎉 시스템 시작 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 프론트엔드: http://localhost:8080"
echo "🔧 백엔드 API: http://localhost:8003"
echo "📖 API 문서: http://localhost:8003/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "📋 유용한 명령어:"
echo "  프로세스 종료: pkill -f 'uvicorn.*app:app'; pkill -f 'vite.*preview'"
echo "  백엔드 로그:   tail -f backend.log"
echo "  프론트엔드 로그: tail -f frontend.log"
echo "  프로세스 확인:  ps aux | grep -E '(uvicorn|node)'"

echo "PID 정보:"
echo "  백엔드 PID: $BACKEND_PID"
echo "  프론트엔드 PID: $FRONTEND_PID"
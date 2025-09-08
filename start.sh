#!/bin/bash

echo "🚀 AI 리밸런싱 시스템 시작 중..."

# 현재 디렉토리 확인
if [ ! -f "package.json" ]; then
    echo "❌ 오류: package.json 파일을 찾을 수 없습니다."
    echo "프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

# 기존 프로세스 종료
echo "🛑 기존 프로세스 종료 중..."
lsof -ti:8003 | xargs kill -9 2>/dev/null || echo "포트 8003 프로세스 없음"
lsof -ti:8080 | xargs kill -9 2>/dev/null || echo "포트 8080 프로세스 없음"

# 대기 시간
sleep 2

# 백엔드 시작 (백그라운드)
echo "🐍 백엔드 서버 시작 중..."
if [ -f "backend/app.py" ]; then
    cd backend
    echo "📁 백엔드 디렉토리로 이동: $(pwd)"
    
    # 가상환경 확인 및 생성
    if [ ! -d "venv" ]; then
        echo "🔧 Python 가상환경 생성 중..."
        python3 -m venv venv
    fi
    
    # 가상환경 활성화 및 의존성 설치
    echo "🔄 가상환경 활성화 및 의존성 확인 중..."
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install fastapi uvicorn "pydantic>=2.0,<3.0" "pandas>=2.0" numpy yfinance requests beautifulsoup4 python-multipart aiofiles python-dotenv httpx lxml PyPDF2 arxiv anthropic > /dev/null 2>&1
    
    # 백엔드 서버 시작
    echo "🌐 백엔드 서버 시작: http://localhost:8003"
    nohup uvicorn app:app --host 0.0.0.0 --port 8003 --reload > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo "백엔드 PID: $BACKEND_PID"
    
    cd ..
else
    echo "❌ 오류: backend/app.py 파일을 찾을 수 없습니다."
    exit 1
fi

# 백엔드 시작 대기
echo "⏳ 백엔드 서버 시작 대기 중..."
sleep 5

# 백엔드 상태 확인
echo "🔍 백엔드 상태 확인 중..."
if curl -s http://localhost:8003/health > /dev/null; then
    echo "✅ 백엔드 서버 정상 작동 중"
else
    echo "❌ 백엔드 서버 시작 실패"
    echo "로그 확인: tail -f backend.log"
    exit 1
fi

# 프론트엔드 시작
echo "⚛️  프론트엔드 서버 시작 중..."
echo "🌐 프론트엔드 서버 시작: http://localhost:8080"
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "프론트엔드 PID: $FRONTEND_PID"

# 프론트엔드 시작 대기
echo "⏳ 프론트엔드 서버 시작 대기 중..."
sleep 5

# 프론트엔드 상태 확인
echo "🔍 프론트엔드 상태 확인 중..."
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ 프론트엔드 서버 정상 작동 중"
else
    echo "⚠️  프론트엔드 서버 아직 시작 중... (정상적인 경우가 많습니다)"
fi

echo ""
echo "🎉 시스템 시작 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 프론트엔드: http://localhost:8080"
echo "🔧 백엔드 API: http://localhost:8003"
echo "📖 API 문서: http://localhost:8003/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 유용한 명령어:"
echo "  프로세스 종료: ./stop.sh"
echo "  백엔드 로그:   tail -f backend.log"
echo "  프론트엔드 로그: tail -f frontend.log"
echo "  프로세스 확인:  ps aux | grep -E '(uvicorn|vite)'"
echo ""
echo "PID 정보:"
echo "  백엔드 PID: $BACKEND_PID"
echo "  프론트엔드 PID: $FRONTEND_PID"
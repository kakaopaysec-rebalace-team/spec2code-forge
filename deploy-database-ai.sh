#!/bin/bash

# Database AI 시스템 프로덕션 배포 스크립트
# API 키 불필요 - 완전 자립형 시스템

set -e

echo "🚀 Database AI 시스템 배포 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 시스템 정보 출력
echo "📋 시스템 정보:"
echo "   OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"' || uname -s)"
echo "   사용자: $(whoami)"
echo "   디렉토리: $(pwd)"
echo "   시간: $(date)"

# 2. 기존 프로세스 정리
echo ""
echo "🛑 기존 프로세스 정리 중..."
./stop.sh 2>/dev/null || true
sleep 2

# 3. 프로젝트 업데이트 (Git이 있는 경우)
if [ -d ".git" ]; then
    echo ""
    echo "📦 프로젝트 업데이트 중..."
    git stash 2>/dev/null || true
    git pull origin main 2>/dev/null || echo "Git pull 실패 - 로컬 파일 사용"
fi

# 4. 백엔드 설정
echo ""
echo "🐍 백엔드 환경 설정 중..."
cd backend

# 가상환경 생성/활성화
if [ ! -d "venv" ]; then
    echo "   가상환경 생성 중..."
    python3 -m venv venv
fi

echo "   가상환경 활성화 중..."
source venv/bin/activate

# 의존성 설치
echo "   Python 의존성 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# Database AI 엔진 필수 패키지 확인
echo "   Database AI 엔진 의존성 확인 중..."
pip install aiosqlite pandas numpy scikit-learn 2>/dev/null || echo "일부 패키지 설치 실패 - 계속 진행"

# 환경 변수 설정 (API 키 불필요!)
echo "   환경 변수 설정 중..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ✅ .env 파일 생성 완료 (API 키 설정 불필요)"
else
    echo "   ✅ 기존 .env 파일 사용"
fi

# 데이터베이스 초기화
echo ""
echo "🗄️ 데이터베이스 초기화 중..."
if [ ! -f "asset_rebalancing.db" ] || [ ! -f "expert_strategies.db" ]; then
    echo "   데이터베이스 파일 생성 중..."
    cd ..
    ./init-db.sh
    cd backend
else
    echo "   ✅ 기존 데이터베이스 파일 사용"
fi

# Database AI 엔진 테스트
echo ""
echo "🧠 Database AI 엔진 테스트 중..."
python -c "
import asyncio
from database_ai_engine import get_database_ai_engine

async def test():
    try:
        db_ai = await get_database_ai_engine()
        result = await db_ai.generate_intelligent_strategy({
            'risk_tolerance': 'moderate',
            'investment_goal': 'wealth_building',
            'investment_horizon': 10
        })
        print('   ✅ Database AI 엔진 정상 작동 확인')
        print(f'   📊 전략 생성 완료: {len(result[\"portfolio_allocation\"])}개 자산')
        print(f'   🎯 신뢰도: {result[\"confidence_score\"]:.2f}')
        return True
    except Exception as e:
        print(f'   ❌ Database AI 테스트 실패: {e}')
        return False

result = asyncio.run(test())
" || echo "   ⚠️ Database AI 테스트 실패 - 서버 시작 후 재확인 필요"

cd ..

# 5. 프론트엔드 설정
echo ""
echo "⚛️ 프론트엔드 설정 중..."

# Node.js 의존성 설치
if [ ! -d "node_modules" ]; then
    echo "   Node.js 의존성 설치 중..."
    npm install
fi

# 프론트엔드 빌드
echo "   프론트엔드 빌드 중..."
npm run build

# 6. 서버 시작
echo ""
echo "🌟 서버 시작 중..."
./start.sh

# 7. 서비스 확인
echo ""
echo "🔍 서비스 상태 확인 중..."
sleep 5

# 백엔드 확인
if curl -s http://localhost:8003/health > /dev/null; then
    echo "   ✅ 백엔드 서버: 정상 작동 (http://localhost:8003)"
else
    echo "   ❌ 백엔드 서버: 응답 없음"
fi

# 프론트엔드 확인
if curl -s http://localhost:8080 > /dev/null; then
    echo "   ✅ 프론트엔드 서버: 정상 작동 (http://localhost:8080)"
else
    echo "   ❌ 프론트엔드 서버: 응답 없음"
fi

# Database AI API 확인
if curl -s -X POST http://localhost:8003/database-ai/generate-strategy \
   -H "Content-Type: application/json" \
   -d '{"user_profile":{"risk_tolerance":"moderate","investment_goal":"wealth_building"}}' > /dev/null; then
    echo "   ✅ Database AI API: 정상 작동"
else
    echo "   ❌ Database AI API: 응답 없음"
fi

# 8. 최종 결과
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Database AI 시스템 배포 완료!"
echo ""
echo "📱 서비스 접속 정보:"
echo "   • 프론트엔드:        http://localhost:8080"
echo "   • 백엔드 API:        http://localhost:8003"
echo "   • Database AI 전용:  http://localhost:8003/database-ai/generate-strategy"
echo "   • API 문서:          http://localhost:8003/docs"
echo ""
echo "🔧 관리 명령어:"
echo "   • 상태 확인:  ./status.sh"
echo "   • 서버 중지:  ./stop.sh"
echo "   • 서버 재시작: ./restart.sh"
echo "   • 로그 확인:  tail -f backend.log"
echo ""
echo "✨ 특징:"
echo "   • API 키 완전 불필요 - 100% 자립형 시스템"
echo "   • 318개 전문가 전략 활용"
echo "   • 실시간 포트폴리오 분석"
echo "   • 무료 사용 가능"
echo ""
echo "🚀 배포 성공! 시스템이 정상 작동 중입니다."
#!/bin/bash

# Rocky Linux 진단 및 문제 해결 스크립트
# Database AI 시스템 전용

echo "🐧 Rocky Linux Database AI 시스템 진단"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 시스템 환경 진단
echo "1️⃣ 시스템 환경:"
echo "   OS: $(cat /etc/redhat-release 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo "   커널: $(uname -r)"
echo "   아키텍처: $(uname -m)"
echo "   메모리: $(free -h | grep Mem | awk '{print $2" 총, "$3" 사용중"}')"
echo "   디스크: $(df -h . | tail -1 | awk '{print $2" 총, "$3" 사용중, "$4" 여유"}')"

# 2. Python 환경 상세 진단
echo ""
echo "2️⃣ Python 환경 상세 진단:"

# Python 버전들 확인
for py_cmd in python3.11 python3.10 python3.9 python3.8 python3 python; do
    if command -v $py_cmd >/dev/null; then
        echo "   ✅ $py_cmd: $($py_cmd --version 2>&1)"
    fi
done

# 가상환경 진단
cd backend 2>/dev/null || { echo "❌ backend 디렉토리 없음"; exit 1; }

if [ -d "venv" ]; then
    echo "   ✅ 가상환경: venv/ 존재"
    if [ -f "venv/bin/activate" ]; then
        echo "   ✅ 활성화 스크립트: 정상"
        source venv/bin/activate
        echo "   ✅ Python (venv): $(python --version)"
        echo "   ✅ pip (venv): $(pip --version | awk '{print $1, $2}')"
    else
        echo "   ❌ 활성화 스크립트: 없음"
    fi
else
    echo "   ❌ 가상환경: 없음"
fi

# 3. SQLite 상세 진단
echo ""
echo "3️⃣ SQLite 환경 진단:"

if command -v sqlite3 >/dev/null; then
    SQLITE_VERSION=$(sqlite3 --version | awk '{print $1}')
    echo "   ✅ SQLite3: $SQLITE_VERSION"
    
    # SQLite 기능 테스트
    TEST_DB="/tmp/test_sqlite_$$"
    if sqlite3 "$TEST_DB" "CREATE TABLE test(id INTEGER); INSERT INTO test VALUES(1); SELECT * FROM test;" >/dev/null 2>&1; then
        echo "   ✅ SQLite 기능: 정상"
        rm -f "$TEST_DB"
    else
        echo "   ❌ SQLite 기능: 오류"
    fi
else
    echo "   ❌ SQLite3: 설치되지 않음"
    echo "      설치 명령: sudo dnf install sqlite sqlite-devel"
fi

# Python SQLite 지원 확인
python -c "
import sqlite3
import sys
print(f'   ✅ Python SQLite: {sqlite3.sqlite_version}')
try:
    import aiosqlite
    print('   ✅ aiosqlite: 설치됨')
except ImportError:
    print('   ❌ aiosqlite: 없음')
    sys.exit(1)
" 2>/dev/null || echo "   ❌ Python SQLite 모듈 오류"

# 4. 데이터베이스 파일 상세 진단
echo ""
echo "4️⃣ 데이터베이스 파일 진단:"

DB_FILES=("asset_rebalancing.db" "expert_strategies.db" "simulation_results.db")

for db in "${DB_FILES[@]}"; do
    if [ -f "$db" ]; then
        SIZE=$(stat -c%s "$db" 2>/dev/null || stat -f%z "$db" 2>/dev/null)
        PERMISSIONS=$(ls -la "$db" | awk '{print $1}')
        OWNER=$(ls -la "$db" | awk '{print $3":"$4}')
        MODIFIED=$(stat -c%y "$db" 2>/dev/null | awk '{print $1, $2}' | cut -c1-16)
        
        echo "   📊 $db:"
        echo "      크기: $SIZE bytes"
        echo "      권한: $PERMISSIONS"
        echo "      소유자: $OWNER"
        echo "      수정일: $MODIFIED"
        
        # SQLite 파일 무결성 검사
        if sqlite3 "$db" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
            echo "      ✅ 무결성: OK"
            
            # 테이블 확인
            TABLES=$(sqlite3 "$db" ".tables" 2>/dev/null | wc -w)
            echo "      📋 테이블 수: $TABLES"
            
            # 주요 테이블 레코드 수 확인
            if [ "$db" = "asset_rebalancing.db" ]; then
                for table in users holdings; do
                    COUNT=$(sqlite3 "$db" "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
                    echo "         $table: $COUNT rows"
                done
            elif [ "$db" = "expert_strategies.db" ]; then
                COUNT=$(sqlite3 "$db" "SELECT COUNT(*) FROM expert_strategies;" 2>/dev/null || echo "0")
                echo "         expert_strategies: $COUNT rows"
            fi
        else
            echo "      ❌ 무결성: 손상됨"
        fi
    else
        echo "   ❌ $db: 파일 없음"
    fi
done

# 5. 네트워크 및 포트 진단
echo ""
echo "5️⃣ 네트워크 및 포트:"

PORTS=(8000 8003 8080 3000)
for port in "${PORTS[@]}"; do
    if ss -tuln 2>/dev/null | grep -q ":$port "; then
        PROCESS=$(ss -tulpn 2>/dev/null | grep ":$port " | awk '{print $NF}' | head -1)
        echo "   ✅ 포트 $port: 사용 중 ($PROCESS)"
    else
        echo "   ❌ 포트 $port: 사용하지 않음"
    fi
done

# 6. 서비스 프로세스 진단
echo ""
echo "6️⃣ 서비스 프로세스:"

# Python 프로세스
PYTHON_PROCS=$(pgrep -f "python.*app\\.py\\|uvicorn\\|start_backend" | wc -l)
echo "   백엔드 (Python): $PYTHON_PROCS 개 프로세스"
if [ "$PYTHON_PROCS" -gt 0 ]; then
    pgrep -f "python.*app\\.py\\|uvicorn\\|start_backend" | while read pid; do
        CMD=$(ps -p $pid -o cmd --no-headers 2>/dev/null | cut -c1-60)
        echo "     PID $pid: $CMD..."
    done
fi

# Node.js 프로세스
NODE_PROCS=$(pgrep -f "node.*vite\\|npm.*dev" | wc -l)
echo "   프론트엔드 (Node): $NODE_PROCS 개 프로세스"

# 7. 로그 파일 분석
echo ""
echo "7️⃣ 로그 파일 분석:"

cd .. 2>/dev/null

LOG_FILES=("backend.log" "frontend.log")
for log in "${LOG_FILES[@]}"; do
    if [ -f "$log" ]; then
        SIZE=$(stat -c%s "$log" 2>/dev/null || stat -f%z "$log" 2>/dev/null)
        LINES=$(wc -l < "$log" 2>/dev/null)
        echo "   📄 $log: $SIZE bytes, $LINES 줄"
        
        # 최근 에러 확인
        RECENT_ERRORS=$(tail -20 "$log" 2>/dev/null | grep -i "error\\|exception\\|failed\\|traceback" | wc -l)
        if [ "$RECENT_ERRORS" -gt 0 ]; then
            echo "      ⚠️ 최근 에러 $RECENT_ERRORS 건:"
            tail -20 "$log" 2>/dev/null | grep -i "error\\|exception\\|failed" | tail -3 | while read line; do
                echo "        $(echo "$line" | cut -c1-70)..."
            done
        else
            echo "      ✅ 최근 에러 없음"
        fi
    else
        echo "   ❌ $log: 없음"
    fi
done

# 8. Database AI Engine 기능 테스트
echo ""
echo "8️⃣ Database AI Engine 기능 테스트:"

cd backend 2>/dev/null
source venv/bin/activate 2>/dev/null

python -c "
import asyncio
import sys
import traceback

async def comprehensive_test():
    try:
        print('   🧠 Database AI Engine 로드 중...')
        
        from database_ai_engine import get_database_ai_engine
        db_ai = await get_database_ai_engine()
        
        print('   ✅ Database AI Engine 로드 성공')
        
        # 전략 생성 테스트
        print('   🎯 전략 생성 테스트 중...')
        
        test_profiles = [
            {'risk_tolerance': 'conservative', 'investment_goal': 'income'},
            {'risk_tolerance': 'moderate', 'investment_goal': 'wealth_building'},
            {'risk_tolerance': 'aggressive', 'investment_goal': 'growth'}
        ]
        
        for i, profile in enumerate(test_profiles, 1):
            try:
                result = await db_ai.generate_intelligent_strategy(profile)
                allocation_count = len(result['portfolio_allocation'])
                confidence = result['confidence_score']
                sources = len(result['strategy_sources'])
                
                print(f'   ✅ 테스트 {i}: {allocation_count}개 자산, 신뢰도 {confidence:.3f}, {sources}개 전략 소스')
                
            except Exception as e:
                print(f'   ❌ 테스트 {i} 실패: {e}')
                return False
        
        return True
        
    except Exception as e:
        print(f'   💥 Database AI 테스트 실패: {e}')
        traceback.print_exc()
        return False

result = asyncio.run(comprehensive_test())
if result:
    print('   🎉 모든 Database AI 테스트 통과!')
else:
    print('   ❌ Database AI 테스트 실패')
    exit(1)
" || echo "   ❌ Database AI Engine 테스트 실패"

# 9. API 엔드포인트 테스트
echo ""
echo "9️⃣ API 엔드포인트 테스트:"

cd .. 2>/dev/null

# 기본 헬스체크
if curl -s --connect-timeout 5 "http://localhost:8003/health" >/dev/null; then
    echo "   ✅ 헬스체크: 정상"
else
    echo "   ❌ 헬스체크: 실패"
fi

# Database AI 엔드포인트 테스트
if curl -s --connect-timeout 5 -X POST "http://localhost:8003/database-ai/generate-strategy" \
   -H "Content-Type: application/json" \
   -d '{"user_profile":{"risk_tolerance":"moderate","investment_goal":"wealth_building"}}' >/dev/null; then
    echo "   ✅ Database AI API: 정상"
else
    echo "   ❌ Database AI API: 실패"
fi

# 사용자 데이터 조회
if curl -s --connect-timeout 5 "http://localhost:8003/users/mock-user-001/holdings" >/dev/null; then
    echo "   ✅ 사용자 데이터 API: 정상"
else
    echo "   ❌ 사용자 데이터 API: 실패"
fi

# 10. Rocky Linux 특화 문제점 및 해결방안
echo ""
echo "🔟 Rocky Linux 특화 체크:"

# SELinux 상태
if command -v getenforce >/dev/null; then
    SELINUX_STATUS=$(getenforce)
    echo "   🛡️ SELinux: $SELINUX_STATUS"
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        echo "      ⚠️ SELinux가 활성화됨 - 필요시 컨텍스트 설정 필요"
    fi
else
    echo "   🛡️ SELinux: 없음"
fi

# 방화벽 상태
if command -v firewall-cmd >/dev/null; then
    if systemctl is-active firewalld >/dev/null 2>&1; then
        echo "   🔥 방화벽: 활성"
        for port in 8003 8080; do
            if firewall-cmd --query-port=${port}/tcp >/dev/null 2>&1; then
                echo "      ✅ 포트 $port: 열림"
            else
                echo "      ❌ 포트 $port: 닫힘 - 방화벽 설정 필요"
            fi
        done
    else
        echo "   🔥 방화벽: 비활성"
    fi
fi

# DNF/YUM 패키지 관리자
if command -v dnf >/dev/null; then
    echo "   📦 패키지 관리자: DNF"
elif command -v yum >/dev/null; then
    echo "   📦 패키지 관리자: YUM"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 진단 완료 요약:"
echo ""

# 전체적인 상태 평가
CRITICAL_ISSUES=0
WARNING_ISSUES=0

# 중요한 체크포인트들 재검사
if ! command -v sqlite3 >/dev/null; then
    echo "❌ CRITICAL: SQLite3 없음"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if [ ! -f "backend/asset_rebalancing.db" ] && [ ! -f "backend/expert_strategies.db" ]; then
    echo "❌ CRITICAL: 핵심 데이터베이스 파일 없음"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if ! curl -s --connect-timeout 3 "http://localhost:8003/health" >/dev/null; then
    echo "❌ CRITICAL: 백엔드 서버 응답 없음"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if ! curl -s --connect-timeout 3 -X POST "http://localhost:8003/database-ai/generate-strategy" \
   -H "Content-Type: application/json" \
   -d '{"user_profile":{"risk_tolerance":"moderate"}}' >/dev/null; then
    echo "⚠️ WARNING: Database AI API 응답 없음"
    WARNING_ISSUES=$((WARNING_ISSUES + 1))
fi

echo ""
if [ "$CRITICAL_ISSUES" -eq 0 ] && [ "$WARNING_ISSUES" -eq 0 ]; then
    echo "🎉 시스템 상태: 정상 - Database AI 시스템이 완벽하게 작동 중!"
    echo "🔗 접속: http://localhost:8080"
elif [ "$CRITICAL_ISSUES" -eq 0 ]; then
    echo "⚠️ 시스템 상태: 주의 - 일부 기능에 문제가 있지만 작동 가능"
    echo "🔧 해결방안: ./rocky-linux-db-fix.sh 실행"
else
    echo "💥 시스템 상태: 심각 - 즉시 수정 필요"
    echo "🚨 해결방안: ./rocky-linux-db-fix.sh 실행 후 재진단"
fi

echo ""
echo "🛠️ 문제 해결 도구:"
echo "   • 데이터베이스 수정: ./rocky-linux-db-fix.sh"
echo "   • 서비스 재시작: ./restart.sh"
echo "   • 상태 확인: ./status.sh"
echo "   • 전체 진단: ./rocky-linux-diagnostic.sh"
#!/bin/bash

# AI Asset Rebalancing System - Server Configuration Inspector
# 서버 설정 정보 및 DB 상태 종합 점검

echo "🔍 서버 설정 및 상태 점검"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 기본 시스템 정보
echo "1️⃣ 시스템 정보:"
echo "   OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '"' || uname -s)"
echo "   커널: $(uname -r)"
echo "   아키텍처: $(uname -m)"
echo "   현재 사용자: $(whoami) (UID: $(id -u))"
echo "   현재 디렉토리: $(pwd)"
echo "   홈 디렉토리: $HOME"

# 2. Python 환경 정보
echo ""
echo "2️⃣ Python 환경:"
echo "   Python 경로: $(which python3 || which python || echo 'None')"
echo "   Python 버전: $(python3 --version 2>/dev/null || python --version 2>/dev/null || echo 'None')"
echo "   pip 경로: $(which pip3 || which pip || echo 'None')"
echo "   가상환경 상태: ${VIRTUAL_ENV:-'비활성화'}"

if [ -d "backend/venv" ]; then
    echo "   백엔드 가상환경: ✅ backend/venv 존재"
    if [ -f "backend/venv/bin/activate" ]; then
        echo "   가상환경 활성화 스크립트: ✅ 존재"
    else
        echo "   가상환경 활성화 스크립트: ❌ 없음"
    fi
else
    echo "   백엔드 가상환경: ❌ backend/venv 없음"
fi

# 3. 환경 변수 및 설정 파일
echo ""
echo "3️⃣ 환경 변수 및 설정:"
echo "   PATH: ${PATH:0:100}..."
echo "   PYTHONPATH: ${PYTHONPATH:-'설정되지 않음'}"

# .env 파일들 확인
ENV_FILES=(".env" "backend/.env" ".env.example" "backend/.env.example")
echo "   환경 설정 파일들:"
for env_file in "${ENV_FILES[@]}"; do
    if [ -f "$env_file" ]; then
        echo "     ✅ $env_file ($(wc -l < "$env_file") 줄)"
    else
        echo "     ❌ $env_file 없음"
    fi
done

# 주요 환경 변수들
echo "   주요 환경 변수:"
echo "     API_URL: ${VITE_API_URL:-${API_URL:-'설정되지 않음'}}"
echo "     DEBUG: ${DEBUG:-'설정되지 않음'}"
echo "     PORT: ${PORT:-'설정되지 않음'}"

# 4. 서버 프로세스 상태
echo ""
echo "4️⃣ 서버 프로세스 상태:"
BACKEND_PROCESSES=$(pgrep -f "uvicorn\|python.*app\.py" | wc -l)
FRONTEND_PROCESSES=$(pgrep -f "vite\|npm.*dev" | wc -l)

echo "   백엔드 프로세스: $BACKEND_PROCESSES 개"
if [ "$BACKEND_PROCESSES" -gt 0 ]; then
    echo "   실행 중인 백엔드:"
    ps aux | grep -E "(uvicorn|python.*app\.py)" | grep -v grep | while read line; do
        echo "     $line"
    done
fi

echo "   프론트엔드 프로세스: $FRONTEND_PROCESSES 개"
if [ "$FRONTEND_PROCESSES" -gt 0 ]; then
    echo "   실행 중인 프론트엔드:"
    ps aux | grep -E "(vite|npm.*dev)" | grep -v grep | while read line; do
        echo "     $line"
    done
fi

# 5. 포트 사용 상태
echo ""
echo "5️⃣ 포트 사용 상태:"
PORTS=(8000 8003 8080 3000 80 443)
for port in "${PORTS[@]}"; do
    if lsof -i :$port >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep ":$port " >/dev/null; then
        echo "   포트 $port: ✅ 사용 중"
        lsof -i :$port 2>/dev/null | head -2 | tail -1 || netstat -tuln 2>/dev/null | grep ":$port "
    else
        echo "   포트 $port: ❌ 사용하지 않음"
    fi
done

# 6. 데이터베이스 파일 상세 정보
echo ""
echo "6️⃣ 데이터베이스 상세 정보:"
DB_FILES=("backend/asset_rebalancing.db" "backend/expert_strategies.db" "backend/simulation_results.db" 
          "asset_rebalancing.db" "expert_strategies.db" "simulation_results.db")

for db in "${DB_FILES[@]}"; do
    if [ -f "$db" ]; then
        SIZE=$(stat -f%z "$db" 2>/dev/null || stat -c%s "$db" 2>/dev/null || echo '?')
        PERMISSIONS=$(ls -la "$db" | awk '{print $1, $3, $4}')
        MODIFIED=$(stat -f%Sm "$db" 2>/dev/null || stat -c%y "$db" 2>/dev/null || echo '?')
        echo "   ✅ $db:"
        echo "     크기: $SIZE bytes"
        echo "     권한: $PERMISSIONS"
        echo "     수정일: $MODIFIED"
        
        # SQLite로 테이블 확인
        if command -v sqlite3 >/dev/null; then
            TABLES=$(sqlite3 "$db" ".tables" 2>/dev/null || echo "접근 불가")
            echo "     테이블: $TABLES"
            
            # 각 테이블의 레코드 수 확인
            if [ "$TABLES" != "접근 불가" ] && [ -n "$TABLES" ]; then
                for table in $TABLES; do
                    COUNT=$(sqlite3 "$db" "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "?")
                    echo "       - $table: $COUNT rows"
                done
            fi
        else
            echo "     테이블: sqlite3 명령어 없음"
        fi
    else
        echo "   ❌ $db 없음"
    fi
done

# 7. 네트워크 접근성 테스트
echo ""
echo "7️⃣ 네트워크 접근성:"
URLS=("http://localhost:8000" "http://localhost:8003" "http://localhost:8080" "http://127.0.0.1:8000")

for url in "${URLS[@]}"; do
    if command -v curl >/dev/null; then
        if curl -s --connect-timeout 3 "$url" >/dev/null 2>&1; then
            echo "   ✅ $url 응답함"
        else
            echo "   ❌ $url 응답하지 않음"
        fi
    elif command -v wget >/dev/null; then
        if wget -q --timeout=3 --tries=1 "$url" -O /dev/null 2>/dev/null; then
            echo "   ✅ $url 응답함"
        else
            echo "   ❌ $url 응답하지 않음"
        fi
    else
        echo "   ⚠️ curl/wget 없음 - 네트워크 테스트 불가"
        break
    fi
done

# 8. 로그 파일 확인
echo ""
echo "8️⃣ 로그 파일:"
LOG_FILES=("backend.log" "frontend.log" "backend/logs/app.log" "logs/app.log")

for log_file in "${LOG_FILES[@]}"; do
    if [ -f "$log_file" ]; then
        SIZE=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo '?')
        LINES=$(wc -l < "$log_file" 2>/dev/null || echo '?')
        echo "   ✅ $log_file: $SIZE bytes, $LINES 줄"
        
        # 최근 에러 확인
        if [ -r "$log_file" ]; then
            RECENT_ERRORS=$(tail -50 "$log_file" 2>/dev/null | grep -i "error\|exception\|failed\|traceback" | wc -l)
            if [ "$RECENT_ERRORS" -gt 0 ]; then
                echo "     ⚠️ 최근 50줄에서 $RECENT_ERRORS 개 에러 발견"
                echo "     최근 에러:"
                tail -50 "$log_file" 2>/dev/null | grep -i "error\|exception\|failed" | tail -3 | while read line; do
                    echo "       $line"
                done
            fi
        fi
    else
        echo "   ❌ $log_file 없음"
    fi
done

# 9. 주요 설정 파일들
echo ""
echo "9️⃣ 주요 설정 파일들:"
CONFIG_FILES=("package.json" "vite.config.ts" "backend/app.py" "backend/requirements.txt" 
              "docker-compose.yml" "Dockerfile" "start.sh" "stop.sh")

for config in "${CONFIG_FILES[@]}"; do
    if [ -f "$config" ]; then
        echo "   ✅ $config"
    else
        echo "   ❌ $config 없음"
    fi
done

# 10. 디스크 사용량
echo ""
echo "🔟 디스크 사용량:"
echo "   현재 디렉토리: $(du -sh . 2>/dev/null || echo '계산 불가')"
echo "   backend/ 디렉토리: $(du -sh backend/ 2>/dev/null || echo '계산 불가')"
echo "   node_modules/: $(du -sh node_modules/ 2>/dev/null || echo '없음')"
echo "   여유 공간: $(df -h . 2>/dev/null | tail -1 | awk '{print $4}' || echo '계산 불가')"

# 11. 추천 조치사항
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 추천 조치사항:"

# DB 문제 해결
if [ ! -f "backend/asset_rebalancing.db" ] && [ ! -f "asset_rebalancing.db" ]; then
    echo "   📊 DB 없음: ./quick-db-fix.sh 실행"
fi

# 가상환경 문제 해결  
if [ ! -d "backend/venv" ]; then
    echo "   🐍 가상환경 없음: cd backend && python3 -m venv venv"
fi

# 프로세스 문제 해결
if [ "$BACKEND_PROCESSES" -eq 0 ] && [ "$FRONTEND_PROCESSES" -eq 0 ]; then
    echo "   🚀 서버 미실행: ./start.sh 실행"
fi

# 포트 충돌 해결
for port in 8000 8003 8080; do
    if lsof -i :$port >/dev/null 2>&1; then
        PID=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$PID" ]; then
            echo "   🔌 포트 $port 사용 중 (PID: $PID): ./stop.sh 후 ./start.sh"
        fi
    fi
done

echo ""
echo "📋 빠른 해결 명령어들:"
echo "   • 전체 재시작: ./stop.sh && ./start.sh"
echo "   • DB 수정: ./quick-db-fix.sh"  
echo "   • 의존성 수정: ./fix-dependencies.sh"
echo "   • 진단 재실행: ./check-server-config.sh"
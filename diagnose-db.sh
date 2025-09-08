#!/bin/bash

# AI Asset Rebalancing System - Database Diagnosis
# 로컬에서는 작동하지만 Rocky Linux 서버에서 DB 조회 실패 문제 진단

echo "🔍 데이터베이스 진단 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 현재 작업 디렉토리 확인
echo "1️⃣ 작업 디렉토리 확인:"
echo "   현재 디렉토리: $(pwd)"
echo "   백엔드 디렉토리 존재: $([ -d backend ] && echo 'YES' || echo 'NO')"

# 2. 데이터베이스 파일 존재 확인
echo ""
echo "2️⃣ 데이터베이스 파일 확인:"
for db in "asset_rebalancing.db" "expert_strategies.db" "simulation_results.db"; do
    if [ -f "backend/$db" ]; then
        echo "   ✅ backend/$db ($(stat -f%z backend/$db 2>/dev/null || stat -c%s backend/$db 2>/dev/null || echo '?') bytes)"
    elif [ -f "$db" ]; then
        echo "   ✅ $db ($(stat -f%z $db 2>/dev/null || stat -c%s $db 2>/dev/null || echo '?') bytes)"
    else
        echo "   ❌ $db 없음"
    fi
done

# 3. 파일 권한 확인
echo ""
echo "3️⃣ 파일 권한 확인:"
for db in backend/*.db *.db; do
    if [ -f "$db" ]; then
        echo "   $db: $(ls -la $db | awk '{print $1, $3, $4}')"
    fi
done 2>/dev/null

# 4. 현재 사용자 확인
echo ""
echo "4️⃣ 실행 환경 확인:"
echo "   현재 사용자: $(whoami)"
echo "   사용자 ID: $(id -u)"
echo "   그룹 ID: $(id -g)"

# 5. 백엔드 프로세스 확인
echo ""
echo "5️⃣ 백엔드 프로세스 확인:"
if pgrep -f "uvicorn\|python.*app\.py" >/dev/null; then
    echo "   ✅ 백엔드 프로세스 실행 중"
    echo "   프로세스 정보:"
    ps aux | grep -E "(uvicorn|python.*app\.py)" | grep -v grep | while read line; do
        echo "     $line"
    done
else
    echo "   ❌ 백엔드 프로세스 없음"
fi

# 6. 데이터베이스 접근 테스트
echo ""
echo "6️⃣ 데이터베이스 접근 테스트:"

# Python을 통한 데이터베이스 접근 테스트
cat > /tmp/db_test.py << 'EOF'
import sys
import sqlite3
import os
from pathlib import Path

# 데이터베이스 경로들 시도
db_paths = [
    "asset_rebalancing.db",
    "backend/asset_rebalancing.db", 
    "./asset_rebalancing.db",
    "./backend/asset_rebalancing.db"
]

print("🔍 데이터베이스 접근 테스트:")
for db_path in db_paths:
    try:
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            print(f"   ✅ {db_path}: {len(tables)} 테이블 발견")
            
            # 테이블 내용 확인
            if tables:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                for table in tables[:3]:  # 첫 3개 테이블만 확인
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                        count = cursor.fetchone()[0]
                        print(f"     - {table[0]}: {count} rows")
                    except Exception as e:
                        print(f"     - {table[0]}: 쿼리 실패 ({e})")
                conn.close()
        else:
            print(f"   ❌ {db_path}: 파일 없음")
    except Exception as e:
        print(f"   ❌ {db_path}: 접근 실패 ({e})")

print()
print("🔍 aiosqlite 테스트:")
try:
    import aiosqlite
    print("   ✅ aiosqlite 모듈 로드 성공")
except ImportError as e:
    print(f"   ❌ aiosqlite 모듈 로드 실패: {e}")
    
# 작업 디렉토리의 모든 .db 파일 찾기
print()
print("🔍 모든 .db 파일 검색:")
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.db'):
            full_path = os.path.join(root, file)
            size = os.path.getsize(full_path)
            print(f"   📁 {full_path}: {size} bytes")
EOF

python3 /tmp/db_test.py 2>/dev/null || python /tmp/db_test.py 2>/dev/null || echo "   ❌ Python DB 테스트 실패"

# 7. 환경 변수 확인
echo ""
echo "7️⃣ 환경 변수 확인:"
echo "   PYTHONPATH: ${PYTHONPATH:-'없음'}"
echo "   PWD: $PWD"
echo "   HOME: $HOME"

# 8. 권한 문제 해결 제안
echo ""
echo "8️⃣ 권한 문제 해결 제안:"
echo "   chmod 644 backend/*.db     # 읽기 권한 부여"
echo "   chown \$(whoami) backend/*.db  # 소유권 변경"

# 정리
rm -f /tmp/db_test.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 데이터베이스 진단 완료!"
echo ""
echo "💡 일반적인 해결 방법:"
echo "   1. 데이터베이스 재초기화: ./init-db.sh"  
echo "   2. 권한 수정: chmod 644 backend/*.db"
echo "   3. 의존성 재설치: ./fix-dependencies.sh"
echo "   4. 서버 재시작: ./restart.sh"
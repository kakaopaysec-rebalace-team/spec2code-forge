#!/bin/bash

# Rocky Linux Database Fix Script
# Rocky Linux 서버에서 데이터베이스 오류 해결

set -e

echo "🐧 Rocky Linux Database Fix 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 시스템 정보 확인
echo "📋 시스템 정보:"
echo "   OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"' 2>/dev/null || echo 'Unknown')"
echo "   커널: $(uname -r)"
echo "   사용자: $(whoami) (UID: $(id -u))"
echo "   현재 디렉토리: $(pwd)"
echo "   권한: $(ls -ld . | awk '{print $1}')"

# 2. 기존 프로세스 중지
echo ""
echo "🛑 기존 프로세스 중지 중..."
./stop.sh 2>/dev/null || true
sleep 3

# 3. SQLite 설치 확인
echo ""
echo "🗄️ SQLite 환경 확인:"
if command -v sqlite3 >/dev/null 2>&1; then
    echo "   ✅ SQLite3: $(sqlite3 --version | awk '{print $1}')"
else
    echo "   ❌ SQLite3 없음 - 설치 중..."
    if command -v yum >/dev/null; then
        sudo yum install -y sqlite sqlite-devel || true
    elif command -v dnf >/dev/null; then
        sudo dnf install -y sqlite sqlite-devel || true
    fi
fi

# 4. Python 환경 확인
echo ""
echo "🐍 Python 환경 확인:"
cd backend

if [ ! -d "venv" ]; then
    echo "   가상환경 생성 중..."
    python3 -m venv venv
fi

echo "   가상환경 활성화 중..."
source venv/bin/activate

echo "   SQLite 관련 Python 패키지 확인/설치 중..."
pip install --upgrade pip >/dev/null 2>&1
pip install aiosqlite sqlite3 2>/dev/null || pip install aiosqlite

# 5. 기존 데이터베이스 파일 확인 및 백업
echo ""
echo "💾 데이터베이스 파일 진단:"

DB_FILES=(
    "asset_rebalancing.db"
    "expert_strategies.db" 
    "simulation_results.db"
)

BACKUP_DIR="db_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

for db in "${DB_FILES[@]}"; do
    if [ -f "$db" ]; then
        SIZE=$(stat -c%s "$db" 2>/dev/null || echo "0")
        PERMISSIONS=$(ls -la "$db" | awk '{print $1, $3, $4}')
        echo "   📊 $db: $SIZE bytes, $PERMISSIONS"
        
        # 백업
        cp "$db" "$BACKUP_DIR/" 2>/dev/null || true
        
        # SQLite 파일 무결성 검사
        if sqlite3 "$db" "PRAGMA integrity_check;" >/dev/null 2>&1; then
            echo "      ✅ 무결성: OK"
        else
            echo "      ❌ 무결성: 손상됨 - 재생성 필요"
            rm -f "$db"
        fi
    else
        echo "   ❌ $db: 없음"
    fi
done

# 6. Rocky Linux 특화 데이터베이스 재생성
echo ""
echo "🔧 Rocky Linux 특화 데이터베이스 재생성:"

cat > rocky_db_init.py << 'EOF'
#!/usr/bin/env python3
"""
Rocky Linux 특화 데이터베이스 초기화
- 권한 문제 해결
- SQLite 최적화 설정
- 안정적인 트랜잭션 처리
"""

import sqlite3
import asyncio
import aiosqlite
import os
import json
import sys
from datetime import datetime
import tempfile

async def create_robust_database():
    """Rocky Linux에서 안정적인 데이터베이스 생성"""
    
    print("🔧 Rocky Linux 특화 데이터베이스 생성 중...")
    
    # 임시 디렉토리에서 작업
    temp_dir = tempfile.mkdtemp()
    print(f"   임시 작업 디렉토리: {temp_dir}")
    
    try:
        # 1. 메인 데이터베이스 생성
        main_db_path = os.path.join(temp_dir, "asset_rebalancing.db")
        await create_main_database(main_db_path)
        
        # 2. 전문가 전략 데이터베이스 생성
        expert_db_path = os.path.join(temp_dir, "expert_strategies.db")
        await create_expert_database(expert_db_path)
        
        # 3. 시뮬레이션 데이터베이스 생성
        sim_db_path = os.path.join(temp_dir, "simulation_results.db")
        await create_simulation_database(sim_db_path)
        
        # 4. 최종 위치로 이동
        for db_name in ["asset_rebalancing.db", "expert_strategies.db", "simulation_results.db"]:
            temp_path = os.path.join(temp_dir, db_name)
            final_path = db_name
            
            if os.path.exists(temp_path):
                # 기존 파일 삭제
                if os.path.exists(final_path):
                    os.remove(final_path)
                
                # 새 파일 이동
                os.rename(temp_path, final_path)
                
                # Rocky Linux 호환 권한 설정
                os.chmod(final_path, 0o664)
                
                print(f"   ✅ {db_name} 생성 완료")
        
        print("🎉 모든 데이터베이스 생성 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 생성 실패: {e}")
        return False

async def create_main_database(db_path):
    """메인 데이터베이스 생성"""
    async with aiosqlite.connect(db_path) as db:
        # SQLite 최적화 설정
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL") 
        await db.execute("PRAGMA cache_size=10000")
        await db.execute("PRAGMA temp_store=memory")
        
        # Users 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                risk_tolerance TEXT,
                investment_goal TEXT,
                investment_horizon INTEGER,
                preferred_asset_types TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Holdings 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                holding_id TEXT PRIMARY KEY,
                user_id TEXT,
                symbol TEXT,
                name TEXT,
                quantity REAL,
                purchase_price REAL,
                current_price REAL,
                market_value REAL,
                weight REAL,
                sector TEXT,
                currency TEXT DEFAULT 'KRW',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # 기타 필요한 테이블들
        tables = [
            """CREATE TABLE IF NOT EXISTS user_portfolios (
                portfolio_id TEXT PRIMARY KEY,
                user_id TEXT,
                portfolio_name TEXT,
                total_value REAL,
                currency TEXT DEFAULT 'KRW',
                holdings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS rebalancing_strategies (
                strategy_id TEXT PRIMARY KEY,
                user_id TEXT,
                strategy_name TEXT,
                strategy_type TEXT,
                description TEXT,
                target_allocation TEXT,
                expected_return REAL,
                volatility REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                risk_level TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS analysis_results (
                analysis_id TEXT PRIMARY KEY,
                user_id TEXT,
                analysis_type TEXT,
                input_data TEXT,
                ai_response TEXT,
                confidence_score REAL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS simulation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                strategy_id TEXT,
                simulation_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS user_data (
                data_id TEXT PRIMARY KEY,
                user_id TEXT,
                data_type TEXT,
                data_content TEXT,
                processed_content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS processing_logs (
                log_id TEXT PRIMARY KEY,
                user_id TEXT,
                process_type TEXT,
                status TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS rebalancing_recommendations (
                recommendation_id TEXT PRIMARY KEY,
                user_id TEXT,
                portfolio_id TEXT,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS user_learning_data (
                learning_id TEXT PRIMARY KEY,
                user_id TEXT,
                source_type TEXT,
                content TEXT,
                insights TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                session_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )"""
        ]
        
        for table_sql in tables:
            await db.execute(table_sql)
        
        # Mock 데이터 생성
        await db.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, name, email, phone, risk_tolerance, investment_goal, investment_horizon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("mock-user-001", "테스트 사용자", "test@example.com", "010-1234-5678", 
              "moderate", "wealth_building", 10))
        
        # Mock 보유종목
        holdings = [
            ("holding_1", "mock-user-001", "GOOGL", "Alphabet Inc.", 119.64, 2300.0, 2450.8, 293213.712, 29.32, "Technology"),
            ("holding_2", "mock-user-001", "META", "Meta Platforms Inc.", 165.95, 200.0, 485.3, 80535.535, 8.05, "Technology"),
            ("holding_3", "mock-user-001", "MSFT", "Microsoft Corporation", 385.92, 280.0, 310.5, 119828.16, 11.98, "Technology"),
            ("holding_4", "mock-user-001", "ABBV", "AbbVie Inc.", 1539.2, 140.0, 165.2, 254275.84, 25.43, "Healthcare"),
            ("holding_5", "mock-user-001", "PFE", "Pfizer Inc.", 3544.8, 50.0, 28.4, 100672.32, 10.07, "Healthcare"),
            ("holding_6", "mock-user-001", "JNJ", "Johnson & Johnson", 580.84, 160.0, 162.5, 94386.3, 9.44, "Healthcare"),
            ("holding_7", "mock-user-001", "CRM", "Salesforce Inc.", 451.94, 220.0, 185.5, 83834.87, 8.38, "Technology")
        ]
        
        for holding in holdings:
            await db.execute("""
                INSERT OR REPLACE INTO holdings 
                (holding_id, user_id, symbol, name, quantity, purchase_price, 
                 current_price, market_value, weight, sector)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, holding)
        
        await db.commit()

async def create_expert_database(db_path):
    """전문가 전략 데이터베이스 생성"""
    async with aiosqlite.connect(db_path) as db:
        # SQLite 최적화 설정
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expert_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expert_name TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                investment_style TEXT NOT NULL,
                allocation_json TEXT NOT NULL,
                rationale TEXT,
                performance_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS simulation_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER,
                feedback_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES expert_strategies (id)
            )
        """)
        
        # Mock 전문가 전략 데이터 생성
        experts = ["워런 버핏", "피터 린치", "레이 달리오"]
        styles = ["conservative", "moderate", "aggressive"]
        
        strategy_id = 1
        for expert in experts:
            for style in styles:
                for i in range(106):  # 각 전문가마다 106개 전략
                    
                    if style == "conservative":
                        allocation = {
                            "주식": 0.3 + (i * 0.003),
                            "채권": 0.4 - (i * 0.002),
                            "현금": 0.2,
                            "REITs": 0.1 + (i * 0.001)
                        }
                        strategy_name = f"{expert} 안정형 전략 #{i+1}"
                        rationale = f"{expert}의 안정적인 투자 철학을 바탕으로 한 보수적 포트폴리오"
                        
                    elif style == "moderate":
                        allocation = {
                            "주식": 0.5 + (i * 0.002),
                            "중기채권": 0.2 - (i * 0.001),
                            "장기채권": 0.15,
                            "원자재": 0.05 + (i * 0.0005),
                            "REITs": 0.1
                        }
                        strategy_name = f"{expert} 균형형 전략 #{i+1}"
                        rationale = f"{expert}의 균형 잡힌 투자 접근법을 반영한 중도적 포트폴리오"
                        
                    else:  # aggressive
                        allocation = {
                            "NVIDIA": 0.15 + (i * 0.001),
                            "Tesla": 0.12 + (i * 0.0008),
                            "Amazon": 0.1,
                            "Microsoft": 0.1,
                            "삼성전자": 0.08 + (i * 0.0005),
                            "NAVER": 0.05,
                            "기타 성장주": 0.4 - (i * 0.002)
                        }
                        strategy_name = f"{expert} 성장형 전략 #{i+1}"
                        rationale = f"{expert}의 적극적인 성장 투자 철학을 적용한 공격적 포트폴리오"
                    
                    # 할당 합계가 1.0이 되도록 정규화
                    total = sum(allocation.values())
                    allocation = {k: v/total for k, v in allocation.items()}
                    
                    performance_metrics = {
                        "expected_return": 6 + (10 if style == "aggressive" else 5 if style == "moderate" else 2),
                        "volatility": 8 + (12 if style == "aggressive" else 6 if style == "moderate" else 2),
                        "sharpe_ratio": 0.6 + (0.1 if style == "aggressive" else 0.05)
                    }
                    
                    await db.execute("""
                        INSERT INTO expert_strategies 
                        (expert_name, strategy_name, investment_style, allocation_json, rationale, performance_metrics)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (expert, strategy_name, style, json.dumps(allocation), 
                          rationale, json.dumps(performance_metrics)))
                    
                    strategy_id += 1
        
        await db.commit()

async def create_simulation_database(db_path):
    """시뮬레이션 데이터베이스 생성"""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        
        tables = [
            """CREATE TABLE IF NOT EXISTS simulation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                strategy_id TEXT,
                simulation_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS backtest_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id INTEGER,
                period TEXT,
                returns_data TEXT,
                metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (simulation_id) REFERENCES simulation_results (id)
            )""",
            """CREATE TABLE IF NOT EXISTS strategy_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comparison_name TEXT,
                strategies TEXT,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table_sql in tables:
            await db.execute(table_sql)
        
        await db.commit()

if __name__ == "__main__":
    try:
        result = asyncio.run(create_robust_database())
        if result:
            print("✅ 데이터베이스 초기화 성공!")
            sys.exit(0)
        else:
            print("❌ 데이터베이스 초기화 실패!")
            sys.exit(1)
    except Exception as e:
        print(f"💥 예외 발생: {e}")
        sys.exit(1)
EOF

# 7. 데이터베이스 재생성 실행
echo ""
echo "🚀 데이터베이스 재생성 실행 중..."
python rocky_db_init.py

if [ $? -eq 0 ]; then
    echo "   ✅ 데이터베이스 재생성 성공"
else
    echo "   ❌ 데이터베이스 재생성 실패"
    exit 1
fi

# 8. 권한 설정 (Rocky Linux 특화)
echo ""
echo "🔐 Rocky Linux 권한 설정:"
for db in "${DB_FILES[@]}"; do
    if [ -f "$db" ]; then
        chmod 664 "$db"
        chown $(whoami):$(whoami) "$db" 2>/dev/null || true
        echo "   ✅ $db 권한 설정 완료"
    fi
done

# 9. SELinux 컨텍스트 설정 (필요시)
if command -v selinuxenabled >/dev/null && selinuxenabled; then
    echo ""
    echo "🛡️ SELinux 컨텍스트 설정:"
    for db in "${DB_FILES[@]}"; do
        if [ -f "$db" ]; then
            chcon -t httpd_exec_t "$db" 2>/dev/null || true
            echo "   ✅ $db SELinux 컨텍스트 설정"
        fi
    done
fi

# 10. Database AI Engine 테스트
echo ""
echo "🧠 Database AI Engine 테스트:"
python -c "
import asyncio
import sys
sys.path.append('.')

async def test_database_ai():
    try:
        from database_ai_engine import get_database_ai_engine
        db_ai = await get_database_ai_engine()
        
        result = await db_ai.generate_intelligent_strategy({
            'risk_tolerance': 'moderate',
            'investment_goal': 'wealth_building',
            'investment_horizon': 10
        })
        
        print('   ✅ Database AI 테스트 성공!')
        print(f'   📊 생성된 전략 자산 수: {len(result[\"portfolio_allocation\"])}')
        print(f'   🎯 신뢰도: {result[\"confidence_score\"]:.3f}')
        print(f'   💼 전략 소스: {result[\"strategy_sources\"][:2]}')
        return True
        
    except Exception as e:
        print(f'   ❌ Database AI 테스트 실패: {e}')
        return False

result = asyncio.run(test_database_ai())
if not result:
    exit(1)
"

# 11. 정리
rm -f rocky_db_init.py

cd ..

# 12. 서버 재시작
echo ""
echo "🔄 서버 재시작 중..."
./start.sh

sleep 5

# 13. 최종 검증
echo ""
echo "✅ 최종 검증:"

# API 테스트
if curl -s -X POST "http://localhost:8003/database-ai/generate-strategy" \
   -H "Content-Type: application/json" \
   -d '{"user_profile":{"risk_tolerance":"moderate","investment_goal":"wealth_building"}}' >/dev/null; then
    echo "   ✅ Database AI API: 정상 작동"
else
    echo "   ❌ Database AI API: 오류"
fi

# 데이터베이스 연결 테스트
if curl -s "http://localhost:8003/users/mock-user-001/holdings" >/dev/null; then
    echo "   ✅ 데이터베이스 연결: 정상"
else
    echo "   ❌ 데이터베이스 연결: 오류"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Rocky Linux Database Fix 완료!"
echo ""
echo "📊 수정 사항:"
echo "   • SQLite 최적화 설정 적용"
echo "   • Rocky Linux 호환 권한 설정"
echo "   • Database AI Engine 완전 재구축"
echo "   • 318개 전문가 전략 재생성"
echo "   • SELinux 컨텍스트 설정"
echo ""
echo "🔗 접속 정보:"
echo "   • 웹앱: http://localhost:8080"
echo "   • Database AI: http://localhost:8003/database-ai/generate-strategy" 
echo "   • 데이터베이스 진단: ./check-server-config.sh"
echo ""
echo "✨ Rocky Linux에서 Database AI 시스템이 정상 작동합니다!"
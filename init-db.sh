#!/bin/bash

# AI Asset Rebalancing System - Database Initialization
# 데이터베이스 초기화 및 Mock 데이터 생성

set -e

echo "🗄️ 데이터베이스 초기화 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 백엔드 디렉토리로 이동
cd backend

# 2. 가상환경 활성화
if [ -f "venv/bin/activate" ]; then
    echo "🔄 가상환경 활성화..."
    source venv/bin/activate
else
    echo "❌ 가상환경을 찾을 수 없습니다. ./start.sh를 먼저 실행하세요."
    exit 1
fi

# 3. 필수 패키지 확인
echo "📦 필수 패키지 확인..."
python -c "import sqlite3, aiosqlite" 2>/dev/null || {
    echo "⚠️ aiosqlite 설치 중..."
    pip install aiosqlite
}

# 4. 기존 데이터베이스 백업 (있는 경우)
echo "💾 기존 데이터베이스 백업..."
for db in *.db; do
    if [ -f "$db" ]; then
        cp "$db" "${db}.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
        echo "   백업: $db → ${db}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
done

# 5. 데이터베이스 초기화 Python 스크립트 생성
echo "🔧 데이터베이스 초기화 스크립트 생성..."
cat > init_database.py << 'EOF'
#!/usr/bin/env python3
"""
데이터베이스 초기화 및 Mock 데이터 생성
Rocky Linux 서버에서 DB 조회 문제 해결
"""

import sqlite3
import asyncio
import aiosqlite
import os
from datetime import datetime, timedelta
import json
import random

async def init_main_database():
    """메인 데이터베이스 초기화"""
    print("📊 메인 데이터베이스 초기화 중...")
    
    db_path = "asset_rebalancing.db"
    
    async with aiosqlite.connect(db_path) as db:
        # Users 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                investment_style TEXT,
                investment_goal TEXT,
                investment_period TEXT,
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
        
        # Strategies 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id TEXT PRIMARY KEY,
                strategy_name TEXT,
                strategy_type TEXT,
                description TEXT,
                target_allocation TEXT,
                expected_return REAL,
                volatility REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                risk_level TEXT,
                tags TEXT,
                user_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
    
    print(f"   ✅ {db_path} 초기화 완료")
    return db_path

async def init_expert_strategies_database():
    """전문가 전략 데이터베이스 초기화"""
    print("🎯 전문가 전략 데이터베이스 초기화 중...")
    
    db_path = "expert_strategies.db"
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expert_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                description TEXT,
                strategy_type TEXT,
                target_allocation TEXT,
                expected_return REAL,
                volatility REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                risk_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
    
    print(f"   ✅ {db_path} 초기화 완료")
    return db_path

async def init_simulation_database():
    """시뮬레이션 데이터베이스 초기화"""
    print("📈 시뮬레이션 데이터베이스 초기화 중...")
    
    db_path = "simulation_results.db"
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS simulation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                strategy_id TEXT,
                simulation_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
    
    print(f"   ✅ {db_path} 초기화 완료")
    return db_path

async def create_mock_data():
    """Mock 데이터 생성"""
    print("🎭 Mock 데이터 생성 중...")
    
    # 메인 데이터베이스에 Mock 사용자 및 보유종목 추가
    async with aiosqlite.connect("asset_rebalancing.db") as db:
        # Mock 사용자 추가
        user_id = "test_user_12345"
        await db.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, email, investment_style, investment_goal, investment_period)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, "test@example.com", "moderate", "growth", "long"))
        
        # Mock 보유종목 추가
        holdings = [
            ("holding_1", user_id, "005930", "삼성전자", 10, 70000, 75000, 750000, 25.0, "기술", "KRW"),
            ("holding_2", user_id, "000660", "SK하이닉스", 5, 90000, 95000, 475000, 15.83, "기술", "KRW"),
            ("holding_3", user_id, "035420", "NAVER", 3, 200000, 210000, 630000, 21.0, "인터넷", "KRW"),
            ("holding_4", user_id, "051910", "LG화학", 2, 400000, 420000, 840000, 28.0, "화학", "KRW"),
            ("holding_5", user_id, "006400", "삼성SDI", 1, 300000, 310000, 310000, 10.33, "배터리", "KRW"),
        ]
        
        for holding in holdings:
            await db.execute("""
                INSERT OR REPLACE INTO holdings 
                (holding_id, user_id, symbol, name, quantity, purchase_price, 
                 current_price, market_value, weight, sector, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, holding)
        
        await db.commit()
    
    # 전문가 전략 데이터베이스에 Mock 전략 추가
    async with aiosqlite.connect("expert_strategies.db") as db:
        strategies = [
            ("성장형 포트폴리오", "기술주 중심의 성장 지향 전략", "growth", 
             '{"기술": 40, "헬스케어": 20, "금융": 15, "소비재": 15, "기타": 10}', 
             12.5, 18.2, 15.3, 0.68, "중간"),
            ("안정형 포트폴리오", "배당주 중심의 안정성 추구 전략", "conservative",
             '{"배당주": 35, "금융": 25, "유틸리티": 20, "소비재": 15, "현금": 5}',
             8.5, 12.1, 8.7, 0.70, "낮음"),
            ("균형형 포트폴리오", "성장과 안정성의 균형", "balanced",
             '{"기술": 25, "금융": 20, "헬스케어": 15, "소비재": 20, "배당주": 15, "현금": 5}',
             10.2, 14.8, 12.1, 0.69, "중간"),
        ]
        
        for strategy in strategies:
            await db.execute("""
                INSERT OR REPLACE INTO expert_strategies 
                (strategy_name, description, strategy_type, target_allocation, 
                 expected_return, volatility, max_drawdown, sharpe_ratio, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, strategy)
        
        await db.commit()
    
    print("   ✅ Mock 데이터 생성 완료")

async def verify_data():
    """데이터 검증"""
    print("✅ 데이터 검증 중...")
    
    databases = [
        ("asset_rebalancing.db", ["users", "holdings", "strategies"]),
        ("expert_strategies.db", ["expert_strategies"]),
        ("simulation_results.db", ["simulation_results"])
    ]
    
    for db_path, tables in databases:
        if os.path.exists(db_path):
            async with aiosqlite.connect(db_path) as db:
                for table in tables:
                    try:
                        cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                        count = await cursor.fetchone()
                        print(f"   📊 {db_path} / {table}: {count[0]} rows")
                    except Exception as e:
                        print(f"   ❌ {db_path} / {table}: {e}")

async def main():
    """메인 함수"""
    print("🚀 데이터베이스 전체 초기화 시작")
    
    try:
        # 데이터베이스들 초기화
        await init_main_database()
        await init_expert_strategies_database() 
        await init_simulation_database()
        
        # Mock 데이터 생성
        await create_mock_data()
        
        # 데이터 검증
        await verify_data()
        
        print("\n🎉 데이터베이스 초기화 성공!")
        print("   - 총 3개 데이터베이스 초기화 완료")
        print("   - Mock 데이터 생성 완료") 
        print("   - 데이터 검증 완료")
        
    except Exception as e:
        print(f"\n❌ 데이터베이스 초기화 실패: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
EOF

# 6. 데이터베이스 초기화 실행
echo "🚀 데이터베이스 초기화 실행..."
python init_database.py

# 7. 파일 권한 설정
echo "🔧 파일 권한 설정..."
chmod 644 *.db 2>/dev/null || true
ls -la *.db

# 8. 정리
rm -f init_database.py

cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 데이터베이스 초기화 완료!"
echo ""
echo "📊 생성된 데이터베이스:"
echo "   • asset_rebalancing.db - 메인 데이터베이스"  
echo "   • expert_strategies.db - 전문가 전략"
echo "   • simulation_results.db - 시뮬레이션 결과"
echo ""
echo "🎭 생성된 Mock 데이터:"
echo "   • 테스트 사용자: test_user_12345"
echo "   • 보유종목: 5개 (삼성전자, SK하이닉스 등)"
echo "   • 전문가 전략: 3개 (성장형, 안정형, 균형형)"
echo ""
echo "🔄 서버 재시작 권장: ./restart.sh"
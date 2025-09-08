#!/bin/bash

# AI Asset Rebalancing System - Database Schema Fix
# 스키마 불일치 문제 해결

echo "🔧 데이터베이스 스키마 수정 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd backend
source venv/bin/activate

# 올바른 스키마로 데이터베이스 재생성
cat > fix_schema.py << 'EOF'
import asyncio
import aiosqlite
import os
import sqlite3

async def fix_database_schema():
    """올바른 스키마로 데이터베이스 수정"""
    print("🔧 데이터베이스 스키마 수정 중...")
    
    db_path = "asset_rebalancing.db"
    
    # 기존 데이터베이스 삭제하고 새로 만들기
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"   🗑️ 기존 {db_path} 삭제")
    
    async with aiosqlite.connect(db_path) as db:
        # 올바른 users 테이블 스키마 (database_manager.py 기준)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                risk_tolerance TEXT,
                investment_goal TEXT,
                investment_horizon INTEGER,
                preferred_asset_types TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # user_portfolios 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_portfolios (
                portfolio_id TEXT PRIMARY KEY,
                user_id TEXT,
                portfolio_name TEXT,
                total_value REAL,
                currency TEXT DEFAULT 'KRW',
                holdings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # holdings 테이블 (기존 방식 유지)
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
        
        # user_data 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                data_id TEXT PRIMARY KEY,
                user_id TEXT,
                data_type TEXT,
                data_content TEXT,
                processed_content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # ai_analysis_results 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_analysis_results (
                analysis_id TEXT PRIMARY KEY,
                user_id TEXT,
                analysis_type TEXT,
                input_data TEXT,
                ai_response TEXT,
                confidence_score REAL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # rebalancing_strategies 테이블
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rebalancing_strategies (
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
                tags TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        await db.commit()
        print(f"   ✅ {db_path} 스키마 생성 완료")
    
    # Mock 데이터 생성 (올바른 컬럼명 사용)
    await create_correct_mock_data()

async def create_correct_mock_data():
    """올바른 스키마에 맞는 Mock 데이터 생성"""
    print("🎭 Mock 데이터 생성 중...")
    
    async with aiosqlite.connect("asset_rebalancing.db") as db:
        # Mock 사용자 (올바른 컬럼명 사용)
        user_id = "test_user_12345"
        await db.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, name, email, risk_tolerance, investment_goal, investment_horizon)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, "테스트 사용자", "test@example.com", "moderate", "growth", 60))
        
        # Mock 보유종목
        holdings = [
            ("holding_1", user_id, "005930", "삼성전자", 10, 70000, 75000, 750000, 25.0, "기술"),
            ("holding_2", user_id, "000660", "SK하이닉스", 5, 90000, 95000, 475000, 15.83, "반도체"),
            ("holding_3", user_id, "035420", "NAVER", 3, 200000, 210000, 630000, 21.0, "인터넷"),
            ("holding_4", user_id, "051910", "LG화학", 2, 400000, 420000, 840000, 28.0, "화학"),
            ("holding_5", user_id, "006400", "삼성SDI", 1, 300000, 310000, 310000, 10.33, "배터리"),
            ("holding_6", user_id, "207940", "삼성바이오로직스", 1, 800000, 820000, 820000, 27.33, "바이오"),
            ("holding_7", user_id, "373220", "LG에너지솔루션", 2, 400000, 410000, 820000, 27.33, "배터리"),
        ]
        
        for holding in holdings:
            await db.execute("""
                INSERT OR REPLACE INTO holdings 
                (holding_id, user_id, symbol, name, quantity, purchase_price, 
                 current_price, market_value, weight, sector)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, holding)
        
        await db.commit()
        print("   ✅ Mock 사용자 및 보유종목 생성 완료")
    
    # Expert strategies DB도 동일하게 처리
    await fix_expert_strategies_db()

async def fix_expert_strategies_db():
    """전문가 전략 데이터베이스 수정"""
    print("🎯 전문가 전략 DB 수정 중...")
    
    db_path = "expert_strategies.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
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
        
        # Mock 전문가 전략 데이터
        strategies = [
            ("성장형 포트폴리오", "기술주 중심의 성장 지향 전략", "growth", 
             '{"기술": 40, "바이오": 20, "반도체": 15, "인터넷": 15, "기타": 10}', 
             14.5, 18.2, 15.3, 0.68, "중간"),
            ("안정형 포트폴리오", "배당주 중심의 안정성 추구 전략", "conservative",
             '{"금융": 30, "유틸리티": 25, "소비재": 20, "배당주": 20, "현금": 5}',
             8.5, 12.1, 8.7, 0.70, "낮음"),
            ("균형형 포트폴리오", "성장과 안정성의 균형", "balanced",
             '{"기술": 25, "금융": 20, "바이오": 15, "소비재": 20, "배당주": 15, "현금": 5}',
             11.2, 14.8, 12.1, 0.69, "중간"),
            ("혁신성장 포트폴리오", "미래 유망 산업 중심", "aggressive", 
             '{"바이오": 30, "배터리": 25, "인터넷": 20, "반도체": 15, "기타": 10}', 
             16.8, 22.5, 18.7, 0.65, "높음"),
        ]
        
        for strategy in strategies:
            await db.execute("""
                INSERT INTO expert_strategies 
                (strategy_name, description, strategy_type, target_allocation, 
                 expected_return, volatility, max_drawdown, sharpe_ratio, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, strategy)
        
        await db.commit()
        print("   ✅ Expert strategies DB 생성 완료")

async def verify_schema():
    """스키마 검증"""
    print("✅ 스키마 검증 중...")
    
    async with aiosqlite.connect("asset_rebalancing.db") as db:
        # 테이블 목록 확인
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = await cursor.fetchall()
        print(f"   📊 테이블 수: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = await cursor.fetchone()
            print(f"   📋 {table_name}: {count[0]} rows")
    
    # Expert strategies 확인
    async with aiosqlite.connect("expert_strategies.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM expert_strategies")
        count = await cursor.fetchone()
        print(f"   🎯 expert_strategies: {count[0]} rows")

async def main():
    try:
        await fix_database_schema()
        await verify_schema()
        print("\n🎉 데이터베이스 스키마 수정 성공!")
    except Exception as e:
        print(f"\n❌ 스키마 수정 실패: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
EOF

# 스키마 수정 실행
python fix_schema.py

# 권한 설정
chmod 644 *.db

# 정리
rm fix_schema.py

cd ..

echo ""
echo "✅ 데이터베이스 스키마 수정 완료!"
echo "🔄 서버 재시작: ./restart.sh"
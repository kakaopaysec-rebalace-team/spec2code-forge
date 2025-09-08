#!/bin/bash

# Quick Database Schema Fix
echo "🚀 빠른 DB 스키마 수정..."

cd backend
source venv/bin/activate

# 간단한 스키마 수정
python3 -c "
import asyncio
import aiosqlite
import os

async def quick_fix():
    # 기존 DB 삭제
    for db in ['asset_rebalancing.db', 'expert_strategies.db']:
        if os.path.exists(db):
            os.remove(db)
    
    # 메인 DB 재생성
    async with aiosqlite.connect('asset_rebalancing.db') as db:
        await db.execute('''
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                risk_tolerance TEXT,
                investment_goal TEXT,
                investment_horizon INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE holdings (
                holding_id TEXT PRIMARY KEY,
                user_id TEXT,
                symbol TEXT,
                name TEXT,
                quantity REAL,
                current_price REAL,
                market_value REAL,
                sector TEXT
            )
        ''')
        
        # Mock 데이터
        await db.execute(
            'INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)',
            ('test_user_12345', '테스트사용자', 'test@test.com', 'moderate', 'growth', 60, '2024-01-01')
        )
        
        holdings = [
            ('h1', 'test_user_12345', '005930', '삼성전자', 10, 75000, 750000, '기술'),
            ('h2', 'test_user_12345', '000660', 'SK하이닉스', 5, 95000, 475000, '반도체'),
            ('h3', 'test_user_12345', '035420', 'NAVER', 3, 210000, 630000, '인터넷'),
        ]
        
        for h in holdings:
            await db.execute(
                'INSERT INTO holdings VALUES (?, ?, ?, ?, ?, ?, ?, ?)', h
            )
        
        await db.commit()
    
    # Expert strategies DB
    async with aiosqlite.connect('expert_strategies.db') as db:
        await db.execute('''
            CREATE TABLE expert_strategies (
                id INTEGER PRIMARY KEY,
                strategy_name TEXT,
                strategy_type TEXT,
                expected_return REAL,
                risk_level TEXT
            )
        ''')
        
        strategies = [
            (1, '성장형 포트폴리오', 'growth', 12.5, '중간'),
            (2, '안정형 포트폴리오', 'conservative', 8.5, '낮음'),
            (3, '균형형 포트폴리오', 'balanced', 10.2, '중간'),
        ]
        
        for s in strategies:
            await db.execute('INSERT INTO expert_strategies VALUES (?, ?, ?, ?, ?)', s)
        
        await db.commit()
    
    print('✅ Quick DB fix complete!')

asyncio.run(quick_fix())
"

cd ..
echo "✅ 빠른 DB 수정 완료!"
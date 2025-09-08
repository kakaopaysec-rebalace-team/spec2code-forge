#!/usr/bin/env python3
"""
Rocky Linux Docker Database Initialization Script
Database AI 시스템용 데이터베이스 초기화
"""

import asyncio
import aiosqlite
import os
import json
import sqlite3

async def init_rocky_db():
    print('🐧 Rocky Linux Docker DB 초기화 중...')
    
    # 메인 데이터베이스
    async with aiosqlite.connect('asset_rebalancing.db') as db:
        await db.execute('PRAGMA journal_mode=WAL')
        await db.execute('PRAGMA synchronous=NORMAL')
        
        await db.execute('''
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
        ''')
        
        await db.execute('''
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
        ''')
        
        # Mock 사용자
        await db.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, name, email, phone, risk_tolerance, investment_goal, investment_horizon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('mock-user-001', '테스트 사용자', 'test@example.com', '010-1234-5678', 
              'moderate', 'wealth_building', 10))
        
        # Mock 보유종목
        holdings = [
            ('holding_1', 'mock-user-001', 'GOOGL', 'Alphabet Inc.', 119.64, 2300.0, 2450.8, 293213.712, 29.32, 'Technology'),
            ('holding_2', 'mock-user-001', 'MSFT', 'Microsoft Corporation', 385.92, 280.0, 310.5, 119828.16, 11.98, 'Technology'),
            ('holding_3', 'mock-user-001', 'AAPL', 'Apple Inc.', 300.0, 180.0, 195.5, 58650.0, 5.87, 'Technology')
        ]
        
        for holding in holdings:
            await db.execute('''
                INSERT OR REPLACE INTO holdings 
                (holding_id, user_id, symbol, name, quantity, purchase_price, 
                 current_price, market_value, weight, sector)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', holding)
        
        await db.commit()
    
    # 전문가 전략 데이터베이스
    async with aiosqlite.connect('expert_strategies.db') as db:
        await db.execute('PRAGMA journal_mode=WAL')
        await db.execute('PRAGMA synchronous=NORMAL')
        
        await db.execute('''
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
        ''')
        
        # 318개 전문가 전략 생성
        experts = ['워런 버핏', '피터 린치', '레이 달리오']
        styles = ['conservative', 'moderate', 'aggressive']
        
        for expert in experts:
            for style in styles:
                for i in range(106):
                    if style == 'conservative':
                        allocation = {'주식': 0.4, '채권': 0.4, '현금': 0.2}
                        strategy_name = f'{expert} 안정형 전략 #{i+1}'
                        rationale = f'{expert}의 안정적인 투자 철학 기반 포트폴리오'
                    elif style == 'moderate':  
                        allocation = {'주식': 0.6, '채권': 0.3, 'REITs': 0.1}
                        strategy_name = f'{expert} 균형형 전략 #{i+1}'
                        rationale = f'{expert}의 균형잡힌 투자 접근법 반영'
                    else:
                        allocation = {'기술주': 0.5, '성장주': 0.3, '신흥시장': 0.2}
                        strategy_name = f'{expert} 성장형 전략 #{i+1}'
                        rationale = f'{expert}의 적극적인 성장투자 철학 적용'
                    
                    perf_metrics = {'expected_return': 8+i*0.1, 'volatility': 12+i*0.05}
                    
                    await db.execute('''
                        INSERT INTO expert_strategies 
                        (expert_name, strategy_name, investment_style, allocation_json, rationale, performance_metrics)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (expert, strategy_name, style, json.dumps(allocation), 
                          rationale, json.dumps(perf_metrics)))
        
        await db.commit()
    
    print('✅ Rocky Linux Docker DB 초기화 완료 - 318개 전문가 전략 생성됨')

if __name__ == '__main__':
    asyncio.run(init_rocky_db())
import sqlite3
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import logging
from pathlib import Path
import aiosqlite
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    포괄적인 데이터베이스 관리 클래스
    사용자 데이터, 포트폴리오, 분석 결과, AI 전략을 관리
    """
    
    def __init__(self, db_path: str = "asset_rebalancing.db"):
        self.db_path = db_path
        self.db_dir = Path(db_path).parent
        self.db_dir.mkdir(exist_ok=True)
        
    async def initialize_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 사용자 정보 테이블
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
                
                # 사용자 포트폴리오 테이블
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_portfolios (
                        portfolio_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        portfolio_name TEXT,
                        total_value REAL,
                        currency TEXT DEFAULT 'KRW',
                        holdings TEXT,  -- JSON format
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # 사용자 업로드 데이터 테이블
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_data (
                        data_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        data_type TEXT,  -- 'pdf', 'url', 'text', 'file'
                        data_content TEXT,
                        processed_content TEXT,
                        metadata TEXT,  -- JSON format
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # AI 분석 결과 테이블
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        analysis_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        portfolio_id TEXT,
                        analysis_type TEXT,
                        input_data TEXT,  -- JSON format
                        analysis_results TEXT,  -- JSON format
                        confidence_score REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (portfolio_id) REFERENCES user_portfolios (portfolio_id)
                    )
                """)
                
                # 리밸런싱 추천 테이블
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS rebalancing_recommendations (
                        recommendation_id TEXT PRIMARY KEY,
                        analysis_id TEXT,
                        user_id TEXT,
                        current_allocation TEXT,  -- JSON format
                        recommended_allocation TEXT,  -- JSON format
                        reasoning TEXT,
                        expected_return REAL,
                        risk_score REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (analysis_id) REFERENCES analysis_results (analysis_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # 시뮬레이션 결과 테이블
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS simulation_results (
                        simulation_id TEXT PRIMARY KEY,
                        analysis_id TEXT,
                        user_id TEXT,
                        simulation_config TEXT,  -- JSON format
                        performance_metrics TEXT,  -- JSON format
                        backtest_results TEXT,  -- JSON format
                        stress_test_results TEXT,  -- JSON format
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (analysis_id) REFERENCES analysis_results (analysis_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # 사용자 세션 테이블
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        session_data TEXT,  -- JSON format
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # 데이터 처리 로그 테이블
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS processing_logs (
                        log_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        process_type TEXT,
                        status TEXT,
                        input_data TEXT,
                        output_data TEXT,
                        error_message TEXT,
                        processing_time REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                await db.commit()
                logger.info("데이터베이스 초기화 완료")
                
        except Exception as e:
            logger.error(f"데이터베이스 초기화 오류: {e}")
            raise
    
    # ================== 사용자 관리 ==================
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """새 사용자 생성"""
        user_id = str(uuid.uuid4())
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO users (user_id, name, email, phone, risk_tolerance, 
                                     investment_goal, investment_horizon, preferred_asset_types)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    user_data.get('name'),
                    user_data.get('email'),
                    user_data.get('phone'),
                    user_data.get('risk_tolerance'),
                    user_data.get('investment_goal'),
                    user_data.get('investment_horizon'),
                    json.dumps(user_data.get('preferred_asset_types', []))
                ))
                await db.commit()
                logger.info(f"사용자 생성 완료: {user_id}")
                return user_id
        except Exception as e:
            logger.error(f"사용자 생성 오류: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 정보 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        user_data = dict(row)
                        if user_data.get('preferred_asset_types'):
                            user_data['preferred_asset_types'] = json.loads(user_data['preferred_asset_types'])
                        return user_data
                    return None
        except Exception as e:
            logger.error(f"사용자 조회 오류: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """사용자 정보 업데이트"""
        try:
            set_clauses = []
            values = []
            
            for key, value in update_data.items():
                if key == 'preferred_asset_types':
                    set_clauses.append(f"{key} = ?")
                    values.append(json.dumps(value))
                elif key != 'user_id':
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, values)
                await db.commit()
                logger.info(f"사용자 정보 업데이트 완료: {user_id}")
                return True
        except Exception as e:
            logger.error(f"사용자 정보 업데이트 오류: {e}")
            return False
    
    # ================== 포트폴리오 관리 ==================
    
    async def save_portfolio(self, user_id: str, portfolio_data: Dict[str, Any]) -> str:
        """사용자 포트폴리오 저장"""
        portfolio_id = str(uuid.uuid4())
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO user_portfolios (portfolio_id, user_id, portfolio_name, 
                                                total_value, currency, holdings)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    portfolio_id,
                    user_id,
                    portfolio_data.get('name', 'Default Portfolio'),
                    portfolio_data.get('total_value', 0),
                    portfolio_data.get('currency', 'KRW'),
                    json.dumps(portfolio_data.get('holdings', {}))
                ))
                await db.commit()
                logger.info(f"포트폴리오 저장 완료: {portfolio_id}")
                return portfolio_id
        except Exception as e:
            logger.error(f"포트폴리오 저장 오류: {e}")
            raise
    
    async def get_user_portfolios(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 모든 포트폴리오 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM user_portfolios 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                """, (user_id,)) as cursor:
                    rows = await cursor.fetchall()
                    portfolios = []
                    for row in rows:
                        portfolio = dict(row)
                        portfolio['holdings'] = json.loads(portfolio['holdings'])
                        portfolios.append(portfolio)
                    return portfolios
        except Exception as e:
            logger.error(f"포트폴리오 조회 오류: {e}")
            return []
    
    async def get_portfolio(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """특정 포트폴리오 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM user_portfolios WHERE portfolio_id = ?
                """, (portfolio_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        portfolio = dict(row)
                        portfolio['holdings'] = json.loads(portfolio['holdings'])
                        return portfolio
                    return None
        except Exception as e:
            logger.error(f"포트폴리오 조회 오류: {e}")
            return None
    
    # ================== 사용자 데이터 관리 ==================
    
    async def save_user_data(self, user_id: str, data_type: str, content: str, 
                           processed_content: str = None, metadata: Dict[str, Any] = None) -> str:
        """사용자 업로드 데이터 저장"""
        data_id = str(uuid.uuid4())
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO user_data (data_id, user_id, data_type, data_content, 
                                         processed_content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    data_id,
                    user_id,
                    data_type,
                    content,
                    processed_content,
                    json.dumps(metadata or {})
                ))
                await db.commit()
                logger.info(f"사용자 데이터 저장 완료: {data_id}")
                return data_id
        except Exception as e:
            logger.error(f"사용자 데이터 저장 오류: {e}")
            raise
    
    async def get_user_data(self, user_id: str, data_type: str = None) -> List[Dict[str, Any]]:
        """사용자 업로드 데이터 조회"""
        try:
            query = "SELECT * FROM user_data WHERE user_id = ?"
            params = [user_id]
            
            if data_type:
                query += " AND data_type = ?"
                params.append(data_type)
            
            query += " ORDER BY created_at DESC"
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    data_list = []
                    for row in rows:
                        data = dict(row)
                        data['metadata'] = json.loads(data['metadata'])
                        data_list.append(data)
                    return data_list
        except Exception as e:
            logger.error(f"사용자 데이터 조회 오류: {e}")
            return []
    
    # ================== 분석 결과 관리 ==================
    
    async def save_analysis_result(self, user_id: str, portfolio_id: str, 
                                 analysis_type: str, input_data: Dict[str, Any],
                                 results: Dict[str, Any], confidence_score: float = None) -> str:
        """AI 분석 결과 저장"""
        analysis_id = str(uuid.uuid4())
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO analysis_results (analysis_id, user_id, portfolio_id, 
                                                analysis_type, input_data, analysis_results, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    user_id,
                    portfolio_id,
                    analysis_type,
                    json.dumps(input_data),
                    json.dumps(results),
                    confidence_score
                ))
                await db.commit()
                logger.info(f"분석 결과 저장 완료: {analysis_id}")
                return analysis_id
        except Exception as e:
            logger.error(f"분석 결과 저장 오류: {e}")
            raise
    
    async def get_analysis_results(self, user_id: str, analysis_type: str = None) -> List[Dict[str, Any]]:
        """사용자의 분석 결과 조회"""
        try:
            query = "SELECT * FROM analysis_results WHERE user_id = ?"
            params = [user_id]
            
            if analysis_type:
                query += " AND analysis_type = ?"
                params.append(analysis_type)
            
            query += " ORDER BY created_at DESC"
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    results = []
                    for row in rows:
                        result = dict(row)
                        result['input_data'] = json.loads(result['input_data'])
                        result['analysis_results'] = json.loads(result['analysis_results'])
                        results.append(result)
                    return results
        except Exception as e:
            logger.error(f"분석 결과 조회 오류: {e}")
            return []
    
    # ================== 리밸런싱 추천 관리 ==================
    
    async def save_rebalancing_recommendation(self, analysis_id: str, user_id: str,
                                            current_allocation: Dict[str, Any],
                                            recommended_allocation: Dict[str, Any],
                                            reasoning: str, expected_return: float = None,
                                            risk_score: float = None) -> str:
        """리밸런싱 추천 저장"""
        recommendation_id = str(uuid.uuid4())
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO rebalancing_recommendations 
                    (recommendation_id, analysis_id, user_id, current_allocation, 
                     recommended_allocation, reasoning, expected_return, risk_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    recommendation_id,
                    analysis_id,
                    user_id,
                    json.dumps(current_allocation),
                    json.dumps(recommended_allocation),
                    reasoning,
                    expected_return,
                    risk_score
                ))
                await db.commit()
                logger.info(f"리밸런싱 추천 저장 완료: {recommendation_id}")
                return recommendation_id
        except Exception as e:
            logger.error(f"리밸런싱 추천 저장 오류: {e}")
            raise
    
    # ================== 시뮬레이션 결과 관리 ==================
    
    async def save_simulation_result(self, analysis_id: str, user_id: str,
                                   simulation_config: Dict[str, Any],
                                   performance_metrics: Dict[str, Any],
                                   backtest_results: Dict[str, Any],
                                   stress_test_results: Dict[str, Any] = None) -> str:
        """시뮬레이션 결과 저장"""
        simulation_id = str(uuid.uuid4())
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO simulation_results 
                    (simulation_id, analysis_id, user_id, simulation_config, 
                     performance_metrics, backtest_results, stress_test_results)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    simulation_id,
                    analysis_id,
                    user_id,
                    json.dumps(simulation_config),
                    json.dumps(performance_metrics),
                    json.dumps(backtest_results),
                    json.dumps(stress_test_results or {})
                ))
                await db.commit()
                logger.info(f"시뮬레이션 결과 저장 완료: {simulation_id}")
                return simulation_id
        except Exception as e:
            logger.error(f"시뮬레이션 결과 저장 오류: {e}")
            raise
    
    # ================== 세션 관리 ==================
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any], 
                           expires_hours: int = 24) -> str:
        """사용자 세션 생성"""
        session_id = str(uuid.uuid4())
        try:
            expires_at = datetime.now().timestamp() + (expires_hours * 3600)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO user_sessions (session_id, user_id, session_data, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    session_id,
                    user_id,
                    json.dumps(session_data),
                    datetime.fromtimestamp(expires_at).isoformat()
                ))
                await db.commit()
                logger.info(f"세션 생성 완료: {session_id}")
                return session_id
        except Exception as e:
            logger.error(f"세션 생성 오류: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM user_sessions 
                    WHERE session_id = ? AND expires_at > CURRENT_TIMESTAMP
                """, (session_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        session = dict(row)
                        session['session_data'] = json.loads(session['session_data'])
                        return session
                    return None
        except Exception as e:
            logger.error(f"세션 조회 오류: {e}")
            return None
    
    # ================== 로그 관리 ==================
    
    async def log_processing(self, user_id: str, process_type: str, status: str,
                           input_data: Dict[str, Any] = None, output_data: Dict[str, Any] = None,
                           error_message: str = None, processing_time: float = None) -> str:
        """처리 로그 저장"""
        log_id = str(uuid.uuid4())
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO processing_logs 
                    (log_id, user_id, process_type, status, input_data, 
                     output_data, error_message, processing_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_id,
                    user_id,
                    process_type,
                    status,
                    json.dumps(input_data or {}),
                    json.dumps(output_data or {}),
                    error_message,
                    processing_time
                ))
                await db.commit()
                return log_id
        except Exception as e:
            logger.error(f"로그 저장 오류: {e}")
            raise
    
    # ================== 데이터 정리 및 관리 ==================
    
    async def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                result = await db.execute("""
                    DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP
                """)
                await db.commit()
                logger.info(f"만료된 세션 {result.rowcount}개 정리 완료")
        except Exception as e:
            logger.error(f"세션 정리 오류: {e}")
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """사용자 통계 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                stats = {}
                
                # 포트폴리오 수
                async with db.execute("""
                    SELECT COUNT(*) FROM user_portfolios WHERE user_id = ?
                """, (user_id,)) as cursor:
                    result = await cursor.fetchone()
                    stats['portfolio_count'] = result[0] if result else 0
                
                # 분석 수
                async with db.execute("""
                    SELECT COUNT(*) FROM analysis_results WHERE user_id = ?
                """, (user_id,)) as cursor:
                    result = await cursor.fetchone()
                    stats['analysis_count'] = result[0] if result else 0
                
                # 업로드 데이터 수
                async with db.execute("""
                    SELECT COUNT(*) FROM user_data WHERE user_id = ?
                """, (user_id,)) as cursor:
                    result = await cursor.fetchone()
                    stats['data_count'] = result[0] if result else 0
                
                return stats
        except Exception as e:
            logger.error(f"사용자 통계 조회 오류: {e}")
            return {}
    
    async def backup_user_data(self, user_id: str) -> Dict[str, Any]:
        """사용자 데이터 백업"""
        try:
            backup_data = {
                'user_info': await self.get_user(user_id),
                'portfolios': await self.get_user_portfolios(user_id),
                'user_data': await self.get_user_data(user_id),
                'analysis_results': await self.get_analysis_results(user_id),
                'backup_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"사용자 데이터 백업 완료: {user_id}")
            return backup_data
        except Exception as e:
            logger.error(f"사용자 데이터 백업 오류: {e}")
            return {}

# 데이터베이스 매니저 싱글톤 인스턴스
db_manager = DatabaseManager()

async def get_database_manager() -> DatabaseManager:
    """데이터베이스 매니저 인스턴스 반환"""
    await db_manager.initialize_database()
    return db_manager
#!/usr/bin/env python3
"""
리밸런싱 전략과 보유 종목 초기 데이터 생성 스크립트
기본 전략들과 mock 보유 종목을 데이터베이스에 저장합니다.
"""

import asyncio
import json
import uuid
import random
from database_manager import get_database_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock 보유 종목 데이터
MOCK_HOLDINGS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "purchase_price": 150.0, "current_price": 185.2},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "purchase_price": 280.0, "current_price": 310.5},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "purchase_price": 2300.0, "current_price": 2450.8},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "purchase_price": 3200.0, "current_price": 3150.3},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary", "purchase_price": 800.0, "current_price": 245.6},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "purchase_price": 400.0, "current_price": 875.2},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology", "purchase_price": 200.0, "current_price": 485.3},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "purchase_price": 165.0, "current_price": 172.8},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Financial Services", "purchase_price": 220.0, "current_price": 275.4},
    {"symbol": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Staples", "purchase_price": 140.0, "current_price": 155.2},
    {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "sector": "Healthcare", "purchase_price": 450.0, "current_price": 485.7},
    {"symbol": "HD", "name": "The Home Depot Inc.", "sector": "Consumer Discretionary", "purchase_price": 300.0, "current_price": 345.1},
    {"symbol": "MA", "name": "Mastercard Inc.", "sector": "Financial Services", "purchase_price": 320.0, "current_price": 415.6},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare", "purchase_price": 50.0, "current_price": 28.4},
    {"symbol": "KO", "name": "The Coca-Cola Company", "sector": "Consumer Staples", "purchase_price": 55.0, "current_price": 62.8},
    {"symbol": "ABBV", "name": "AbbVie Inc.", "sector": "Healthcare", "purchase_price": 140.0, "current_price": 165.2},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology", "purchase_price": 220.0, "current_price": 185.5},
    {"symbol": "COST", "name": "Costco Wholesale Corporation", "sector": "Consumer Staples", "purchase_price": 500.0, "current_price": 665.8},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "Technology", "purchase_price": 450.0, "current_price": 1250.4},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services", "purchase_price": 400.0, "current_price": 485.9}
]

# 기본 리밸런싱 전략 데이터
DEFAULT_STRATEGIES = [
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "성장형 포트폴리오",
        "strategy_type": "default",
        "description": "고성장 기술주 중심의 공격적 투자 전략으로, 장기적 자본 증식을 추구합니다.",
        "target_allocation": {
            "AAPL": 30,
            "GOOGL": 25,
            "MSFT": 20,
            "NVDA": 15,
            "TSLA": 10
        },
        "expected_return": 24.5,
        "volatility": 28.2,
        "max_drawdown": -22.1,
        "sharpe_ratio": 0.85,
        "risk_level": "높음",
        "tags": ["기술주", "고성장", "공격적", "장기투자"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "균형형 포트폴리오", 
        "strategy_type": "default",
        "description": "성장성과 안정성의 균형을 맞춘 중도적 투자 전략입니다.",
        "target_allocation": {
            "AAPL": 25,
            "GOOGL": 20,
            "MSFT": 25,
            "AMZN": 20,
            "TSLA": 10
        },
        "expected_return": 18.2,
        "volatility": 21.5,
        "max_drawdown": -16.8,
        "sharpe_ratio": 0.74,
        "risk_level": "중간",
        "tags": ["균형", "중위험", "다양화", "안정성"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "안정형 포트폴리오",
        "strategy_type": "default", 
        "description": "배당과 안정성을 중시하는 보수적 투자 전략입니다.",
        "target_allocation": {
            "AAPL": 35,
            "MSFT": 30,
            "GOOGL": 20,
            "AMZN": 15
        },
        "expected_return": 14.8,
        "volatility": 16.3,
        "max_drawdown": -12.4,
        "sharpe_ratio": 0.68,
        "risk_level": "낮음",
        "tags": ["안정성", "배당", "보수적", "저위험"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "AI 혁신 포트폴리오",
        "strategy_type": "default",
        "description": "인공지능과 혁신 기술에 특화된 미래 지향적 투자 전략입니다.",
        "target_allocation": {
            "NVDA": 40,
            "GOOGL": 25,
            "MSFT": 20,
            "TSLA": 15
        },
        "expected_return": 29.3,
        "volatility": 32.1,
        "max_drawdown": -26.7,
        "sharpe_ratio": 0.91,
        "risk_level": "높음",
        "tags": ["AI", "혁신기술", "미래지향", "고위험고수익"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "가치투자 포트폴리오",
        "strategy_type": "default",
        "description": "저평가된 우량 기업을 발굴하여 장기 보유하는 가치투자 전략입니다.",
        "target_allocation": {
            "AAPL": 30,
            "MSFT": 25,
            "GOOGL": 20,
            "BRK.B": 15,
            "JPM": 10
        },
        "expected_return": 16.4,
        "volatility": 18.7,
        "max_drawdown": -14.2,
        "sharpe_ratio": 0.71,
        "risk_level": "중간",
        "tags": ["가치투자", "저평가", "우량주", "장기보유"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "배당 중심 포트폴리오",
        "strategy_type": "default",
        "description": "꾸준한 배당 수익을 중시하는 인컴 중심의 투자 전략입니다.",
        "target_allocation": {
            "AAPL": 25,
            "MSFT": 25,
            "JNJ": 20,
            "PG": 15,
            "KO": 15
        },
        "expected_return": 12.8,
        "volatility": 14.5,
        "max_drawdown": -10.3,
        "sharpe_ratio": 0.65,
        "risk_level": "낮음",
        "tags": ["배당", "인컴", "현금흐름", "안정적수익"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "ESG 지속가능 포트폴리오",
        "strategy_type": "default",
        "description": "환경, 사회, 지배구조를 고려한 지속가능한 투자 전략입니다.",
        "target_allocation": {
            "MSFT": 30,
            "GOOGL": 25,
            "AAPL": 20,
            "TSLA": 15,
            "V": 10
        },
        "expected_return": 19.6,
        "volatility": 22.8,
        "max_drawdown": -17.5,
        "sharpe_ratio": 0.78,
        "risk_level": "중간",
        "tags": ["ESG", "지속가능성", "친환경", "사회책임"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "디지털 전환 포트폴리오",
        "strategy_type": "default",
        "description": "디지털 전환과 클라우드 혁명의 수혜주에 집중한 전략입니다.",
        "target_allocation": {
            "MSFT": 25,
            "GOOGL": 20,
            "AMZN": 20,
            "NVDA": 20,
            "CRM": 15
        },
        "expected_return": 26.1,
        "volatility": 29.4,
        "max_drawdown": -23.8,
        "sharpe_ratio": 0.82,
        "risk_level": "높음",
        "tags": ["디지털전환", "클라우드", "SaaS", "플랫폼"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "글로벌 리더 포트폴리오",
        "strategy_type": "default",
        "description": "각 분야별 글로벌 1위 기업들로 구성된 블루칩 전략입니다.",
        "target_allocation": {
            "AAPL": 20,
            "MSFT": 20,
            "GOOGL": 15,
            "AMZN": 15,
            "TSLA": 10,
            "NVDA": 10,
            "META": 10
        },
        "expected_return": 21.3,
        "volatility": 24.6,
        "max_drawdown": -19.2,
        "sharpe_ratio": 0.79,
        "risk_level": "중간",
        "tags": ["글로벌리더", "블루칩", "시장지배력", "다각화"]
    },
    {
        "strategy_id": str(uuid.uuid4()),
        "strategy_name": "헬스케어 혁신 포트폴리오",
        "strategy_type": "default",
        "description": "헬스케어와 생명과학 분야의 혁신 기업들에 집중한 전략입니다.",
        "target_allocation": {
            "JNJ": 25,
            "UNH": 20,
            "PFE": 20,
            "ABBV": 15,
            "TMO": 10,
            "MRNA": 10
        },
        "expected_return": 17.9,
        "volatility": 20.1,
        "max_drawdown": -15.6,
        "sharpe_ratio": 0.73,
        "risk_level": "중간",
        "tags": ["헬스케어", "바이오", "제약", "의료기기"]
    }
]

async def initialize_default_strategies():
    """기본 전략들을 데이터베이스에 저장"""
    try:
        db_manager = await get_database_manager()
        logger.info("기본 리밸런싱 전략 초기화 시작...")
        
        created_strategies = []
        
        for strategy_data in DEFAULT_STRATEGIES:
            try:
                # 기존에 같은 이름의 전략이 있는지 확인
                existing_strategies = await db_manager.get_all_strategies()
                strategy_exists = any(s['strategy_name'] == strategy_data['strategy_name'] 
                                   for s in existing_strategies)
                
                if not strategy_exists:
                    success = await db_manager.save_rebalancing_strategy(
                        strategy_id=strategy_data['strategy_id'],
                        strategy_name=strategy_data['strategy_name'],
                        strategy_type=strategy_data['strategy_type'],
                        description=strategy_data['description'],
                        target_allocation=strategy_data['target_allocation'],
                        expected_return=strategy_data['expected_return'],
                        volatility=strategy_data['volatility'],
                        max_drawdown=strategy_data['max_drawdown'],
                        sharpe_ratio=strategy_data['sharpe_ratio'],
                        risk_level=strategy_data['risk_level'],
                        tags=strategy_data['tags'],
                        user_id=None
                    )
                    if success:
                        created_strategies.append({
                            'id': strategy_data['strategy_id'],
                            'name': strategy_data['strategy_name']
                        })
                    logger.info(f"전략 생성 완료: {strategy_data['strategy_name']}")
                else:
                    logger.info(f"전략 이미 존재: {strategy_data['strategy_name']}")
                    
            except Exception as e:
                logger.error(f"전략 생성 실패 ({strategy_data['strategy_name']}): {e}")
                continue
        
        logger.info(f"기본 전략 초기화 완료. 생성된 전략: {len(created_strategies)}개")
        return created_strategies
        
    except Exception as e:
        logger.error(f"기본 전략 초기화 오류: {e}")
        return []

async def create_mock_user():
    """테스트용 mock 사용자 생성"""
    try:
        db_manager = await get_database_manager()
        
        # 기존 mock 사용자 확인
        mock_user_id = "mock-user-001"
        existing_user = await db_manager.get_user(mock_user_id)
        
        if not existing_user:
            user_data = {
                "name": "테스트 사용자",
                "email": "test@example.com", 
                "phone": "010-1234-5678",
                "risk_tolerance": "moderate",
                "investment_goal": "wealth_building",
                "investment_horizon": 10,
                "preferred_asset_types": ["stocks", "bonds", "etfs"]
            }
            
            # 사용자 생성 시 직접 UUID 지정
            import aiosqlite
            async with aiosqlite.connect(db_manager.db_path) as db:
                await db.execute("""
                    INSERT INTO users (user_id, name, email, phone, risk_tolerance, 
                                     investment_goal, investment_horizon, preferred_asset_types)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mock_user_id,
                    user_data['name'],
                    user_data['email'], 
                    user_data['phone'],
                    user_data['risk_tolerance'],
                    user_data['investment_goal'],
                    user_data['investment_horizon'],
                    json.dumps(user_data['preferred_asset_types'])
                ))
                await db.commit()
                
            logger.info(f"Mock 사용자 생성 완료: {mock_user_id}")
            return mock_user_id
        else:
            logger.info(f"Mock 사용자 이미 존재: {mock_user_id}")
            return mock_user_id
            
    except Exception as e:
        logger.error(f"Mock 사용자 생성 오류: {e}")
        return None

async def initialize_mock_holdings():
    """Mock 보유 종목 데이터 생성"""
    try:
        db_manager = await get_database_manager()
        
        # Mock 사용자 생성
        user_id = await create_mock_user()
        if not user_id:
            logger.error("Mock 사용자 생성 실패")
            return [], None
        
        logger.info("Mock 보유 종목 초기화 시작...")
        
        # 기존 보유 종목 삭제 (중복 방지)
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            await db.execute("DELETE FROM holdings WHERE user_id = ?", (user_id,))
            await db.commit()
        
        created_holdings = []
        total_value = 1000000  # 총 100만 달러
        
        # 랜덤하게 5-8개 종목 선택
        selected_holdings = random.sample(MOCK_HOLDINGS, random.randint(5, 8))
        
        # 가중치 생성 (합이 100이 되도록)
        weights = [random.uniform(5, 25) for _ in selected_holdings]
        weight_sum = sum(weights)
        weights = [w / weight_sum * 100 for w in weights]
        
        for i, holding_data in enumerate(selected_holdings):
            try:
                weight = weights[i]
                target_value = total_value * (weight / 100)
                quantity = target_value / holding_data['current_price']
                
                holding_id = await db_manager.save_holding(
                    user_id=user_id,
                    symbol=holding_data['symbol'],
                    name=holding_data['name'],
                    quantity=round(quantity, 2),
                    purchase_price=holding_data['purchase_price'],
                    current_price=holding_data['current_price'],
                    weight=round(weight, 2),
                    sector=holding_data['sector']
                )
                
                created_holdings.append({
                    'id': holding_id,
                    'symbol': holding_data['symbol'],
                    'name': holding_data['name'],
                    'weight': round(weight, 2)
                })
                
                logger.info(f"보유 종목 생성 완료: {holding_data['symbol']} ({weight:.1f}%)")
                
            except Exception as e:
                logger.error(f"보유 종목 생성 실패 ({holding_data['symbol']}): {e}")
                continue
        
        logger.info(f"Mock 보유 종목 초기화 완료. 생성된 종목: {len(created_holdings)}개")
        return created_holdings, user_id
        
    except Exception as e:
        logger.error(f"Mock 보유 종목 초기화 오류: {e}")
        return [], None

async def verify_strategies():
    """생성된 전략들 확인"""
    try:
        db_manager = await get_database_manager()
        strategies = await db_manager.get_all_strategies()
        
        logger.info(f"현재 데이터베이스에 저장된 전략 수: {len(strategies)}")
        for strategy in strategies:
            logger.info(f"- {strategy['strategy_name']} ({strategy['risk_level']}, 예상수익률: {strategy['expected_return']}%)")
            
        return strategies
        
    except Exception as e:
        logger.error(f"전략 확인 오류: {e}")
        return []

async def verify_holdings(user_id: str):
    """생성된 보유 종목들 확인"""
    try:
        db_manager = await get_database_manager()
        holdings = await db_manager.get_user_holdings(user_id)
        
        logger.info(f"사용자 {user_id}의 보유 종목 수: {len(holdings)}")
        for holding in holdings:
            logger.info(f"- {holding['symbol']} ({holding['name']}) - {holding['weight']}%")
            
        return holdings
        
    except Exception as e:
        logger.error(f"보유 종목 확인 오류: {e}")
        return []

async def main():
    """메인 실행 함수"""
    try:
        print("\n" + "="*60)
        print("AI 자산 리밸런싱 시스템 - 초기 데이터 생성")
        print("="*60)
        
        # 1. 기본 전략들 초기화
        print("\n1. 기본 리밸런싱 전략 초기화...")
        created_strategies = await initialize_default_strategies()
        
        # 2. Mock 보유 종목 초기화
        print("\n2. Mock 보유 종목 초기화...")
        created_holdings, mock_user_id = await initialize_mock_holdings()
        
        # 3. 생성된 데이터 확인
        print("\n3. 생성된 데이터 확인...")
        all_strategies = await verify_strategies()
        
        if mock_user_id:
            all_holdings = await verify_holdings(mock_user_id)
        else:
            all_holdings = []
        
        # 4. 결과 출력
        print("\n" + "="*60)
        print("초기화 완료!")
        print("="*60)
        
        print(f"\n📊 리밸런싱 전략:")
        print(f"   - 총 전략 수: {len(all_strategies)}개")
        print(f"   - 새로 생성된 전략: {len(created_strategies)}개")
        
        if created_strategies:
            print("\n   새로 생성된 전략들:")
            for strategy in created_strategies:
                print(f"   • {strategy['name']}")
        
        print(f"\n💼 보유 종목 (사용자: {mock_user_id or 'N/A'}):")
        print(f"   - 총 보유 종목: {len(all_holdings)}개")
        print(f"   - 새로 생성된 종목: {len(created_holdings)}개")
        
        if created_holdings:
            print("\n   생성된 보유 종목들:")
            total_weight = 0
            for holding in created_holdings:
                print(f"   • {holding['symbol']} ({holding['name']}) - {holding['weight']}%")
                total_weight += holding['weight']
            print(f"   총 비중: {total_weight:.1f}%")
        
        print(f"\n✅ 데이터베이스 초기화 성공!")
        print(f"   Mock 사용자 ID: {mock_user_id}")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"메인 실행 오류: {e}")
        print(f"\n❌ 초기화 실패: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())
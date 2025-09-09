from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional, Union
import uvicorn
import logging
from datetime import datetime
import json
import uuid
from pathlib import Path
import tempfile
import os

# Import our custom modules
from data_processor import DataProcessor
from ai_model_trainer import AIModelTrainer
from simulation_analyzer import SimulationAnalyzer
from database_manager import get_database_manager
from user_data_processor import get_user_data_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Asset Rebalancing API",
    description="AI-powered asset rebalancing system with comprehensive portfolio analysis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",  # ngrok 동적 URL 지원을 위해 모든 origin 허용 (개발/데모용)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize modules
data_processor = DataProcessor()
ai_trainer = AIModelTrainer()
simulation_analyzer = SimulationAnalyzer()

# ================== Pydantic Models ==================

class UserRegistration(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    risk_tolerance: str  # conservative, moderate, aggressive
    investment_goal: str  # retirement, wealth_building, income_generation, growth
    investment_horizon: int  # years
    preferred_asset_types: List[str] = []

class UserProfile(BaseModel):
    investment_style: str  # conservative, moderate, aggressive
    investment_goal: str   # retirement, wealth, income, growth
    investment_period: str # short, medium, long
    risk_tolerance: Optional[str] = None
    investment_horizon: Optional[int] = None

class PortfolioItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    quantity: Optional[float] = None
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    weight: float  # percentage allocation

class Portfolio(BaseModel):
    name: str
    total_value: float
    currency: str = "KRW"
    holdings: List[PortfolioItem]

class UserDataUpload(BaseModel):
    data_type: str  # text, url
    content: str
    metadata: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    user_id: str
    user_profile: UserProfile
    current_portfolio: List[PortfolioItem]
    analysis_type: str = "comprehensive"  # comprehensive, quick, simulation_only
    include_stress_test: bool = True

class RebalancingResponse(BaseModel):
    status: str
    analysis_id: str
    user_id: str
    current_allocation: Dict[str, float]
    recommended_allocation: Dict[str, float]
    strategy: Dict[str, Any]
    simulation_results: Dict[str, Any]
    rationale: str
    confidence_score: float
    created_at: str

class TrainingRequest(BaseModel):
    user_id: str
    learning_config: Dict[str, Any]

class SimulationRequest(BaseModel):
    user_id: str
    portfolio_data: Dict[str, Any]
    strategies: List[Dict[str, Any]]
    simulation_config: Optional[Dict[str, Any]] = None

# ================== Dependency Functions ==================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """간단한 인증 (실제 환경에서는 JWT 등 사용)"""
    if not credentials:
        return None
    # 임시로 토큰을 user_id로 사용
    return credentials.credentials

# ================== Health & Root Endpoints ==================

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "AI Asset Rebalancing API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "포트폴리오 분석",
            "AI 전략 생성", 
            "백테스팅 시뮬레이션",
            "사용자 데이터 처리",
            "리스크 분석"
        ]
    }

@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    try:
        db_manager = await get_database_manager()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": "operational",
                "ai_trainer": "operational", 
                "data_processor": "operational",
                "simulation_analyzer": "operational"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

# ================== User Management ==================

@app.post("/users/register")
async def register_user(user_data: UserRegistration):
    """새 사용자 등록"""
    try:
        db_manager = await get_database_manager()
        user_id = await db_manager.create_user(user_data.dict())
        
        logger.info(f"New user registered: {user_id}")
        return {
            "status": "success",
            "user_id": user_id,
            "message": "사용자 등록이 완료되었습니다"
        }
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(status_code=400, detail=f"사용자 등록 실패: {str(e)}")

@app.get("/users/{user_id}")
async def get_user_info(user_id: str):
    """사용자 정보 조회"""
    try:
        db_manager = await get_database_manager()
        user_info = await db_manager.get_user(user_id)
        
        if not user_info:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return {"status": "success", "user": user_info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info failed: {e}")
        raise HTTPException(status_code=500, detail="사용자 정보 조회 실패")

@app.put("/users/{user_id}")
async def update_user_info(user_id: str, update_data: Dict[str, Any]):
    """사용자 정보 업데이트"""
    try:
        db_manager = await get_database_manager()
        success = await db_manager.update_user(user_id, update_data)
        
        if not success:
            raise HTTPException(status_code=400, detail="사용자 정보 업데이트 실패")
        
        return {"status": "success", "message": "사용자 정보가 업데이트되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user info failed: {e}")
        raise HTTPException(status_code=500, detail="사용자 정보 업데이트 실패")

@app.get("/users/{user_id}/statistics")
async def get_user_statistics(user_id: str):
    """사용자 통계 조회"""
    try:
        db_manager = await get_database_manager()
        stats = await db_manager.get_user_statistics(user_id)
        return {"status": "success", "statistics": stats}
    except Exception as e:
        logger.error(f"Get user statistics failed: {e}")
        raise HTTPException(status_code=500, detail="사용자 통계 조회 실패")

# ================== Portfolio Management ==================

@app.post("/portfolios")
async def create_portfolio(user_id: str, portfolio: Portfolio):
    """새 포트폴리오 생성"""
    try:
        db_manager = await get_database_manager()
        portfolio_data = {
            "name": portfolio.name,
            "total_value": portfolio.total_value,
            "currency": portfolio.currency,
            "holdings": [holding.dict() for holding in portfolio.holdings]
        }
        
        portfolio_id = await db_manager.save_portfolio(user_id, portfolio_data)
        
        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "message": "포트폴리오가 생성되었습니다"
        }
    except Exception as e:
        logger.error(f"Create portfolio failed: {e}")
        raise HTTPException(status_code=400, detail=f"포트폴리오 생성 실패: {str(e)}")

@app.get("/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """포트폴리오 조회"""
    try:
        db_manager = await get_database_manager()
        portfolio = await db_manager.get_portfolio(portfolio_id)
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다")
        
        return {"status": "success", "portfolio": portfolio}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get portfolio failed: {e}")
        raise HTTPException(status_code=500, detail="포트폴리오 조회 실패")

@app.get("/users/{user_id}/portfolios")
async def get_user_portfolios(user_id: str):
    """사용자의 모든 포트폴리오 조회"""
    try:
        db_manager = await get_database_manager()
        portfolios = await db_manager.get_user_portfolios(user_id)
        
        return {
            "status": "success",
            "portfolios": portfolios,
            "count": len(portfolios)
        }
    except Exception as e:
        logger.error(f"Get user portfolios failed: {e}")
        raise HTTPException(status_code=500, detail="포트폴리오 목록 조회 실패")

# ================== Market Data ==================

@app.get("/market-data/{symbol}")
async def get_market_data(symbol: str):
    """특정 종목의 시장 데이터 조회"""
    try:
        data = await data_processor.get_single_stock_data(symbol)
        return {"status": "success", "symbol": symbol, "data": data}
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시장 데이터 조회 실패: {symbol}")

@app.post("/market-data/batch")
async def get_batch_market_data(symbols: List[str]):
    """여러 종목의 시장 데이터 일괄 조회"""
    try:
        data = await data_processor.get_market_data(symbols)
        return {"status": "success", "data": data.to_dict('records') if hasattr(data, 'to_dict') else data}
    except Exception as e:
        logger.error(f"Error fetching batch market data: {str(e)}")
        raise HTTPException(status_code=500, detail="시장 데이터 일괄 조회 실패")

@app.get("/market-data/{symbol}/history")
async def get_historical_data(symbol: str, period: str = "1y"):
    """종목의 과거 데이터 조회"""
    try:
        data = await data_processor.get_historical_data(symbol, period)
        return {"status": "success", "symbol": symbol, "period": period, "data": data}
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"과거 데이터 조회 실패: {symbol}")

# ================== User Data Processing ==================

@app.post("/user-data/upload")
async def upload_user_data(user_id: str, data: UserDataUpload):
    """텍스트 또는 URL 데이터 업로드"""
    try:
        processor = await get_user_data_processor()
        result = await processor.process_user_data(
            user_id=user_id,
            data_type=data.data_type,
            data_input=data.content,
            filename=None
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Upload user data failed: {e}")
        raise HTTPException(status_code=400, detail=f"데이터 업로드 실패: {str(e)}")

@app.post("/user-data/upload-file")
async def upload_user_file(user_id: str = Form(...), file: UploadFile = File(...)):
    """파일 업로드"""
    try:
        # 파일 확장자 확인
        file_ext = Path(file.filename).suffix.lower()
        supported_extensions = ['.pdf', '.txt', '.md']
        
        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(supported_extensions)}"
            )
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        processor = await get_user_data_processor()
        result = await processor.process_user_data(
            user_id=user_id,
            data_type="file",
            data_input=file_content,
            filename=file.filename
        )
        
        return {"status": "success", "filename": file.filename, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload user file failed: {e}")
        raise HTTPException(status_code=400, detail=f"파일 업로드 실패: {str(e)}")

@app.get("/users/{user_id}/data")
async def get_user_data(user_id: str, data_type: Optional[str] = None):
    """사용자 업로드 데이터 조회"""
    try:
        db_manager = await get_database_manager()
        user_data = await db_manager.get_user_data(user_id, data_type)
        
        return {
            "status": "success",
            "user_data": user_data,
            "count": len(user_data)
        }
    except Exception as e:
        logger.error(f"Get user data failed: {e}")
        raise HTTPException(status_code=500, detail="사용자 데이터 조회 실패")

@app.post("/users/{user_id}/data/analyze")
async def analyze_user_data_comprehensive(user_id: str):
    """사용자 데이터 종합 분석"""
    try:
        processor = await get_user_data_processor()
        analysis = await processor.analyze_user_data_batch(user_id)
        
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        logger.error(f"Analyze user data failed: {e}")
        raise HTTPException(status_code=500, detail="사용자 데이터 분석 실패")

# ================== AI Training ==================

@app.post("/ai/train")
async def train_ai_model(request: TrainingRequest):
    """AI 모델 학습"""
    try:
        training_result = await ai_trainer.train_with_multiple_sources(request.learning_config)
        
        # 학습 결과를 데이터베이스에 저장
        db_manager = await get_database_manager()
        await db_manager.log_processing(
            user_id=request.user_id,
            process_type="ai_training",
            status="success",
            input_data=request.learning_config,
            output_data=training_result
        )
        
        return {"status": "success", "training_result": training_result}
    except Exception as e:
        logger.error(f"AI training failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI 학습 실패: {str(e)}")

@app.post("/ai/generate-strategy")
async def generate_investment_strategy(user_id: str, request_data: Dict[str, Any]):
    """투자 전략 생성"""
    try:
        strategy = await ai_trainer.generate_investment_strategy(request_data)
        
        # 전략을 데이터베이스에 저장
        db_manager = await get_database_manager()
        await db_manager.log_processing(
            user_id=user_id,
            process_type="strategy_generation",
            status="success",
            input_data=request_data,
            output_data=strategy
        )
        
        return {"status": "success", "strategy": strategy}
    except Exception as e:
        logger.error(f"Strategy generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"전략 생성 실패: {str(e)}")

# ================== Portfolio Analysis ==================

@app.post("/analysis/comprehensive", response_model=RebalancingResponse)
async def comprehensive_portfolio_analysis(request: AnalysisRequest):
    """종합 포트폴리오 분석"""
    try:
        logger.info(f"Starting comprehensive analysis for user: {request.user_id}")
        start_time = datetime.now()
        
        # 1. 시장 데이터 수집
        logger.info("Collecting market data...")
        stock_list = [item.symbol for item in request.current_portfolio]
        market_data = await data_processor.collect_and_process_data(stock_list)
        
        # 2. 사용자 데이터 분석
        logger.info("Analyzing user data...")
        processor = await get_user_data_processor()
        user_analysis = await processor.analyze_user_data_batch(request.user_id)
        
        # 3. AI 전략 생성
        logger.info("Generating AI strategy...")
        portfolio_dict = {item.symbol: item.weight for item in request.current_portfolio}
        
        strategy_input = {
            "user_profile": request.user_profile.dict(),
            "current_portfolio": portfolio_dict,
            "market_data": market_data.to_dict() if hasattr(market_data, 'to_dict') else market_data,
            "user_insights": user_analysis.get('comprehensive_insights', {}),
            "analysis_type": request.analysis_type
        }
        
        strategy = await ai_trainer.generate_investment_strategy(strategy_input)
        
        # 4. 시뮬레이션 실행
        logger.info("Running simulation...")
        simulation_config = {
            "include_stress_test": request.include_stress_test,
            "backtest_period": "2y",
            "rebalancing_frequency": "quarterly"
        }
        
        simulation_result = await simulation_analyzer.run_comprehensive_backtest(
            user_holding_data=portfolio_dict,
            historical_market_data=market_data,
            rebalancing_strategies=[strategy],
            simulation_config=simulation_config
        )
        
        # 5. 결과 저장
        db_manager = await get_database_manager()
        analysis_id = await db_manager.save_analysis_result(
            user_id=request.user_id,
            portfolio_id=None,  # 임시로 None
            analysis_type=request.analysis_type,
            input_data=request.dict(),
            results={
                "strategy": strategy,
                "simulation": simulation_result,
                "processing_time": (datetime.now() - start_time).total_seconds()
            },
            confidence_score=strategy.get('confidence_score', 0.8)
        )
        
        # 6. 리밸런싱 추천 저장
        current_allocation = {item.symbol: item.weight for item in request.current_portfolio}
        recommended_allocation = strategy.get('portfolio_allocation', {})
        
        await db_manager.save_rebalancing_recommendation(
            analysis_id=analysis_id,
            user_id=request.user_id,
            current_allocation=current_allocation,
            recommended_allocation=recommended_allocation,
            reasoning=strategy.get('rationale', ''),
            expected_return=strategy.get('expected_return'),
            risk_score=strategy.get('risk_score')
        )
        
        # 7. 시뮬레이션 결과 저장
        await db_manager.save_simulation_result(
            analysis_id=analysis_id,
            user_id=request.user_id,
            simulation_config=simulation_config,
            performance_metrics=simulation_result.get('performance_metrics', {}),
            backtest_results=simulation_result.get('backtest_results', {}),
            stress_test_results=simulation_result.get('stress_test_results', {})
        )
        
        # 8. 응답 생성
        response = RebalancingResponse(
            status="success",
            analysis_id=analysis_id,
            user_id=request.user_id,
            current_allocation=current_allocation,
            recommended_allocation=recommended_allocation,
            strategy=strategy,
            simulation_results=simulation_result,
            rationale=strategy.get('rationale', '포트폴리오 분석이 완료되었습니다'),
            confidence_score=strategy.get('confidence_score', 0.8),
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"Comprehensive analysis completed for user: {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"종합 분석 실패: {str(e)}")

@app.post("/analysis/simulation")
async def run_portfolio_simulation(request: SimulationRequest):
    """포트폴리오 시뮬레이션 실행"""
    try:
        logger.info(f"Starting simulation for user: {request.user_id}")
        
        # 시장 데이터 수집
        symbols = list(request.portfolio_data.keys())
        market_data = await data_processor.collect_and_process_data(symbols)
        
        # 시뮬레이션 실행
        simulation_result = await simulation_analyzer.run_comprehensive_backtest(
            user_holding_data=request.portfolio_data,
            historical_market_data=market_data,
            rebalancing_strategies=request.strategies,
            simulation_config=request.simulation_config
        )
        
        return {"status": "success", "simulation_result": simulation_result}
    except Exception as e:
        logger.error(f"Portfolio simulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"시뮬레이션 실패: {str(e)}")

# ================== Analysis Results ==================

@app.get("/users/{user_id}/analyses")
async def get_user_analyses(user_id: str, analysis_type: Optional[str] = None):
    """사용자의 분석 결과 조회"""
    try:
        db_manager = await get_database_manager()
        analyses = await db_manager.get_analysis_results(user_id, analysis_type)
        
        return {
            "status": "success", 
            "analyses": analyses,
            "count": len(analyses)
        }
    except Exception as e:
        logger.error(f"Get user analyses failed: {e}")
        raise HTTPException(status_code=500, detail="분석 결과 조회 실패")

@app.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """특정 분석 결과 조회"""
    try:
        # 구현 필요: 특정 분석 결과 조회 로직
        return {"status": "success", "message": "특정 분석 결과 조회 기능 구현 필요"}
    except Exception as e:
        logger.error(f"Get analysis result failed: {e}")
        raise HTTPException(status_code=500, detail="분석 결과 조회 실패")

# ================== Holdings Management ==================

@app.get("/users/{user_id}/holdings")
async def get_user_holdings(user_id: str):
    """사용자의 보유 종목 조회"""
    try:
        db_manager = await get_database_manager()
        holdings = await db_manager.get_user_holdings(user_id)
        
        # 총 포트폴리오 가치 계산
        total_value = sum(holding['market_value'] for holding in holdings)
        
        return {
            "status": "success",
            "user_id": user_id,
            "holdings": holdings,
            "total_value": total_value,
            "count": len(holdings)
        }
    except Exception as e:
        logger.error(f"Get user holdings failed: {e}")
        raise HTTPException(status_code=500, detail="보유 종목 조회 실패")

@app.get("/holdings")
async def get_all_holdings():
    """모든 보유 종목 조회 (관리자용)"""
    try:
        db_manager = await get_database_manager()
        holdings = await db_manager.get_all_holdings()
        
        return {
            "status": "success",
            "holdings": holdings,
            "count": len(holdings)
        }
    except Exception as e:
        logger.error(f"Get all holdings failed: {e}")
        raise HTTPException(status_code=500, detail="전체 보유 종목 조회 실패")

@app.post("/users/{user_id}/holdings")
async def create_holding(user_id: str, holding_data: Dict[str, Any]):
    """새 보유 종목 추가"""
    try:
        db_manager = await get_database_manager()
        
        holding_id = await db_manager.save_holding(
            user_id=user_id,
            symbol=holding_data['symbol'],
            name=holding_data.get('name', ''),
            quantity=holding_data['quantity'],
            purchase_price=holding_data['purchase_price'],
            current_price=holding_data['current_price'],
            weight=holding_data.get('weight', 0),
            sector=holding_data.get('sector', ''),
            currency=holding_data.get('currency', 'USD')
        )
        
        return {
            "status": "success",
            "holding_id": holding_id,
            "message": "보유 종목이 추가되었습니다"
        }
    except Exception as e:
        logger.error(f"Create holding failed: {e}")
        raise HTTPException(status_code=400, detail=f"보유 종목 추가 실패: {str(e)}")

@app.put("/users/{user_id}/holdings/prices")
async def update_holding_prices(user_id: str, price_updates: Dict[str, float]):
    """보유 종목 가격 업데이트"""
    try:
        db_manager = await get_database_manager()
        success = await db_manager.update_holding_prices(user_id, price_updates)
        
        if not success:
            raise HTTPException(status_code=400, detail="가격 업데이트 실패")
        
        return {
            "status": "success",
            "message": f"{len(price_updates)}개 종목의 가격이 업데이트되었습니다"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update holding prices failed: {e}")
        raise HTTPException(status_code=500, detail="가격 업데이트 실패")

@app.delete("/holdings/{holding_id}")
async def delete_holding(holding_id: str):
    """보유 종목 삭제"""
    try:
        db_manager = await get_database_manager()
        success = await db_manager.delete_holding(holding_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="보유 종목을 찾을 수 없습니다")
        
        return {
            "status": "success", 
            "message": "보유 종목이 삭제되었습니다"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete holding failed: {e}")
        raise HTTPException(status_code=500, detail="보유 종목 삭제 실패")

# ================== Rebalancing Strategies ==================

@app.get("/strategies")
async def get_all_strategies(user_id: str = None):
    """모든 리밸런싱 전략 조회 (기본 전략 + 사용자 생성 전략)"""
    try:
        db_manager = await get_database_manager()
        
        # 모든 전략 조회
        all_strategies = await db_manager.get_all_strategies(user_id)
        
        return {
            "status": "success",
            "strategies": all_strategies,
            "count": len(all_strategies)
        }
    except Exception as e:
        logger.error(f"Get all strategies failed: {e}")
        raise HTTPException(status_code=500, detail="전략 조회 실패")

@app.get("/strategies/{strategy_id}")
async def get_strategy_details(strategy_id: str):
    """특정 전략 상세 조회"""
    try:
        db_manager = await get_database_manager()
        strategy = await db_manager.get_strategy_by_id(strategy_id)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
            
        return {
            "status": "success",
            "strategy": strategy
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get strategy details failed: {e}")
        raise HTTPException(status_code=500, detail="전략 상세 조회 실패")

# ================== Strategy Templates ==================

@app.get("/strategies/templates")
async def get_strategy_templates():
    """투자 전략 템플릿 조회"""
    templates = {
        "conservative": {
            "name": "Conservative Strategy",
            "description": "Capital preservation focused with stable dividend-paying stocks",
            "risk_level": "Low",
            "expected_return": "5-7%",
            "typical_allocation": {
                "Large Cap Dividend": 25,  # JNJ, PG, KO
                "Utilities": 15,           # Electric, Gas utilities
                "Consumer Staples": 20,    # WMT, PG, KO
                "Treasury Bonds": 25,      # Government bonds
                "Cash/Money Market": 15    # Cash equivalents
            },
            "sample_stocks": ["JNJ", "PG", "KO", "WMT", "VZ", "T"],
            "characteristics": ["Low Volatility", "Stable Returns", "Capital Preservation"]
        },
        "moderate": {
            "name": "Balanced Strategy", 
            "description": "Balanced growth and stability with diversified sector exposure",
            "risk_level": "Medium",
            "expected_return": "7-10%",
            "typical_allocation": {
                "Large Cap Growth": 30,    # AAPL, MSFT, GOOGL
                "Value Stocks": 20,        # BRK-B, JPM, V
                "Healthcare": 15,          # JNJ, UNH, PFE
                "Corporate Bonds": 20,     # Investment grade bonds
                "Cash/Money Market": 5,    # Cash buffer
                "REITs": 10               # Real Estate Investment Trusts
            },
            "sample_stocks": ["AAPL", "MSFT", "JNJ", "JPM", "V", "UNH"],
            "characteristics": ["Balanced Risk", "Diversified Sectors", "Moderate Growth"]
        },
        "aggressive": {
            "name": "Growth Strategy",
            "description": "High growth potential with technology and emerging sector focus",
            "risk_level": "High", 
            "expected_return": "10-15%",
            "typical_allocation": {
                "Large Cap Tech": 40,      # AAPL, MSFT, GOOGL, NVDA
                "Growth Stocks": 25,       # AMZN, TSLA, META
                "Small Cap Growth": 15,    # Smaller growth companies
                "International": 10,       # International exposure
                "Commodities/Crypto": 5,   # Alternative investments
                "Cash": 5                  # Minimal cash
            },
            "sample_stocks": ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META"],
            "characteristics": ["High Growth Potential", "High Volatility", "Long-term Focus"]
        },
        "tech_focused": {
            "name": "Technology Focus",
            "description": "Technology sector concentration with AI and innovation themes",
            "risk_level": "High",
            "expected_return": "12-18%",
            "typical_allocation": {
                "AI/Semiconductor": 30,    # NVDA, AMD, INTC
                "Software Giants": 25,     # MSFT, GOOGL, CRM
                "Cloud/SaaS": 20,         # AMZN, MSFT, CRM
                "Consumer Tech": 15,       # AAPL, META, NFLX
                "Emerging Tech": 10        # Smaller tech innovators
            },
            "sample_stocks": ["NVDA", "MSFT", "GOOGL", "AAPL", "AMD", "CRM"],
            "characteristics": ["Innovation Focus", "High Beta", "Sector Concentration"]
        }
    }
    return {"status": "success", "templates": templates}

# ================== Utility Endpoints ==================

@app.post("/users/{user_id}/backup")
async def backup_user_data(user_id: str):
    """사용자 데이터 백업"""
    try:
        db_manager = await get_database_manager()
        backup_data = await db_manager.backup_user_data(user_id)
        
        return {"status": "success", "backup": backup_data}
    except Exception as e:
        logger.error(f"Backup user data failed: {e}")
        raise HTTPException(status_code=500, detail="데이터 백업 실패")

@app.post("/system/cleanup")
async def system_cleanup():
    """시스템 정리 (만료된 세션 등)"""
    try:
        db_manager = await get_database_manager()
        await db_manager.cleanup_expired_sessions()
        
        return {"status": "success", "message": "시스템 정리가 완료되었습니다"}
    except Exception as e:
        logger.error(f"System cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="시스템 정리 실패")

# ================== Startup Event ==================

@app.get("/database-ai/generate-strategy")
async def get_database_ai_info():
    """Database AI 엔드포인트 정보 및 사용법"""
    return {
        "name": "Database AI Strategy Generator",
        "description": "API 키 불필요한 자립형 포트폴리오 분석 시스템",
        "version": "1.0.0",
        "features": [
            "318개 전문가 전략 활용",
            "워런 버핏, 피터 린치, 레이 달리오 등 세계적 투자자 전략 융합", 
            "67-71% 신뢰도의 실시간 포트폴리오 최적화",
            "완전 오프라인 작동 가능"
        ],
        "usage": {
            "method": "POST",
            "endpoint": "/database-ai/generate-strategy",
            "required_fields": {
                "user_profile": {
                    "risk_tolerance": "conservative | moderate | aggressive",
                    "investment_goal": "wealth_building | retirement | income | growth",
                    "investment_horizon": "number (years)"
                }
            },
            "optional_fields": {
                "current_holdings": "array of current portfolio holdings"
            },
            "example_request": {
                "user_profile": {
                    "risk_tolerance": "moderate",
                    "investment_goal": "wealth_building",
                    "investment_horizon": 10
                },
                "current_holdings": []
            }
        },
        "curl_example": """curl -X POST "http://localhost:8003/database-ai/generate-strategy" \\
-H "Content-Type: application/json" \\
-d '{
  "user_profile": {
    "risk_tolerance": "moderate",
    "investment_goal": "wealth_building",
    "investment_horizon": 10
  }
}'"""
    }

@app.post("/database-ai/generate-strategy")
async def generate_database_ai_strategy(
    user_profile: Dict[str, Any],
    current_holdings: List[Dict[str, Any]] = None
):
    """Database AI 전용 전략 생성 (API 키 불필요)"""
    try:
        from database_ai_engine import get_database_ai_engine
        
        logger.info(f"Database AI 전략 생성 요청: {user_profile.get('risk_tolerance', 'unknown')}")
        
        # Database AI Engine 사용
        db_ai = await get_database_ai_engine()
        strategy = await db_ai.generate_intelligent_strategy(
            user_profile, 
            current_holdings or []
        )
        
        logger.info("✅ Database AI 전략 생성 성공")
        return {
            "status": "success",
            "strategy": strategy,
            "message": "Database AI 기반 전략 생성 완료 (API 키 불필요)",
            "api_info": {
                "expert_strategies_used": len(strategy.get("strategy_sources", [])),
                "confidence_score": strategy.get("confidence_score", 0),
                "strategy_type": "database_ai",
                "api_key_required": False
            }
        }
        
    except Exception as e:
        logger.error(f"Database AI 전략 생성 실패: {e}")
        return {
            "status": "error", 
            "message": f"Database AI 전략 생성 실패: {str(e)}",
            "help": "GET /database-ai/generate-strategy 에서 사용법을 확인하세요"
        }


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작시 실행"""
    try:
        # 데이터베이스 초기화
        db_manager = await get_database_manager()
        logger.info("Database initialized successfully")
        
        # AI 모델 초기화
        await ai_trainer.initialize()
        logger.info("AI trainer initialized successfully")
        
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
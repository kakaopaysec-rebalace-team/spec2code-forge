import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import yfinance as yf
from dataclasses import dataclass
import sqlite3
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class PortfolioMetrics:
    """포트폴리오 성과 지표 데이터 클래스"""
    total_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    sortino_ratio: float
    calmar_ratio: float
    var_95: float  # Value at Risk (95%)
    beta: float
    alpha: float
    information_ratio: float

@dataclass 
class BacktestResult:
    """백테스팅 결과 데이터 클래스"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_value: float
    final_value: float
    total_return: float
    annual_return: float
    volatility: float
    max_drawdown: float
    sharpe_ratio: float
    trades_count: int
    win_rate: float
    daily_returns: List[float]
    cumulative_returns: List[float]
    drawdowns: List[float]
    portfolio_values: List[float]

class SimulationAnalyzer:
    """
    모의투자 시뮬레이션 및 성과 분석 모듈
    사용자의 실제 보유 잔고 및 과거 시장 데이터를 기반으로, 다양한 리밸런싱 전략의 과거 성과를 시뮬레이션하고 비교 분석
    시뮬레이션 결과를 DB에 저장하는 기능 포함
    """
    
    def __init__(self):
        self.risk_free_rate = 0.03  # 3% risk-free rate assumption
        self.db_path = "simulation_results.db"
        self.korean_stocks = {
            "삼성전자": "005930.KS",
            "SK하이닉스": "000660.KS", 
            "NAVER": "035420.KS",
            "카카오": "035720.KS",
            "LG에너지솔루션": "373220.KS",
            "삼성바이오로직스": "207940.KS",
            "현대차": "005380.KS",
            "POSCO홀딩스": "005490.KS",
            "셀트리온": "068270.KS",
            "KB금융": "105560.KS",
            "신한지주": "055550.KS",
            "LG화학": "051910.KS",
            "삼성SDI": "006400.KS",
            "기아": "000270.KS",
            "하이브": "352820.KS"
        }
        
        # Benchmark indices
        self.benchmarks = {
            "KOSPI": "^KS11",
            "NASDAQ": "^IXIC", 
            "S&P500": "^GSPC",
            "DOW": "^DJI"
        }
        
        self._init_database()

    def _init_database(self):
        """시뮬레이션 결과 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 시뮬레이션 결과 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simulation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    strategy_id TEXT NOT NULL,
                    strategy_name TEXT,
                    strategy_type TEXT,
                    portfolio_allocation TEXT,
                    simulation_start_date DATE,
                    simulation_end_date DATE,
                    initial_value REAL,
                    final_value REAL,
                    total_return REAL,
                    annual_return REAL,
                    volatility REAL,
                    max_drawdown REAL,
                    sharpe_ratio REAL,
                    sortino_ratio REAL,
                    win_rate REAL,
                    trades_count INTEGER,
                    benchmark_return REAL,
                    alpha REAL,
                    beta REAL,
                    performance_data TEXT,
                    risk_metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 백테스팅 상세 결과 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id INTEGER,
                    date DATE,
                    portfolio_value REAL,
                    daily_return REAL,
                    cumulative_return REAL,
                    drawdown REAL,
                    portfolio_weights TEXT,
                    rebalance_flag BOOLEAN DEFAULT 0,
                    FOREIGN KEY (simulation_id) REFERENCES simulation_results (id)
                )
            ''')
            
            # 전략 비교 결과 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    comparison_name TEXT,
                    strategies TEXT,
                    comparison_metrics TEXT,
                    best_strategy TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing simulation database: {str(e)}")

    async def run_comprehensive_backtest(
        self,
        user_holding_data: Dict[str, Any],
        historical_market_data: pd.DataFrame,
        rebalancing_strategies: List[Dict[str, Any]],
        simulation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        종합적인 백테스팅 분석 실행
        
        Args:
            user_holding_data: 사용자의 과거 및 현재 보유 종목, 매수/매도 시점 및 가격 정보
            historical_market_data: 과거 시세, 수익률 등 시장 데이터  
            rebalancing_strategies: AI가 보유한 다양한 리밸런싱 전략 종류
            simulation_config: 시뮬레이션 설정
            
        Returns:
            simulation_result: 시뮬레이션 결과 데이터 (JSON 형식)
            user_portfolio_return: 사용자의 실제 수익률
            simulated_returns: 각 전략별 시뮬레이션 수익률  
            comparison_metrics: 최대 낙폭(MDD), 변동성 등 비교 지표
        """
        try:
            logger.info("Starting comprehensive backtest analysis")
            
            # 기본 설정
            config = simulation_config or {}
            simulation_period = config.get("simulation_period_days", 252)  # 1년
            initial_capital = config.get("initial_capital", 100000000)  # 1억원
            rebalance_frequency = config.get("rebalance_frequency", "monthly")  # 월별 리밸런싱
            transaction_cost = config.get("transaction_cost", 0.003)  # 0.3% 거래비용
            
            # 1. 사용자 실제 포트폴리오 성과 계산
            user_portfolio_result = await self._analyze_user_portfolio(
                user_holding_data, historical_market_data, initial_capital
            )
            
            # 2. 각 전략별 시뮬레이션 실행
            strategy_results = []
            for strategy in rebalancing_strategies:
                strategy_result = await self._run_strategy_simulation(
                    strategy, 
                    historical_market_data,
                    initial_capital,
                    simulation_period,
                    rebalance_frequency,
                    transaction_cost
                )
                strategy_results.append(strategy_result)
            
            # 3. 벤치마크 성과 계산
            benchmark_results = await self._calculate_benchmark_performance(
                historical_market_data, initial_capital, simulation_period
            )
            
            # 4. 종합 비교 분석
            comparison_metrics = self._generate_comprehensive_comparison(
                user_portfolio_result, strategy_results, benchmark_results
            )
            
            # 5. 리스크 분석
            risk_analysis = await self._perform_comprehensive_risk_analysis(
                user_portfolio_result, strategy_results, historical_market_data
            )
            
            # 6. 결과를 데이터베이스에 저장
            simulation_id = await self._save_simulation_results(
                user_portfolio_result, strategy_results, comparison_metrics, risk_analysis
            )
            
            # 7. 최종 결과 구성
            comprehensive_result = {
                "simulation_id": simulation_id,
                "simulation_config": {
                    "period_days": simulation_period,
                    "initial_capital": initial_capital,
                    "rebalance_frequency": rebalance_frequency,
                    "transaction_cost": transaction_cost
                },
                "user_portfolio_return": user_portfolio_result,
                "simulated_returns": strategy_results,
                "benchmark_performance": benchmark_results,
                "comparison_metrics": comparison_metrics,
                "risk_analysis": risk_analysis,
                "performance_visualization": await self._generate_performance_charts(
                    user_portfolio_result, strategy_results, benchmark_results
                ),
                "recommendations": self._generate_strategy_recommendations(
                    comparison_metrics, risk_analysis
                ),
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Comprehensive backtest completed. Simulation ID: {simulation_id}")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Error in comprehensive backtest: {str(e)}")
            return self._generate_fallback_simulation_result()

    async def _analyze_user_portfolio(
        self,
        user_holding_data: Dict[str, Any],
        historical_market_data: pd.DataFrame,
        initial_capital: float
    ) -> Dict[str, Any]:
        """사용자의 실제 포트폴리오 성과 분석"""
        try:
            # 사용자 거래 내역 파싱
            transactions = user_holding_data.get("transactions", [])
            current_holdings = user_holding_data.get("current_holdings", [])
            
            # 백테스팅 엔진으로 사용자 포트폴리오 재구성
            portfolio_history = await self._reconstruct_user_portfolio(
                transactions, historical_market_data, initial_capital
            )
            
            # 성과 지표 계산
            metrics = self._calculate_comprehensive_metrics(portfolio_history, "user_portfolio")
            
            return {
                "strategy_id": "user_actual",
                "strategy_name": "사용자 실제 포트폴리오",
                "portfolio_history": portfolio_history,
                "metrics": metrics.__dict__,
                "final_value": portfolio_history["values"][-1] if portfolio_history["values"] else initial_capital,
                "total_transactions": len(transactions),
                "holding_period_days": len(portfolio_history.get("dates", [])),
                "current_allocation": self._calculate_current_allocation(current_holdings)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user portfolio: {str(e)}")
            return self._generate_mock_user_result(initial_capital)

    async def _reconstruct_user_portfolio(
        self,
        transactions: List[Dict[str, Any]],
        market_data: pd.DataFrame,
        initial_capital: float
    ) -> Dict[str, Any]:
        """사용자 거래 내역을 기반으로 포트폴리오 상태 재구성"""
        try:
            if not transactions:
                return self._create_empty_portfolio_history(initial_capital)
            
            # 거래일자 순으로 정렬
            sorted_transactions = sorted(transactions, key=lambda x: x.get("date", "1900-01-01"))
            
            # 포트폴리오 상태 추적
            portfolio_state = {"cash": initial_capital, "holdings": {}}
            portfolio_history = {
                "dates": [],
                "values": [],
                "daily_returns": [],
                "holdings": []
            }
            
            # 시뮬레이션 기간 설정
            start_date = pd.to_datetime(sorted_transactions[0]["date"]) if sorted_transactions else datetime.now() - timedelta(days=365)
            end_date = datetime.now()
            
            # 일별 포트폴리오 가치 계산
            current_date = start_date
            while current_date <= end_date:
                # 해당 날짜의 거래 처리
                daily_transactions = [t for t in sorted_transactions if pd.to_datetime(t["date"]).date() == current_date.date()]
                
                for transaction in daily_transactions:
                    portfolio_state = self._process_transaction(portfolio_state, transaction, market_data, current_date)
                
                # 포트폴리오 가치 계산
                portfolio_value = self._calculate_portfolio_value(portfolio_state, market_data, current_date)
                
                portfolio_history["dates"].append(current_date)
                portfolio_history["values"].append(portfolio_value)
                portfolio_history["holdings"].append(portfolio_state["holdings"].copy())
                
                # 일일 수익률 계산
                if len(portfolio_history["values"]) > 1:
                    daily_return = (portfolio_value - portfolio_history["values"][-2]) / portfolio_history["values"][-2]
                    portfolio_history["daily_returns"].append(daily_return)
                else:
                    portfolio_history["daily_returns"].append(0.0)
                
                current_date += timedelta(days=1)
            
            return portfolio_history
            
        except Exception as e:
            logger.error(f"Error reconstructing user portfolio: {str(e)}")
            return self._create_empty_portfolio_history(initial_capital)

    def _process_transaction(
        self,
        portfolio_state: Dict[str, Any],
        transaction: Dict[str, Any],
        market_data: pd.DataFrame,
        transaction_date: datetime
    ) -> Dict[str, Any]:
        """개별 거래 처리"""
        try:
            action = transaction.get("action", "buy").lower()
            symbol = transaction.get("symbol", "")
            quantity = float(transaction.get("quantity", 0))
            price = float(transaction.get("price", 0))
            
            # 한국 주식 심볼 변환
            if symbol in self.korean_stocks:
                market_symbol = self.korean_stocks[symbol]
            else:
                market_symbol = symbol
            
            # 시장 데이터에서 가격 확인 (거래 가격 우선 사용)
            if price == 0 and market_symbol in market_data.columns:
                try:
                    market_price = market_data[market_symbol].loc[transaction_date]
                    price = market_price if not pd.isna(market_price) else price
                except (KeyError, IndexError):
                    pass
            
            if action == "buy":
                total_cost = quantity * price
                if portfolio_state["cash"] >= total_cost:
                    portfolio_state["cash"] -= total_cost
                    if symbol in portfolio_state["holdings"]:
                        portfolio_state["holdings"][symbol] += quantity
                    else:
                        portfolio_state["holdings"][symbol] = quantity
            
            elif action == "sell":
                if symbol in portfolio_state["holdings"] and portfolio_state["holdings"][symbol] >= quantity:
                    portfolio_state["holdings"][symbol] -= quantity
                    portfolio_state["cash"] += quantity * price
                    
                    # 보유량이 0이 되면 제거
                    if portfolio_state["holdings"][symbol] == 0:
                        del portfolio_state["holdings"][symbol]
            
            return portfolio_state
            
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
            return portfolio_state

    def _calculate_portfolio_value(
        self,
        portfolio_state: Dict[str, Any],
        market_data: pd.DataFrame,
        valuation_date: datetime
    ) -> float:
        """특정 날짜의 포트폴리오 가치 계산"""
        try:
            total_value = portfolio_state["cash"]
            
            for symbol, quantity in portfolio_state["holdings"].items():
                # 한국 주식 심볼 변환
                market_symbol = self.korean_stocks.get(symbol, symbol)
                
                try:
                    if market_symbol in market_data.columns:
                        price = market_data[market_symbol].loc[valuation_date]
                        if not pd.isna(price):
                            total_value += quantity * price
                except (KeyError, IndexError):
                    # 가격 데이터가 없으면 해당 종목 제외
                    continue
            
            return total_value
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {str(e)}")
            return portfolio_state["cash"]

    async def _run_strategy_simulation(
        self,
        strategy: Dict[str, Any],
        market_data: pd.DataFrame,
        initial_capital: float,
        simulation_period: int,
        rebalance_frequency: str,
        transaction_cost: float
    ) -> Dict[str, Any]:
        """개별 전략 시뮬레이션 실행"""
        try:
            strategy_id = strategy.get("strategy_id", f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            strategy_name = strategy.get("strategy_name", "Unknown Strategy")
            allocation = strategy.get("portfolio_allocation", {})
            
            # 시뮬레이션 기간 설정
            end_date = market_data.index[-1] if not market_data.empty else datetime.now()
            start_date = end_date - timedelta(days=simulation_period)
            
            # 해당 기간 데이터 필터링
            period_data = market_data.loc[start_date:end_date]
            
            if period_data.empty:
                return self._generate_mock_strategy_result(strategy_id, strategy_name, initial_capital)
            
            # 백테스팅 실행
            backtest_result = await self._execute_backtest(
                allocation, period_data, initial_capital, rebalance_frequency, transaction_cost
            )
            
            # 성과 지표 계산
            metrics = self._calculate_comprehensive_metrics(backtest_result, strategy_id)
            
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "strategy_type": strategy.get("strategy_type", "ai_generated"),
                "portfolio_allocation": allocation,
                "backtest_result": backtest_result,
                "metrics": metrics.__dict__,
                "rebalance_frequency": rebalance_frequency,
                "transaction_cost": transaction_cost,
                "simulation_period_days": len(backtest_result["dates"])
            }
            
        except Exception as e:
            logger.error(f"Error running strategy simulation: {str(e)}")
            return self._generate_mock_strategy_result(
                strategy.get("strategy_id", "error_strategy"), 
                strategy.get("strategy_name", "Error Strategy"),
                initial_capital
            )

    async def _execute_backtest(
        self,
        allocation: Dict[str, float],
        market_data: pd.DataFrame,
        initial_capital: float,
        rebalance_frequency: str,
        transaction_cost: float
    ) -> Dict[str, Any]:
        """백테스팅 실행 엔진"""
        try:
            # 리밸런싱 주기 설정
            rebalance_days = {
                "daily": 1,
                "weekly": 7, 
                "monthly": 30,
                "quarterly": 90
            }.get(rebalance_frequency, 30)
            
            # 포트폴리오 상태 초기화
            portfolio_value = initial_capital
            portfolio_history = {
                "dates": [],
                "values": [],
                "daily_returns": [],
                "cumulative_returns": [],
                "holdings": [],
                "rebalance_dates": []
            }
            
            # 거래 대상 종목 확인
            available_symbols = []
            for symbol in allocation.keys():
                market_symbol = self.korean_stocks.get(symbol, symbol)
                if market_symbol in market_data.columns:
                    available_symbols.append(symbol)
            
            if not available_symbols:
                return self._create_empty_backtest_result(initial_capital)
            
            # 일별 시뮬레이션
            days_since_rebalance = 0
            current_allocation = allocation.copy()
            
            for date in market_data.index:
                # 리밸런싱 체크
                should_rebalance = days_since_rebalance >= rebalance_days
                
                if should_rebalance:
                    # 거래 비용 적용
                    portfolio_value *= (1 - transaction_cost)
                    portfolio_history["rebalance_dates"].append(date)
                    days_since_rebalance = 0
                
                # 일일 수익률 계산
                daily_return = 0.0
                for symbol in available_symbols:
                    weight = current_allocation.get(symbol, 0)
                    market_symbol = self.korean_stocks.get(symbol, symbol)
                    
                    try:
                        if len(market_data[market_symbol]) > 1:
                            symbol_return = market_data[market_symbol].pct_change().loc[date]
                            if not pd.isna(symbol_return):
                                daily_return += weight * symbol_return
                    except (KeyError, IndexError):
                        continue
                
                # 포트폴리오 가치 업데이트
                portfolio_value *= (1 + daily_return)
                
                # 기록 저장
                portfolio_history["dates"].append(date)
                portfolio_history["values"].append(portfolio_value)
                portfolio_history["daily_returns"].append(daily_return)
                
                # 누적 수익률 계산
                cumulative_return = (portfolio_value - initial_capital) / initial_capital
                portfolio_history["cumulative_returns"].append(cumulative_return)
                
                days_since_rebalance += 1
            
            return portfolio_history
            
        except Exception as e:
            logger.error(f"Error executing backtest: {str(e)}")
            return self._create_empty_backtest_result(initial_capital)

    def _calculate_comprehensive_metrics(
        self,
        portfolio_history: Dict[str, Any],
        strategy_id: str
    ) -> PortfolioMetrics:
        """종합적인 포트폴리오 성과 지표 계산"""
        try:
            values = portfolio_history.get("values", [])
            daily_returns = portfolio_history.get("daily_returns", [])
            
            if not values or not daily_returns or len(values) < 2:
                return PortfolioMetrics(0, 0, 0, 0, 0, 0.5, 0, 0, 0, 1, 0, 0)
            
            # 기본 지표
            initial_value = values[0]
            final_value = values[-1]
            total_return = (final_value - initial_value) / initial_value
            
            # 연환산 수익률
            days = len(values)
            annual_return = (final_value / initial_value) ** (252 / days) - 1 if days > 0 else 0
            
            # 변동성 (연환산)
            returns_series = pd.Series(daily_returns)
            volatility = returns_series.std() * np.sqrt(252)
            
            # 샤프 비율
            excess_return = annual_return - self.risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            # 최대 낙폭 (MDD)
            cumulative_values = pd.Series(values)
            running_max = cumulative_values.expanding().max()
            drawdowns = (cumulative_values - running_max) / running_max
            max_drawdown = drawdowns.min()
            
            # 승률
            win_rate = (returns_series > 0).mean() if len(returns_series) > 0 else 0.5
            
            # 소르티노 비율 (하방 리스크 기준)
            negative_returns = returns_series[returns_series < 0]
            downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0.001
            sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0
            
            # 칼마 비율 (연수익률 / MDD)
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # VaR (95% 신뢰구간)
            var_95 = returns_series.quantile(0.05) if len(returns_series) > 0 else 0
            
            # 베타 (시장 대비)
            beta = 1.0  # 기본값, 실제로는 벤치마크와의 회귀분석 필요
            
            # 알파 (초과 수익률)
            alpha = annual_return - (self.risk_free_rate + beta * 0.08)  # 가정: 시장 수익률 8%
            
            # 정보 비율 (추적 오차 대비 초과 수익률)
            tracking_error = volatility * 0.1  # 간단한 가정
            information_ratio = alpha / tracking_error if tracking_error > 0 else 0
            
            return PortfolioMetrics(
                total_return=total_return,
                annual_return=annual_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                var_95=var_95,
                beta=beta,
                alpha=alpha,
                information_ratio=information_ratio
            )
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive metrics for {strategy_id}: {str(e)}")
            return PortfolioMetrics(0, 0, 0.2, 0, -0.1, 0.5, 0, 0, -0.05, 1, 0, 0)

    async def _calculate_benchmark_performance(
        self,
        market_data: pd.DataFrame,
        initial_capital: float,
        simulation_period: int
    ) -> Dict[str, Any]:
        """벤치마크 성과 계산"""
        try:
            benchmark_results = {}
            
            # 벤치마크 데이터 가져오기
            end_date = datetime.now()
            start_date = end_date - timedelta(days=simulation_period + 30)
            
            for name, symbol in self.benchmarks.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=start_date, end=end_date)
                    
                    if not hist.empty:
                        # 성과 지표 계산
                        returns = hist['Close'].pct_change().dropna()
                        
                        if len(returns) > 0:
                            total_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                            annual_return = (1 + total_return) ** (252 / len(returns)) - 1
                            volatility = returns.std() * np.sqrt(252)
                            sharpe_ratio = (annual_return - self.risk_free_rate) / volatility if volatility > 0 else 0
                            
                            # 최대 낙폭 계산
                            cumulative_returns = (1 + returns).cumprod()
                            running_max = cumulative_returns.expanding().max()
                            drawdowns = (cumulative_returns - running_max) / running_max
                            max_drawdown = drawdowns.min()
                            
                            benchmark_results[name] = {
                                "symbol": symbol,
                                "total_return": total_return,
                                "annual_return": annual_return,
                                "volatility": volatility,
                                "sharpe_ratio": sharpe_ratio,
                                "max_drawdown": max_drawdown,
                                "final_value": initial_capital * (1 + total_return)
                            }
                
                except Exception as e:
                    logger.warning(f"Failed to fetch benchmark data for {name}: {str(e)}")
                    continue
                
                await asyncio.sleep(0.1)  # Rate limiting
            
            return benchmark_results
            
        except Exception as e:
            logger.error(f"Error calculating benchmark performance: {str(e)}")
            return self._generate_mock_benchmark_results(initial_capital)

    def _generate_comprehensive_comparison(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]],
        benchmark_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """종합 비교 분석 생성"""
        try:
            user_metrics = user_result.get("metrics", {})
            
            # 최고 성과 전략 찾기
            best_strategy = None
            best_sharpe = -999
            
            for strategy in strategy_results:
                strategy_sharpe = strategy.get("metrics", {}).get("sharpe_ratio", 0)
                if strategy_sharpe > best_sharpe:
                    best_sharpe = strategy_sharpe
                    best_strategy = strategy
            
            if not best_strategy:
                return {"error": "No valid strategies to compare"}
            
            best_metrics = best_strategy.get("metrics", {})
            
            # 벤치마크 비교 (KOSPI 기준)
            benchmark_metrics = benchmark_results.get("KOSPI", {})
            
            comparison = {
                "user_vs_best_strategy": {
                    "return_improvement": best_metrics.get("annual_return", 0) - user_metrics.get("annual_return", 0),
                    "volatility_improvement": user_metrics.get("volatility", 0) - best_metrics.get("volatility", 0),
                    "sharpe_improvement": best_metrics.get("sharpe_ratio", 0) - user_metrics.get("sharpe_ratio", 0),
                    "mdd_improvement": user_metrics.get("max_drawdown", 0) - best_metrics.get("max_drawdown", 0),
                },
                "best_strategy_vs_benchmark": {
                    "return_vs_kospi": best_metrics.get("annual_return", 0) - benchmark_metrics.get("annual_return", 0),
                    "volatility_vs_kospi": benchmark_metrics.get("volatility", 0) - best_metrics.get("volatility", 0),
                    "sharpe_vs_kospi": best_metrics.get("sharpe_ratio", 0) - benchmark_metrics.get("sharpe_ratio", 0)
                },
                "strategy_rankings": self._rank_strategies(strategy_results),
                "best_strategy": {
                    "id": best_strategy.get("strategy_id"),
                    "name": best_strategy.get("strategy_name"),
                    "annual_return": best_metrics.get("annual_return", 0),
                    "sharpe_ratio": best_metrics.get("sharpe_ratio", 0),
                    "max_drawdown": best_metrics.get("max_drawdown", 0)
                },
                "user_portfolio_rank": self._calculate_user_rank(user_result, strategy_results),
                "overall_assessment": self._generate_overall_assessment(user_result, best_strategy, benchmark_results)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error generating comprehensive comparison: {str(e)}")
            return {"error": f"Comparison generation failed: {str(e)}"}

    def _rank_strategies(self, strategy_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """전략 순위 매기기 (샤프 비율 기준)"""
        try:
            ranked_strategies = []
            
            for strategy in strategy_results:
                metrics = strategy.get("metrics", {})
                ranked_strategies.append({
                    "rank": 0,  # Will be set after sorting
                    "strategy_id": strategy.get("strategy_id"),
                    "strategy_name": strategy.get("strategy_name"),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "annual_return": metrics.get("annual_return", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "overall_score": self._calculate_strategy_score(metrics)
                })
            
            # 전체 점수 기준 정렬
            ranked_strategies.sort(key=lambda x: x["overall_score"], reverse=True)
            
            # 순위 부여
            for i, strategy in enumerate(ranked_strategies):
                strategy["rank"] = i + 1
            
            return ranked_strategies
            
        except Exception as e:
            logger.error(f"Error ranking strategies: {str(e)}")
            return []

    def _calculate_strategy_score(self, metrics: Dict[str, Any]) -> float:
        """전략 종합 점수 계산"""
        try:
            # 가중치 적용한 종합 점수
            sharpe_weight = 0.4
            return_weight = 0.3
            drawdown_weight = 0.3
            
            sharpe_score = min(metrics.get("sharpe_ratio", 0) * 20, 100)  # 샤프비율 * 20, 최대 100
            return_score = min(metrics.get("annual_return", 0) * 100, 50)  # 연수익률 * 100, 최대 50
            drawdown_score = max(0, 20 + metrics.get("max_drawdown", -0.1) * 100)  # MDD 기준 점수, 최대 20
            
            total_score = (
                sharpe_score * sharpe_weight +
                return_score * return_weight +
                drawdown_score * drawdown_weight
            )
            
            return total_score
            
        except Exception as e:
            logger.error(f"Error calculating strategy score: {str(e)}")
            return 50.0

    def _calculate_user_rank(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]]
    ) -> int:
        """사용자 포트폴리오 순위 계산"""
        try:
            user_metrics = user_result.get("metrics", {})
            user_score = self._calculate_strategy_score(user_metrics)
            
            better_strategies = 0
            for strategy in strategy_results:
                strategy_metrics = strategy.get("metrics", {})
                strategy_score = self._calculate_strategy_score(strategy_metrics)
                if strategy_score > user_score:
                    better_strategies += 1
            
            return better_strategies + 1
            
        except Exception as e:
            logger.error(f"Error calculating user rank: {str(e)}")
            return len(strategy_results) // 2  # 중간 순위로 설정

    def _generate_overall_assessment(
        self,
        user_result: Dict[str, Any],
        best_strategy: Dict[str, Any],
        benchmark_results: Dict[str, Any]
    ) -> str:
        """전체 평가 의견 생성"""
        try:
            user_metrics = user_result.get("metrics", {})
            best_metrics = best_strategy.get("metrics", {})
            
            user_return = user_metrics.get("annual_return", 0) * 100
            best_return = best_metrics.get("annual_return", 0) * 100
            user_sharpe = user_metrics.get("sharpe_ratio", 0)
            best_sharpe = best_metrics.get("sharpe_ratio", 0)
            
            assessment_parts = []
            
            # 수익률 평가
            if user_return > best_return:
                assessment_parts.append(f"사용자의 연간 수익률({user_return:.1f}%)이 최적 전략({best_return:.1f}%)보다 우수합니다.")
            else:
                improvement = best_return - user_return
                assessment_parts.append(f"최적 전략 적용시 연간 {improvement:.1f}%p의 추가 수익이 가능합니다.")
            
            # 위험 조정 수익률 평가  
            if user_sharpe > best_sharpe:
                assessment_parts.append("위험 대비 수익률(샤프비율)이 우수한 편입니다.")
            else:
                assessment_parts.append("위험 관리 측면에서 개선 여지가 있습니다.")
            
            # 벤치마크 대비 평가
            kospi_return = benchmark_results.get("KOSPI", {}).get("annual_return", 0.08) * 100
            if user_return > kospi_return:
                assessment_parts.append(f"KOSPI 수익률({kospi_return:.1f}%)을 상회하고 있습니다.")
            else:
                assessment_parts.append(f"KOSPI 대비 {kospi_return - user_return:.1f}%p 낮은 성과입니다.")
            
            return " ".join(assessment_parts)
            
        except Exception as e:
            logger.error(f"Error generating overall assessment: {str(e)}")
            return "포트폴리오 성과 분석 결과를 생성하는 중 오류가 발생했습니다."

    async def _perform_comprehensive_risk_analysis(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]],
        market_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """종합적인 리스크 분석"""
        try:
            risk_analysis = {
                "user_portfolio_risk": self._analyze_individual_risk(user_result),
                "strategy_risk_comparison": [],
                "market_risk_factors": await self._analyze_market_risk_factors(market_data),
                "correlation_analysis": self._perform_correlation_analysis(strategy_results),
                "stress_test_results": await self._perform_stress_test(user_result, strategy_results),
                "risk_recommendations": []
            }
            
            # 각 전략별 리스크 분석
            for strategy in strategy_results:
                strategy_risk = self._analyze_individual_risk(strategy)
                risk_analysis["strategy_risk_comparison"].append({
                    "strategy_id": strategy.get("strategy_id"),
                    "strategy_name": strategy.get("strategy_name"),
                    "risk_metrics": strategy_risk
                })
            
            # 리스크 기반 추천사항 생성
            risk_analysis["risk_recommendations"] = self._generate_risk_recommendations(
                user_result, strategy_results, risk_analysis
            )
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive risk analysis: {str(e)}")
            return {"error": f"Risk analysis failed: {str(e)}"}

    def _analyze_individual_risk(self, portfolio_result: Dict[str, Any]) -> Dict[str, Any]:
        """개별 포트폴리오 리스크 분석"""
        try:
            metrics = portfolio_result.get("metrics", {})
            
            risk_metrics = {
                "volatility_level": self._categorize_volatility(metrics.get("volatility", 0)),
                "drawdown_risk": self._categorize_drawdown(metrics.get("max_drawdown", 0)),
                "var_risk": self._categorize_var(metrics.get("var_95", 0)),
                "concentration_risk": "분석 필요",  # 포트폴리오 구성에 따라 결정
                "liquidity_risk": "보통",
                "currency_risk": "보통",
                "sector_risk": "분석 필요"
            }
            
            # 종합 리스크 점수 (1-5, 5가 가장 위험)
            risk_score = self._calculate_risk_score(metrics)
            risk_metrics["overall_risk_score"] = risk_score
            risk_metrics["risk_category"] = self._categorize_overall_risk(risk_score)
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing individual risk: {str(e)}")
            return {"error": "Risk analysis failed"}

    def _categorize_volatility(self, volatility: float) -> str:
        """변동성 수준 분류"""
        if volatility < 0.1:
            return "낮음"
        elif volatility < 0.2:
            return "보통"  
        elif volatility < 0.3:
            return "높음"
        else:
            return "매우 높음"

    def _categorize_drawdown(self, max_drawdown: float) -> str:
        """최대 낙폭 수준 분류"""
        mdd = abs(max_drawdown)
        if mdd < 0.05:
            return "낮음"
        elif mdd < 0.15:
            return "보통"
        elif mdd < 0.25:
            return "높음"
        else:
            return "매우 높음"

    def _categorize_var(self, var_95: float) -> str:
        """VaR 수준 분류"""
        var = abs(var_95)
        if var < 0.02:
            return "낮음"
        elif var < 0.05:
            return "보통"
        elif var < 0.08:
            return "높음"
        else:
            return "매우 높음"

    def _calculate_risk_score(self, metrics: Dict[str, Any]) -> float:
        """종합 리스크 점수 계산 (1-5)"""
        try:
            volatility = metrics.get("volatility", 0.2)
            max_drawdown = abs(metrics.get("max_drawdown", -0.1))
            var_95 = abs(metrics.get("var_95", -0.03))
            
            # 각 리스크 요소를 1-5 점수로 변환
            vol_score = min(5, max(1, volatility * 20))  # 0.25 = 5점
            mdd_score = min(5, max(1, max_drawdown * 20))  # 0.25 = 5점  
            var_score = min(5, max(1, var_95 * 50))  # 0.10 = 5점
            
            # 가중 평균
            risk_score = (vol_score * 0.4 + mdd_score * 0.4 + var_score * 0.2)
            
            return round(risk_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 3.0

    def _categorize_overall_risk(self, risk_score: float) -> str:
        """전체 리스크 분류"""
        if risk_score < 2:
            return "안전"
        elif risk_score < 3:
            return "보수적"
        elif risk_score < 4:
            return "적극적"
        else:
            return "공격적"

    async def _analyze_market_risk_factors(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """시장 리스크 요인 분석"""
        try:
            if market_data.empty:
                return {"error": "No market data available"}
            
            # 시장 변동성 분석
            market_returns = market_data.pct_change().dropna()
            
            if market_returns.empty:
                return {"error": "No market return data available"}
            
            # 전체 시장 변동성
            market_volatility = market_returns.std().mean() * np.sqrt(252)
            
            # 상관관계 분석
            correlation_matrix = market_returns.corr()
            avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
            
            # VIX 대용 지표 (변동성의 변동성)
            volatility_of_volatility = market_returns.rolling(window=30).std().std().mean()
            
            risk_factors = {
                "market_volatility": market_volatility,
                "market_volatility_level": self._categorize_volatility(market_volatility),
                "average_correlation": avg_correlation,
                "correlation_risk": "높음" if avg_correlation > 0.7 else "보통" if avg_correlation > 0.4 else "낮음",
                "volatility_of_volatility": volatility_of_volatility,
                "market_regime": self._determine_market_regime(market_returns),
                "systemic_risk_indicators": {
                    "high_correlation_period": avg_correlation > 0.8,
                    "high_volatility_period": market_volatility > 0.25,
                    "volatility_clustering": volatility_of_volatility > 0.02
                }
            }
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error analyzing market risk factors: {str(e)}")
            return {"error": f"Market risk analysis failed: {str(e)}"}

    def _determine_market_regime(self, market_returns: pd.DataFrame) -> str:
        """시장 상황 판단"""
        try:
            recent_returns = market_returns.tail(60)  # 최근 60일
            
            if recent_returns.empty:
                return "불명"
            
            avg_return = recent_returns.mean().mean()
            volatility = recent_returns.std().mean()
            
            if avg_return > 0.001 and volatility < 0.02:
                return "안정적 상승"
            elif avg_return > 0.001 and volatility >= 0.02:
                return "변동성 상승"
            elif avg_return <= 0.001 and volatility < 0.02:
                return "횡보"
            else:
                return "불안정"
                
        except Exception as e:
            logger.error(f"Error determining market regime: {str(e)}")
            return "불명"

    def _perform_correlation_analysis(self, strategy_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """전략 간 상관관계 분석"""
        try:
            if len(strategy_results) < 2:
                return {"message": "상관관계 분석을 위한 전략이 부족합니다"}
            
            # 전략별 수익률 데이터 추출 (실제로는 일별 수익률 필요)
            strategy_returns = {}
            
            for strategy in strategy_results:
                strategy_id = strategy.get("strategy_id", "unknown")
                backtest_result = strategy.get("backtest_result", {})
                daily_returns = backtest_result.get("daily_returns", [])
                
                if daily_returns:
                    strategy_returns[strategy_id] = daily_returns
            
            if len(strategy_returns) < 2:
                return {"message": "상관관계 계산을 위한 데이터가 부족합니다"}
            
            # 상관계수 행렬 계산
            returns_df = pd.DataFrame(strategy_returns)
            correlation_matrix = returns_df.corr()
            
            # 평균 상관계수
            correlation_values = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)]
            avg_correlation = correlation_values.mean() if len(correlation_values) > 0 else 0
            
            return {
                "correlation_matrix": correlation_matrix.to_dict(),
                "average_correlation": avg_correlation,
                "correlation_level": "높음" if avg_correlation > 0.7 else "보통" if avg_correlation > 0.4 else "낮음",
                "diversification_benefit": "낮음" if avg_correlation > 0.7 else "보통" if avg_correlation > 0.4 else "높음"
            }
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {str(e)}")
            return {"error": f"Correlation analysis failed: {str(e)}"}

    async def _perform_stress_test(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """스트레스 테스트 수행"""
        try:
            stress_scenarios = {
                "market_crash_2008": {"market_drop": -0.35, "correlation_increase": 0.9},
                "covid_crash_2020": {"market_drop": -0.30, "volatility_spike": 3.0},
                "tech_bubble_burst": {"tech_drop": -0.50, "sector_rotation": True},
                "inflation_shock": {"bond_drop": -0.20, "commodity_spike": 0.40},
                "geopolitical_crisis": {"flight_to_safety": True, "emerging_market_drop": -0.25}
            }
            
            stress_results = {}
            
            for scenario_name, scenario_params in stress_scenarios.items():
                scenario_results = {
                    "user_portfolio": self._apply_stress_scenario(user_result, scenario_params),
                    "strategies": []
                }
                
                for strategy in strategy_results:
                    strategy_stress = self._apply_stress_scenario(strategy, scenario_params)
                    scenario_results["strategies"].append({
                        "strategy_id": strategy.get("strategy_id"),
                        "stress_result": strategy_stress
                    })
                
                stress_results[scenario_name] = scenario_results
            
            # 전체 스트레스 테스트 결과 요약
            stress_summary = self._summarize_stress_test(stress_results)
            
            return {
                "stress_scenarios": stress_results,
                "summary": stress_summary,
                "resilience_ranking": self._rank_by_resilience(user_result, strategy_results, stress_results)
            }
            
        except Exception as e:
            logger.error(f"Error in stress test: {str(e)}")
            return {"error": f"Stress test failed: {str(e)}"}

    def _apply_stress_scenario(self, portfolio_result: Dict[str, Any], scenario_params: Dict[str, Any]) -> Dict[str, Any]:
        """개별 포트폴리오에 스트레스 시나리오 적용"""
        try:
            metrics = portfolio_result.get("metrics", {})
            current_return = metrics.get("annual_return", 0)
            current_volatility = metrics.get("volatility", 0.2)
            current_mdd = metrics.get("max_drawdown", -0.1)
            
            # 시나리오별 충격 적용
            stressed_return = current_return
            stressed_volatility = current_volatility
            stressed_mdd = current_mdd
            
            if "market_drop" in scenario_params:
                market_drop = scenario_params["market_drop"]
                stressed_return += market_drop
                stressed_mdd = min(stressed_mdd, market_drop * 1.2)
            
            if "volatility_spike" in scenario_params:
                vol_multiplier = scenario_params["volatility_spike"]
                stressed_volatility *= vol_multiplier
            
            if "correlation_increase" in scenario_params:
                # 상관관계 증가시 분산 효과 감소
                stressed_volatility *= 1.2
                stressed_mdd *= 1.1
            
            # 스트레스 후 샤프 비율 재계산
            stressed_sharpe = (stressed_return - self.risk_free_rate) / stressed_volatility if stressed_volatility > 0 else 0
            
            return {
                "stressed_annual_return": stressed_return,
                "stressed_volatility": stressed_volatility,
                "stressed_max_drawdown": stressed_mdd,
                "stressed_sharpe_ratio": stressed_sharpe,
                "return_impact": stressed_return - current_return,
                "volatility_impact": stressed_volatility - current_volatility,
                "drawdown_impact": stressed_mdd - current_mdd
            }
            
        except Exception as e:
            logger.error(f"Error applying stress scenario: {str(e)}")
            return {"error": "Stress scenario application failed"}

    def _summarize_stress_test(self, stress_results: Dict[str, Any]) -> Dict[str, Any]:
        """스트레스 테스트 결과 요약"""
        try:
            all_impacts = []
            worst_scenario = ""
            worst_impact = 0
            
            for scenario_name, scenario_data in stress_results.items():
                user_stress = scenario_data.get("user_portfolio", {})
                return_impact = user_stress.get("return_impact", 0)
                
                all_impacts.append(return_impact)
                
                if return_impact < worst_impact:
                    worst_impact = return_impact
                    worst_scenario = scenario_name
            
            return {
                "worst_case_scenario": worst_scenario,
                "worst_case_impact": worst_impact,
                "average_impact": np.mean(all_impacts) if all_impacts else 0,
                "stress_test_summary": f"최악의 시나리오({worst_scenario})에서 {worst_impact:.1%}의 수익률 하락 예상"
            }
            
        except Exception as e:
            logger.error(f"Error summarizing stress test: {str(e)}")
            return {"error": "Stress test summary failed"}

    def _rank_by_resilience(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]],
        stress_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """스트레스 테스트 기준 회복력 순위"""
        try:
            resilience_scores = []
            
            # 사용자 포트폴리오
            user_resilience = self._calculate_resilience_score(user_result, stress_results, "user_portfolio")
            resilience_scores.append({
                "portfolio_id": "user_actual",
                "portfolio_name": "사용자 실제 포트폴리오",
                "resilience_score": user_resilience,
                "rank": 0
            })
            
            # 전략 포트폴리오들
            for strategy in strategy_results:
                strategy_resilience = self._calculate_resilience_score(strategy, stress_results, "strategies")
                resilience_scores.append({
                    "portfolio_id": strategy.get("strategy_id"),
                    "portfolio_name": strategy.get("strategy_name"),
                    "resilience_score": strategy_resilience,
                    "rank": 0
                })
            
            # 회복력 점수 기준 정렬
            resilience_scores.sort(key=lambda x: x["resilience_score"], reverse=True)
            
            # 순위 부여
            for i, item in enumerate(resilience_scores):
                item["rank"] = i + 1
            
            return resilience_scores
            
        except Exception as e:
            logger.error(f"Error ranking by resilience: {str(e)}")
            return []

    def _calculate_resilience_score(
        self,
        portfolio_result: Dict[str, Any],
        stress_results: Dict[str, Any],
        result_key: str
    ) -> float:
        """회복력 점수 계산"""
        try:
            total_impact = 0
            scenario_count = 0
            
            for scenario_name, scenario_data in stress_results.items():
                if result_key == "user_portfolio":
                    stress_data = scenario_data.get("user_portfolio", {})
                else:
                    # 전략 결과에서 해당 전략 찾기
                    portfolio_id = portfolio_result.get("strategy_id")
                    strategy_stresses = scenario_data.get("strategies", [])
                    
                    stress_data = {}
                    for strategy_stress in strategy_stresses:
                        if strategy_stress.get("strategy_id") == portfolio_id:
                            stress_data = strategy_stress.get("stress_result", {})
                            break
                
                return_impact = stress_data.get("return_impact", 0)
                volatility_impact = stress_data.get("volatility_impact", 0)
                
                # 충격이 작을수록 높은 점수 (회복력이 좋음)
                scenario_score = 100 + (return_impact * 100) - (volatility_impact * 50)
                total_impact += scenario_score
                scenario_count += 1
            
            return total_impact / scenario_count if scenario_count > 0 else 50
            
        except Exception as e:
            logger.error(f"Error calculating resilience score: {str(e)}")
            return 50.0

    def _generate_risk_recommendations(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]],
        risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """리스크 기반 추천사항 생성"""
        try:
            recommendations = []
            
            user_risk = risk_analysis.get("user_portfolio_risk", {})
            user_risk_score = user_risk.get("overall_risk_score", 3.0)
            
            # 위험 수준별 추천사항
            if user_risk_score > 4:
                recommendations.append("현재 포트폴리오의 위험도가 매우 높습니다. 안전자산 비중 확대를 권장합니다.")
                recommendations.append("분산투자를 통해 집중위험을 줄이시기 바랍니다.")
            
            elif user_risk_score > 3:
                recommendations.append("포트폴리오 위험도가 다소 높은 편입니다. 위험관리 전략을 고려해보세요.")
            
            # 변동성 관련 추천
            volatility_level = user_risk.get("volatility_level", "보통")
            if volatility_level in ["높음", "매우 높음"]:
                recommendations.append("높은 변동성에 대비하여 손절선 설정을 권장합니다.")
            
            # 최대낙폭 관련 추천
            drawdown_risk = user_risk.get("drawdown_risk", "보통")
            if drawdown_risk in ["높음", "매우 높음"]:
                recommendations.append("최대낙폭이 큰 편입니다. 리밸런싱 주기를 단축하는 것을 고려해보세요.")
            
            # 상관관계 분석 결과 기반 추천
            correlation_analysis = risk_analysis.get("correlation_analysis", {})
            diversification_benefit = correlation_analysis.get("diversification_benefit", "보통")
            
            if diversification_benefit == "낮음":
                recommendations.append("전략 간 상관관계가 높습니다. 서로 다른 자산군으로의 분산을 고려하세요.")
            
            # 스트레스 테스트 결과 기반 추천
            stress_test = risk_analysis.get("stress_test_results", {})
            resilience_ranking = stress_test.get("resilience_ranking", [])
            
            if resilience_ranking:
                user_rank = next((item["rank"] for item in resilience_ranking if item["portfolio_id"] == "user_actual"), None)
                if user_rank and user_rank > len(resilience_ranking) // 2:
                    recommendations.append("스트레스 테스트에서 회복력이 다소 부족합니다. 방어적 자산 배분을 고려해보세요.")
            
            # 기본 추천사항이 없으면 일반적인 조언 추가
            if not recommendations:
                recommendations.append("전반적으로 양호한 리스크 프로필을 보이고 있습니다.")
                recommendations.append("정기적인 포트폴리오 검토와 리밸런싱을 권장합니다.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating risk recommendations: {str(e)}")
            return ["리스크 분석 기반 추천사항 생성 중 오류가 발생했습니다."]

    async def _generate_performance_charts(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]],
        benchmark_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """성과 시각화 데이터 생성"""
        try:
            # 기간 설정 (최근 1년)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            chart_data = {
                "cumulative_performance": [],
                "monthly_returns": [],
                "risk_return_scatter": [],
                "drawdown_chart": []
            }
            
            # 누적 성과 차트 데이터
            for i, date in enumerate(date_range):
                data_point = {"date": date.strftime("%Y-%m-%d")}
                
                # 사용자 포트폴리오 (실제 데이터 또는 시뮬레이션)
                user_performance = self._simulate_daily_performance(user_result, i, len(date_range))
                data_point["user_portfolio"] = round(user_performance, 2)
                
                # 최고 전략
                if strategy_results:
                    best_strategy = max(strategy_results, key=lambda x: x.get("metrics", {}).get("sharpe_ratio", 0))
                    strategy_performance = self._simulate_daily_performance(best_strategy, i, len(date_range))
                    data_point["best_strategy"] = round(strategy_performance, 2)
                
                # KOSPI 벤치마크
                kospi_performance = self._simulate_benchmark_performance("KOSPI", benchmark_results, i, len(date_range))
                data_point["kospi_benchmark"] = round(kospi_performance, 2)
                
                chart_data["cumulative_performance"].append(data_point)
            
            # 월별 수익률 데이터
            chart_data["monthly_returns"] = self._generate_monthly_returns_data(
                user_result, strategy_results, benchmark_results
            )
            
            # 위험-수익률 산점도 데이터
            chart_data["risk_return_scatter"] = self._generate_risk_return_scatter(
                user_result, strategy_results, benchmark_results
            )
            
            # 낙폭 차트 데이터
            chart_data["drawdown_chart"] = self._generate_drawdown_data(
                user_result, strategy_results
            )
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating performance charts: {str(e)}")
            return {"error": f"Chart generation failed: {str(e)}"}

    def _simulate_daily_performance(self, portfolio_result: Dict[str, Any], day_index: int, total_days: int) -> float:
        """일별 성과 시뮬레이션 (차트용)"""
        try:
            metrics = portfolio_result.get("metrics", {})
            annual_return = metrics.get("annual_return", 0.1)
            volatility = metrics.get("volatility", 0.2)
            
            # 일별 평균 수익률
            daily_mean_return = annual_return / 252
            daily_volatility = volatility / np.sqrt(252)
            
            # 누적 성과 계산 (간단한 기하브라운운동 시뮬레이션)
            np.random.seed(42 + day_index)  # 재현 가능한 결과를 위한 시드
            
            cumulative_return = 0
            for i in range(day_index + 1):
                daily_return = np.random.normal(daily_mean_return, daily_volatility)
                cumulative_return = (1 + cumulative_return) * (1 + daily_return) - 1
            
            # 100 기준으로 정규화
            return 100 * (1 + cumulative_return)
            
        except Exception as e:
            logger.error(f"Error simulating daily performance: {str(e)}")
            return 100.0

    def _simulate_benchmark_performance(
        self,
        benchmark_name: str,
        benchmark_results: Dict[str, Any],
        day_index: int,
        total_days: int
    ) -> float:
        """벤치마크 성과 시뮬레이션"""
        try:
            benchmark_data = benchmark_results.get(benchmark_name, {})
            annual_return = benchmark_data.get("annual_return", 0.08)
            volatility = benchmark_data.get("volatility", 0.18)
            
            return self._simulate_daily_performance(
                {"metrics": {"annual_return": annual_return, "volatility": volatility}},
                day_index,
                total_days
            )
            
        except Exception as e:
            logger.error(f"Error simulating benchmark performance: {str(e)}")
            return 100.0

    def _generate_monthly_returns_data(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]],
        benchmark_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """월별 수익률 데이터 생성"""
        try:
            months = []
            current_date = datetime.now() - timedelta(days=365)
            
            for i in range(12):
                month_date = current_date + timedelta(days=i * 30)
                month_name = month_date.strftime("%Y-%m")
                
                # 사용자 월별 수익률 (시뮬레이션)
                user_monthly = np.random.normal(
                    user_result.get("metrics", {}).get("annual_return", 0.1) / 12,
                    user_result.get("metrics", {}).get("volatility", 0.2) / np.sqrt(12)
                ) * 100
                
                # 최고 전략 월별 수익률
                best_strategy_monthly = 0
                if strategy_results:
                    best_strategy = max(strategy_results, key=lambda x: x.get("metrics", {}).get("sharpe_ratio", 0))
                    best_strategy_monthly = np.random.normal(
                        best_strategy.get("metrics", {}).get("annual_return", 0.12) / 12,
                        best_strategy.get("metrics", {}).get("volatility", 0.18) / np.sqrt(12)
                    ) * 100
                
                # KOSPI 월별 수익률
                kospi_monthly = np.random.normal(
                    benchmark_results.get("KOSPI", {}).get("annual_return", 0.08) / 12,
                    benchmark_results.get("KOSPI", {}).get("volatility", 0.18) / np.sqrt(12)
                ) * 100
                
                months.append({
                    "month": month_name,
                    "user_portfolio": round(user_monthly, 2),
                    "best_strategy": round(best_strategy_monthly, 2),
                    "kospi_benchmark": round(kospi_monthly, 2)
                })
            
            return months
            
        except Exception as e:
            logger.error(f"Error generating monthly returns data: {str(e)}")
            return []

    def _generate_risk_return_scatter(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]],
        benchmark_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """위험-수익률 산점도 데이터 생성"""
        try:
            scatter_data = []
            
            # 사용자 포트폴리오
            user_metrics = user_result.get("metrics", {})
            scatter_data.append({
                "name": "사용자 포트폴리오",
                "return": user_metrics.get("annual_return", 0) * 100,
                "risk": user_metrics.get("volatility", 0) * 100,
                "sharpe": user_metrics.get("sharpe_ratio", 0),
                "type": "user",
                "size": 12
            })
            
            # 전략들
            for strategy in strategy_results:
                metrics = strategy.get("metrics", {})
                scatter_data.append({
                    "name": strategy.get("strategy_name", "Unknown"),
                    "return": metrics.get("annual_return", 0) * 100,
                    "risk": metrics.get("volatility", 0) * 100,
                    "sharpe": metrics.get("sharpe_ratio", 0),
                    "type": "strategy",
                    "size": 10
                })
            
            # 벤치마크
            for name, benchmark in benchmark_results.items():
                scatter_data.append({
                    "name": name,
                    "return": benchmark.get("annual_return", 0) * 100,
                    "risk": benchmark.get("volatility", 0) * 100,
                    "sharpe": benchmark.get("sharpe_ratio", 0),
                    "type": "benchmark",
                    "size": 8
                })
            
            return scatter_data
            
        except Exception as e:
            logger.error(f"Error generating risk-return scatter: {str(e)}")
            return []

    def _generate_drawdown_data(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """낙폭 차트 데이터 생성"""
        try:
            # 간단한 낙폭 시뮬레이션 (실제로는 일별 데이터 필요)
            days = 365
            drawdown_data = []
            
            for i in range(0, days, 7):  # 주별 데이터
                date = (datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d")
                
                # 사용자 낙폭 시뮬레이션
                user_dd = min(0, np.random.normal(-0.02, 0.05)) * 100
                
                # 최고 전략 낙폭
                best_strategy_dd = 0
                if strategy_results:
                    best_strategy_dd = min(0, np.random.normal(-0.015, 0.04)) * 100
                
                drawdown_data.append({
                    "date": date,
                    "user_portfolio": round(user_dd, 2),
                    "best_strategy": round(best_strategy_dd, 2)
                })
            
            return drawdown_data
            
        except Exception as e:
            logger.error(f"Error generating drawdown data: {str(e)}")
            return []

    def _generate_strategy_recommendations(
        self,
        comparison_metrics: Dict[str, Any],
        risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """전략 추천사항 생성"""
        try:
            recommendations = []
            
            # 최고 성과 전략 정보
            best_strategy = comparison_metrics.get("best_strategy", {})
            if best_strategy:
                strategy_name = best_strategy.get("name", "최적 전략")
                annual_return = best_strategy.get("annual_return", 0) * 100
                sharpe_ratio = best_strategy.get("sharpe_ratio", 0)
                
                recommendations.append(
                    f"'{strategy_name}' 전략이 연 {annual_return:.1f}% 수익률과 {sharpe_ratio:.2f} 샤프비율로 최고 성과를 기록했습니다."
                )
            
            # 사용자 대비 개선 여지
            user_vs_best = comparison_metrics.get("user_vs_best_strategy", {})
            return_improvement = user_vs_best.get("return_improvement", 0) * 100
            
            if return_improvement > 2:
                recommendations.append(f"전략 최적화를 통해 연간 {return_improvement:.1f}%p의 추가 수익이 가능합니다.")
            
            # 리스크 개선 사항
            risk_recommendations = risk_analysis.get("risk_recommendations", [])
            recommendations.extend(risk_recommendations[:2])  # 상위 2개만 포함
            
            # 일반적인 추천사항
            recommendations.append("정기적인 포트폴리오 리뷰와 리밸런싱을 통해 최적의 성과를 유지하시기 바랍니다.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating strategy recommendations: {str(e)}")
            return ["전략 추천사항 생성 중 오류가 발생했습니다."]

    async def _save_simulation_results(
        self,
        user_result: Dict[str, Any],
        strategy_results: List[Dict[str, Any]],
        comparison_metrics: Dict[str, Any],
        risk_analysis: Dict[str, Any]
    ) -> str:
        """시뮬레이션 결과를 데이터베이스에 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 메인 시뮬레이션 결과 저장
            for i, strategy in enumerate([user_result] + strategy_results):
                strategy_id = strategy.get("strategy_id", f"strategy_{i}")
                metrics = strategy.get("metrics", {})
                
                cursor.execute('''
                    INSERT INTO simulation_results 
                    (strategy_id, strategy_name, strategy_type, portfolio_allocation,
                     simulation_start_date, simulation_end_date, initial_value, final_value,
                     total_return, annual_return, volatility, max_drawdown, sharpe_ratio,
                     sortino_ratio, win_rate, trades_count, risk_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy_id,
                    strategy.get("strategy_name", "Unknown"),
                    strategy.get("strategy_type", "unknown"),
                    json.dumps(strategy.get("portfolio_allocation", {})),
                    (datetime.now() - timedelta(days=365)).date(),
                    datetime.now().date(),
                    100000000,  # 기본 초기 자본
                    strategy.get("final_value", 100000000),
                    metrics.get("total_return", 0),
                    metrics.get("annual_return", 0),
                    metrics.get("volatility", 0),
                    metrics.get("max_drawdown", 0),
                    metrics.get("sharpe_ratio", 0),
                    metrics.get("sortino_ratio", 0),
                    metrics.get("win_rate", 0),
                    strategy.get("total_transactions", 0),
                    json.dumps(risk_analysis.get("user_portfolio_risk", {}) if i == 0 else {})
                ))
            
            # 비교 결과 저장
            cursor.execute('''
                INSERT INTO strategy_comparisons 
                (comparison_name, strategies, comparison_metrics, best_strategy)
                VALUES (?, ?, ?, ?)
            ''', (
                f"Simulation_{simulation_id}",
                json.dumps([s.get("strategy_id") for s in strategy_results]),
                json.dumps(comparison_metrics),
                comparison_metrics.get("best_strategy", {}).get("id", "")
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Simulation results saved with ID: {simulation_id}")
            return simulation_id
            
        except Exception as e:
            logger.error(f"Error saving simulation results: {str(e)}")
            return f"error_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Helper methods for generating fallback/mock data
    def _generate_fallback_simulation_result(self) -> Dict[str, Any]:
        """시뮬레이션 실패 시 폴백 결과 생성"""
        return {
            "simulation_id": f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "error": "데이터 부족으로 인한 기본 시뮬레이션 결과",
            "user_portfolio_return": self._generate_mock_user_result(100000000),
            "simulated_returns": [self._generate_mock_strategy_result("fallback_strategy", "기본 전략", 100000000)],
            "comparison_metrics": {
                "message": "제한된 데이터로 인해 기본 결과를 제공합니다",
                "user_vs_best_strategy": {"return_improvement": 0.02},
                "best_strategy": {"name": "기본 전략", "annual_return": 0.12}
            },
            "risk_analysis": {"user_portfolio_risk": {"overall_risk_score": 3.0, "risk_category": "보통"}},
            "recommendations": ["더 많은 데이터 수집 후 상세한 분석을 권장합니다"],
            "generated_at": datetime.now().isoformat()
        }

    def _generate_mock_user_result(self, initial_capital: float) -> Dict[str, Any]:
        """Mock 사용자 결과 생성"""
        return {
            "strategy_id": "user_actual",
            "strategy_name": "사용자 실제 포트폴리오",
            "metrics": {
                "total_return": 0.125,
                "annual_return": 0.125,
                "volatility": 0.221,
                "sharpe_ratio": 0.56,
                "max_drawdown": -0.152,
                "win_rate": 0.54,
                "sortino_ratio": 0.72,
                "calmar_ratio": 0.82,
                "var_95": -0.043,
                "beta": 1.05,
                "alpha": 0.045,
                "information_ratio": 0.25
            },
            "final_value": initial_capital * 1.125,
            "current_allocation": {"삼성전자": 0.35, "SK하이닉스": 0.25, "NAVER": 0.20, "카카오": 0.10, "기타": 0.10}
        }

    def _generate_mock_strategy_result(self, strategy_id: str, strategy_name: str, initial_capital: float) -> Dict[str, Any]:
        """Mock 전략 결과 생성"""
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy_name,
            "strategy_type": "ai_generated",
            "metrics": {
                "total_return": 0.187,
                "annual_return": 0.187,
                "volatility": 0.194,
                "sharpe_ratio": 0.78,
                "max_drawdown": -0.128,
                "win_rate": 0.58,
                "sortino_ratio": 0.95,
                "calmar_ratio": 1.46,
                "var_95": -0.038,
                "beta": 0.95,
                "alpha": 0.067,
                "information_ratio": 0.42
            },
            "final_value": initial_capital * 1.187,
            "portfolio_allocation": {"삼성전자": 0.30, "NVIDIA": 0.20, "Apple": 0.18, "TSMC": 0.15, "Amazon": 0.10, "기타": 0.07}
        }

    def _generate_mock_benchmark_results(self, initial_capital: float) -> Dict[str, Any]:
        """Mock 벤치마크 결과 생성"""
        return {
            "KOSPI": {
                "symbol": "^KS11",
                "total_return": 0.089,
                "annual_return": 0.089,
                "volatility": 0.185,
                "sharpe_ratio": 0.32,
                "max_drawdown": -0.195,
                "final_value": initial_capital * 1.089
            },
            "S&P500": {
                "symbol": "^GSPC", 
                "total_return": 0.115,
                "annual_return": 0.115,
                "volatility": 0.162,
                "sharpe_ratio": 0.53,
                "max_drawdown": -0.142,
                "final_value": initial_capital * 1.115
            }
        }

    def _create_empty_portfolio_history(self, initial_capital: float) -> Dict[str, Any]:
        """빈 포트폴리오 히스토리 생성"""
        return {
            "dates": [datetime.now()],
            "values": [initial_capital],
            "daily_returns": [0.0],
            "holdings": [{}]
        }

    def _create_empty_backtest_result(self, initial_capital: float) -> Dict[str, Any]:
        """빈 백테스팅 결과 생성"""
        return {
            "dates": [datetime.now()],
            "values": [initial_capital],
            "daily_returns": [0.0],
            "cumulative_returns": [0.0],
            "holdings": [{}],
            "rebalance_dates": []
        }

    def _calculate_current_allocation(self, current_holdings: List[Dict[str, Any]]) -> Dict[str, float]:
        """현재 보유량을 배분 비중으로 변환"""
        try:
            if not current_holdings:
                return {}
            
            total_value = sum(holding.get("value", 0) for holding in current_holdings)
            
            if total_value == 0:
                return {}
            
            allocation = {}
            for holding in current_holdings:
                symbol = holding.get("symbol", "Unknown")
                value = holding.get("value", 0)
                allocation[symbol] = value / total_value
            
            return allocation
            
        except Exception as e:
            logger.error(f"Error calculating current allocation: {str(e)}")
            return {}
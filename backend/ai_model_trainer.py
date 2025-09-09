import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
import logging
import asyncio
import json
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
import PyPDF2
import io
import arxiv
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET
import re

# For AI model integration
try:
    import anthropic
    from anthropic import Anthropic
except ImportError:
    anthropic = None
    Anthropic = None

# For Ollama integration
try:
    import ollama
except ImportError:
    ollama = None

load_dotenv()
logger = logging.getLogger(__name__)

class AIModelTrainer:
    """
    AI 모델 학습 및 전략 생성 모듈
    Claude 모델을 활용한 리밸런싱 전략 생성
    다양한 학습 소스를 통한 AI 모델 미세 조정
    """
    
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # Ollama settings
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")  # Default free model
        
        if self.anthropic_api_key and Anthropic:
            self.client = Anthropic(api_key=self.anthropic_api_key)
        else:
            self.client = None
            logger.warning("Anthropic API key not found or anthropic package not installed")
            
        # Check Ollama availability
        self.ollama_available = self._check_ollama_availability()
        
        # Initialize knowledge base
        self.knowledge_base = {
            "web_content": [],
            "ebooks": [],
            "papers": [],
            "expert_strategies": [],
            "user_data": [],
            "simulation_results": []
        }
        
        # Initialize local database for expert strategies
        self.expert_db_path = "expert_strategies.db"
        self._init_expert_database()

    async def initialize(self):
        """비동기 초기화"""
        try:
            # 필요한 비동기 초기화 작업 수행
            logger.info("AI Model Trainer 비동기 초기화 시작")
            
            # 데이터베이스 연결 확인
            self._init_expert_database()
            
            # Database AI Engine 초기화 (Claude API 대신 우선 사용)
            try:
                from database_ai_engine import get_database_ai_engine
                await get_database_ai_engine()
                logger.info("✅ Database AI Engine 초기화 완료 - API 키 불필요")
            except Exception as e:
                logger.warning(f"Database AI Engine 초기화 실패: {e}")
            
            # Claude API는 보조적으로만 사용 (오류 로그 최소화)
            if self.client:
                logger.info("Claude API 사용 가능 (보조 분석용)")
            else:
                logger.info("Database AI Engine 단독 모드 - 완전 자립형 시스템")
            
            logger.info("AI Model Trainer 비동기 초기화 완료")
        except Exception as e:
            logger.error(f"AI Model Trainer 초기화 오류: {e}")
            # 초기화 실패해도 서버는 계속 실행

    def _init_expert_database(self):
        """전문가 전략 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.expert_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simulation_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER,
                    returns REAL,
                    volatility REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    feedback_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (strategy_id) REFERENCES expert_strategies (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            # Add some default expert strategies
            self._add_default_expert_strategies()
            
        except Exception as e:
            logger.error(f"Error initializing expert database: {str(e)}")

    def _add_default_expert_strategies(self):
        """기본 전문가 전략 추가"""
        default_strategies = [
            {
                "expert_name": "워런 버핏",
                "strategy_name": "가치 투자 전략",
                "investment_style": "conservative",
                "allocation": {
                    "삼성전자": 0.25,
                    "Apple": 0.20,
                    "Berkshire Hathaway": 0.15,
                    "Johnson & Johnson": 0.15,
                    "Coca-Cola": 0.10,
                    "Cash": 0.15
                },
                "rationale": "장기적인 관점에서 내재 가치가 높은 기업에 투자하여 안정적인 수익 추구",
                "performance_metrics": {"expected_return": 0.12, "volatility": 0.15, "sharpe_ratio": 0.8}
            },
            {
                "expert_name": "피터 린치",
                "strategy_name": "성장주 투자 전략",
                "investment_style": "aggressive",
                "allocation": {
                    "NVIDIA": 0.20,
                    "Tesla": 0.15,
                    "Amazon": 0.15,
                    "Microsoft": 0.15,
                    "삼성전자": 0.15,
                    "NAVER": 0.10,
                    "기타 성장주": 0.10
                },
                "rationale": "빠르게 성장하는 기업에 집중 투자하여 높은 수익률 추구",
                "performance_metrics": {"expected_return": 0.18, "volatility": 0.22, "sharpe_ratio": 0.82}
            },
            {
                "expert_name": "레이 달리오",
                "strategy_name": "올웨더 포트폴리오",
                "investment_style": "moderate",
                "allocation": {
                    "주식": 0.30,
                    "중기채권": 0.15,
                    "장기채권": 0.40,
                    "원자재": 0.075,
                    "REITs": 0.075
                },
                "rationale": "모든 경제 환경에서 안정적인 수익을 추구하는 분산 투자 전략",
                "performance_metrics": {"expected_return": 0.10, "volatility": 0.12, "sharpe_ratio": 0.83}
            }
        ]
        
        try:
            conn = sqlite3.connect(self.expert_db_path)
            cursor = conn.cursor()
            
            for strategy in default_strategies:
                cursor.execute('''
                    INSERT OR IGNORE INTO expert_strategies 
                    (expert_name, strategy_name, investment_style, allocation_json, rationale, performance_metrics)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    strategy["expert_name"],
                    strategy["strategy_name"],
                    strategy["investment_style"],
                    json.dumps(strategy["allocation"]),
                    strategy["rationale"],
                    json.dumps(strategy["performance_metrics"])
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding default expert strategies: {str(e)}")

    async def train_with_multiple_sources(
        self, 
        learning_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        다양한 소스를 통한 AI 모델 학습
        
        Args:
            learning_config: 학습 설정
            {
                "web_search_keywords": ["투자 전략", "포트폴리오 최적화"],
                "ebook_urls": ["url1", "url2"],
                "research_keywords": ["quantitative finance", "portfolio optimization"],
                "expert_strategies": [strategy_data],
                "user_data": {text, files, urls},
                "enable_simulation_learning": True
            }
        """
        try:
            logger.info("Starting multi-source AI training")
            training_results = {
                "web_learning": {},
                "ebook_learning": {},
                "paper_learning": {},
                "expert_learning": {},
                "user_data_learning": {},
                "simulation_learning": {}
            }
            
            # 1. 인터넷 검색을 통한 학습
            if learning_config.get("web_search_keywords"):
                training_results["web_learning"] = await self._learn_from_web_search(
                    learning_config["web_search_keywords"]
                )
            
            # 2. E-book 검색 및 학습
            if learning_config.get("ebook_urls"):
                training_results["ebook_learning"] = await self._learn_from_ebooks(
                    learning_config["ebook_urls"]
                )
            
            # 3. 논문 검색 및 학습
            if learning_config.get("research_keywords"):
                training_results["paper_learning"] = await self._learn_from_papers(
                    learning_config["research_keywords"]
                )
            
            # 4. 전문가 직접 입력 전략 학습
            if learning_config.get("expert_strategies"):
                training_results["expert_learning"] = await self._learn_from_expert_strategies(
                    learning_config["expert_strategies"]
                )
            
            # 5. 사용자 직접 입력 데이터 학습
            if learning_config.get("user_data"):
                training_results["user_data_learning"] = await self._learn_from_user_data(
                    learning_config["user_data"]
                )
            
            # 6. 모의 투자 데이터 기반 강화 학습
            if learning_config.get("enable_simulation_learning"):
                training_results["simulation_learning"] = await self._learn_from_simulation_feedback()
            
            # 통합 학습 결과 생성
            integrated_knowledge = self._integrate_learning_results(training_results)
            
            logger.info("Multi-source AI training completed")
            return {
                "status": "success",
                "training_results": training_results,
                "integrated_knowledge": integrated_knowledge,
                "trained_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in multi-source training: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "trained_at": datetime.now().isoformat()
            }

    async def _learn_from_web_search(self, keywords: List[str]) -> Dict[str, Any]:
        """인터넷 검색을 통한 학습"""
        try:
            web_insights = []
            
            for keyword in keywords:
                # Google Search API 사용
                if self.google_search_api_key:
                    search_results = await self._search_google_for_learning(keyword)
                    
                    for result in search_results:
                        # 웹 콘텐츠 추출 및 분석
                        content = await self._extract_web_content(result["url"])
                        if content and content.get("content"):
                            # Claude를 사용하여 콘텐츠 분석
                            analysis = await self._analyze_content_with_claude(
                                content["content"], 
                                f"투자 전략 관련 콘텐츠 분석: {keyword}"
                            )
                            
                            web_insights.append({
                                "keyword": keyword,
                                "url": result["url"],
                                "title": result["title"],
                                "analysis": analysis,
                                "extracted_at": datetime.now().isoformat()
                            })
                
                await asyncio.sleep(1)  # Rate limiting
            
            # 웹 학습 결과 저장
            self.knowledge_base["web_content"].extend(web_insights)
            
            return {
                "insights_count": len(web_insights),
                "keywords_processed": keywords,
                "key_learnings": self._extract_key_learnings(web_insights)
            }
            
        except Exception as e:
            logger.error(f"Error in web search learning: {str(e)}")
            return {"error": str(e)}

    async def _learn_from_ebooks(self, ebook_urls: List[str]) -> Dict[str, Any]:
        """E-book 검색 및 학습"""
        try:
            ebook_insights = []
            
            for url in ebook_urls:
                try:
                    # PDF나 텍스트 파일 다운로드 및 처리
                    content = await self._download_and_extract_ebook(url)
                    
                    if content:
                        # 책 내용을 청크로 나누어 분석
                        chunks = self._split_content_into_chunks(content, max_chunk_size=8000)
                        
                        for i, chunk in enumerate(chunks[:5]):  # 처음 5개 청크만 처리
                            analysis = await self._analyze_content_with_claude(
                                chunk,
                                "투자 전문서적 내용 분석 및 핵심 투자 원칙 추출"
                            )
                            
                            ebook_insights.append({
                                "url": url,
                                "chunk_index": i,
                                "analysis": analysis,
                                "processed_at": datetime.now().isoformat()
                            })
                    
                    await asyncio.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Failed to process ebook {url}: {str(e)}")
                    continue
            
            # E-book 학습 결과 저장
            self.knowledge_base["ebooks"].extend(ebook_insights)
            
            return {
                "insights_count": len(ebook_insights),
                "ebooks_processed": len(ebook_urls),
                "key_learnings": self._extract_key_learnings(ebook_insights)
            }
            
        except Exception as e:
            logger.error(f"Error in ebook learning: {str(e)}")
            return {"error": str(e)}

    async def _learn_from_papers(self, research_keywords: List[str]) -> Dict[str, Any]:
        """논문 검색 및 학습"""
        try:
            paper_insights = []
            
            for keyword in research_keywords:
                try:
                    # arXiv API를 사용하여 논문 검색
                    papers = await self._search_arxiv_papers(keyword)
                    
                    for paper in papers[:3]:  # 키워드당 최대 3편
                        # 논문 요약 분석
                        analysis = await self._analyze_content_with_claude(
                            paper["summary"],
                            f"금융 연구 논문 분석: {keyword} 관련 학술 연구 내용 요약 및 실용적 투자 전략 도출"
                        )
                        
                        paper_insights.append({
                            "keyword": keyword,
                            "title": paper["title"],
                            "authors": paper["authors"],
                            "summary": paper["summary"],
                            "url": paper["url"],
                            "analysis": analysis,
                            "processed_at": datetime.now().isoformat()
                        })
                
                except Exception as e:
                    logger.warning(f"Failed to process paper for keyword {keyword}: {str(e)}")
                    continue
                
                await asyncio.sleep(1)  # Rate limiting
            
            # 논문 학습 결과 저장
            self.knowledge_base["papers"].extend(paper_insights)
            
            return {
                "insights_count": len(paper_insights),
                "keywords_processed": research_keywords,
                "key_learnings": self._extract_key_learnings(paper_insights)
            }
            
        except Exception as e:
            logger.error(f"Error in paper learning: {str(e)}")
            return {"error": str(e)}

    async def _learn_from_expert_strategies(self, expert_strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """전문가 직접 입력 전략 학습"""
        try:
            processed_count = 0
            
            conn = sqlite3.connect(self.expert_db_path)
            cursor = conn.cursor()
            
            for strategy in expert_strategies:
                try:
                    cursor.execute('''
                        INSERT INTO expert_strategies 
                        (expert_name, strategy_name, investment_style, allocation_json, rationale, performance_metrics)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        strategy.get("expert_name", "Unknown"),
                        strategy.get("strategy_name", "Custom Strategy"),
                        strategy.get("investment_style", "moderate"),
                        json.dumps(strategy.get("allocation", {})),
                        strategy.get("rationale", ""),
                        json.dumps(strategy.get("performance_metrics", {}))
                    ))
                    processed_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to process expert strategy: {str(e)}")
                    continue
            
            conn.commit()
            conn.close()
            
            # 전문가 전략 학습 결과 저장
            self.knowledge_base["expert_strategies"].extend(expert_strategies)
            
            return {
                "strategies_processed": processed_count,
                "total_strategies": len(expert_strategies),
                "success_rate": processed_count / len(expert_strategies) if expert_strategies else 0
            }
            
        except Exception as e:
            logger.error(f"Error in expert strategy learning: {str(e)}")
            return {"error": str(e)}

    async def _learn_from_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 직접 입력 데이터 학습"""
        try:
            user_insights = []
            
            # 텍스트 데이터 처리
            if user_data.get("text"):
                text_analysis = await self._analyze_content_with_claude(
                    user_data["text"],
                    "사용자 투자 철학 및 선호도 분석, 개인화된 투자 전략 요소 추출"
                )
                user_insights.append({
                    "type": "text",
                    "content": user_data["text"],
                    "analysis": text_analysis,
                    "processed_at": datetime.now().isoformat()
                })
            
            # PDF 파일 처리
            if user_data.get("pdf_files"):
                for pdf_content in user_data["pdf_files"]:
                    pdf_text = self._extract_text_from_pdf(pdf_content)
                    if pdf_text:
                        pdf_analysis = await self._analyze_content_with_claude(
                            pdf_text[:8000],  # 처음 8000자만 분석
                            "사용자 제공 PDF 문서 분석 및 투자 관련 인사이트 추출"
                        )
                        user_insights.append({
                            "type": "pdf",
                            "content": pdf_text[:1000],  # 요약용
                            "analysis": pdf_analysis,
                            "processed_at": datetime.now().isoformat()
                        })
            
            # URL 콘텐츠 처리
            if user_data.get("urls"):
                for url in user_data["urls"]:
                    url_content = await self._extract_web_content(url)
                    if url_content and url_content.get("content"):
                        url_analysis = await self._analyze_content_with_claude(
                            url_content["content"][:8000],
                            "사용자 제공 웹사이트 콘텐츠 분석 및 투자 전략 관련 내용 추출"
                        )
                        user_insights.append({
                            "type": "url",
                            "url": url,
                            "content": url_content["content"][:1000],
                            "analysis": url_analysis,
                            "processed_at": datetime.now().isoformat()
                        })
            
            # 사용자 데이터 학습 결과 저장
            self.knowledge_base["user_data"].extend(user_insights)
            
            return {
                "insights_generated": len(user_insights),
                "data_types_processed": list(set(insight["type"] for insight in user_insights)),
                "key_learnings": self._extract_key_learnings(user_insights)
            }
            
        except Exception as e:
            logger.error(f"Error in user data learning: {str(e)}")
            return {"error": str(e)}

    async def _learn_from_simulation_feedback(self) -> Dict[str, Any]:
        """모의 투자 데이터 기반 강화 학습"""
        try:
            conn = sqlite3.connect(self.expert_db_path)
            cursor = conn.cursor()
            
            # 시뮬레이션 피드백 데이터 조회
            cursor.execute('''
                SELECT es.*, sf.returns, sf.volatility, sf.sharpe_ratio, sf.max_drawdown, sf.feedback_score
                FROM expert_strategies es
                JOIN simulation_feedback sf ON es.id = sf.strategy_id
                ORDER BY sf.feedback_score DESC
            ''')
            
            feedback_data = cursor.fetchall()
            conn.close()
            
            if not feedback_data:
                return {"message": "No simulation feedback data available"}
            
            # 성과가 좋은 전략들 분석
            top_strategies = feedback_data[:5]  # 상위 5개 전략
            
            performance_analysis = []
            for strategy in top_strategies:
                strategy_dict = {
                    "strategy_name": strategy[2],
                    "investment_style": strategy[3],
                    "allocation": json.loads(strategy[4]),
                    "returns": strategy[7],
                    "volatility": strategy[8],
                    "sharpe_ratio": strategy[9],
                    "max_drawdown": strategy[10],
                    "feedback_score": strategy[11]
                }
                performance_analysis.append(strategy_dict)
            
            # Claude를 사용하여 성공 패턴 분석
            patterns_analysis = await self._analyze_content_with_claude(
                json.dumps(performance_analysis, indent=2),
                "성공한 투자 전략들의 공통 패턴 분석 및 향후 전략 개선 방향 제시"
            )
            
            # 강화 학습 결과 저장
            self.knowledge_base["simulation_results"].append({
                "top_strategies": performance_analysis,
                "patterns_analysis": patterns_analysis,
                "analyzed_at": datetime.now().isoformat()
            })
            
            return {
                "strategies_analyzed": len(feedback_data),
                "top_performers": len(top_strategies),
                "patterns_identified": patterns_analysis,
                "improvement_suggestions": "Based on historical performance data"
            }
            
        except Exception as e:
            logger.error(f"Error in simulation feedback learning: {str(e)}")
            return {"error": str(e)}

    async def generate_strategy(
        self, 
        processed_data: pd.DataFrame,
        user_profile: Dict[str, Any],
        user_uploaded_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        전처리된 데이터를 바탕으로 최적의 리밸런싱 전략 생성
        
        Args:
            processed_data: data_processor.py에서 생성된 데이터프레임
            user_profile: 사용자 입력 정보 (투자 성향, 목표 수익률, 투자 기간 등)
            user_uploaded_data: 사용자가 업로드한 문서, URL 등의 데이터
            
        Returns:
            rebalancing_strategy: 리밸런싱 전략 (JSON 형식)
            portfolio_allocation: 목표 포트폴리오 자산 배분 비중
            actions: 추천 매수/매도 종목 및 수량
            rationale: AI가 해당 전략을 제안한 이유에 대한 설명
        """
        try:
            logger.info("Generating comprehensive AI rebalancing strategy")
            
            # 1. 사용자 업로드 데이터 처리 (있는 경우)
            user_insights = {}
            if user_uploaded_data:
                user_insights = await self._learn_from_user_data(user_uploaded_data)
            
            # 2. 종합 컨텍스트 준비
            comprehensive_context = await self._prepare_comprehensive_context(
                processed_data, user_profile, user_insights
            )
            
            # 3. AI 전략 생성 (Database AI 우선)
            try:
                from database_ai_engine import get_database_ai_engine
                db_ai = await get_database_ai_engine()
                
                # 현재 보유종목 변환
                current_holdings = []
                if not processed_data.empty:
                    for _, row in processed_data.iterrows():
                        current_holdings.append({
                            'symbol': row.get('Symbol', ''),
                            'name': row.get('Name', ''),
                            'weight': row.get('Weight', 0.0) / 100.0 if 'Weight' in row else 0.0
                        })
                
                # Database AI로 전략 생성
                strategy = await db_ai.generate_intelligent_strategy(
                    user_profile, 
                    current_holdings,
                    {'market_data': processed_data.to_dict('records') if not processed_data.empty else []}
                )
                
                logger.info("✅ Database AI 전략 생성 성공")
                
            except Exception as db_ai_error:
                logger.warning(f"Database AI 실패, 기존 방식 사용: {db_ai_error}")
                
                # 기존 방식 폴백 (무료 LLM 우선, Claude 보조)
                try:
                    if self.ollama_available:
                        logger.info("🤖 Ollama 무료 LLM으로 전략 생성 중...")
                        strategy = await self._generate_strategy_with_ollama(comprehensive_context)
                    elif self.client:
                        logger.info("🧠 Claude API로 전략 생성 중...")
                        strategy = await self._generate_advanced_strategy_with_claude(comprehensive_context)
                    else:
                        logger.info("📊 규칙 기반 전략 생성 중...")
                        strategy = await self._generate_enhanced_rule_based_strategy(
                            processed_data, user_profile, user_insights
                        )
                except Exception as ai_error:
                    logger.warning(f"AI 전략 생성 실패, 규칙 기반으로 폴백: {ai_error}")
                    strategy = await self._generate_enhanced_rule_based_strategy(
                        processed_data, user_profile, user_insights
                    )
            
            # 4. 전략 검증 및 최적화
            validated_strategy = await self._validate_and_optimize_strategy(strategy, processed_data)
            
            # 5. 리스크 분석 추가
            risk_analysis = await self._perform_risk_analysis(validated_strategy, processed_data)
            validated_strategy["risk_analysis"] = risk_analysis
            
            logger.info("Advanced AI strategy generation completed")
            return validated_strategy
            
        except Exception as e:
            logger.error(f"Error generating advanced strategy: {str(e)}")
            return self._generate_fallback_strategy(user_profile)

    async def _prepare_comprehensive_context(
        self, 
        processed_data: pd.DataFrame,
        user_profile: Dict[str, Any],
        user_insights: Dict[str, Any]
    ) -> str:
        """종합적인 컨텍스트 준비"""
        try:
            context_parts = []
            
            # 1. 사용자 프로필
            context_parts.append("=== 투자자 프로필 ===")
            context_parts.append(f"투자 성향: {user_profile.get('investment_style', 'moderate')}")
            context_parts.append(f"목표 수익률: {user_profile.get('target_return', '10-15%')}")
            context_parts.append(f"투자 기간: {user_profile.get('investment_period', 'medium')}")
            context_parts.append(f"위험 허용도: {user_profile.get('risk_tolerance', 'medium')}")
            context_parts.append(f"투자 목적: {user_profile.get('investment_goal', 'wealth_building')}")
            
            # 2. 시장 데이터 분석
            if not processed_data.empty:
                context_parts.append("\n=== 시장 데이터 분석 ===")
                
                # 최신 시장 상황
                latest_data = processed_data.groupby('Symbol').tail(1)
                for _, row in latest_data.head(10).iterrows():  # 상위 10개 종목
                    symbol = row.get('Symbol', 'Unknown')
                    price = row.get('Close', 0)
                    daily_return = row.get('Daily_Return', 0) * 100
                    volatility = row.get('Volatility_30D', 0) * 100
                    rsi = row.get('RSI', 50)
                    
                    context_parts.append(
                        f"{symbol}: 현재가 {price:.2f}, 일일수익률 {daily_return:.2f}%, "
                        f"변동성 {volatility:.2f}%, RSI {rsi:.1f}"
                    )
                
                # 시장 트렌드 분석
                context_parts.append("\n시장 트렌드:")
                market_trend = self._analyze_market_trend(processed_data)
                context_parts.append(market_trend)
            
            # 3. 지식 베이스 활용
            context_parts.append("\n=== 학습된 투자 지식 ===")
            
            # 웹 학습 내용
            if self.knowledge_base["web_content"]:
                recent_web_insights = self.knowledge_base["web_content"][-3:]  # 최근 3개
                context_parts.append("최신 웹 분석 결과:")
                for insight in recent_web_insights:
                    if insight.get("analysis"):
                        context_parts.append(f"- {insight['analysis'][:200]}...")
            
            # 전문가 전략
            expert_strategies = self._get_relevant_expert_strategies(user_profile.get('investment_style', 'moderate'))
            if expert_strategies:
                context_parts.append("관련 전문가 전략:")
                for strategy in expert_strategies[:2]:  # 상위 2개
                    context_parts.append(f"- {strategy['expert_name']}: {strategy['rationale'][:150]}...")
            
            # 4. 사용자 개인화 데이터
            if user_insights and user_insights.get("key_learnings"):
                context_parts.append("\n=== 사용자 맞춤 분석 ===")
                for learning in user_insights["key_learnings"][:3]:
                    context_parts.append(f"- {learning}")
            
            # 5. 시뮬레이션 학습 결과
            if self.knowledge_base["simulation_results"]:
                latest_simulation = self.knowledge_base["simulation_results"][-1]
                context_parts.append("\n=== 성과 분석 기반 인사이트 ===")
                context_parts.append(latest_simulation.get("patterns_identified", "")[:300])
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error preparing comprehensive context: {str(e)}")
            return "기본 컨텍스트를 사용합니다."

    async def _generate_advanced_strategy_with_claude(self, context: str) -> Dict[str, Any]:
        """Claude를 사용한 고도화된 전략 생성"""
        try:
            prompt = f"""
당신은 세계 최고 수준의 투자 전문가입니다. 다음 종합 정보를 바탕으로 최적의 포트폴리오 리밸런싱 전략을 제안해주세요.

{context}

다음 형식으로 구체적이고 실행 가능한 전략을 제안해주세요:

1. **추천 포트폴리오 비중** (JSON 형식으로 정확한 종목명과 비중):
{{
    "삼성전자": 0.25,
    "Apple": 0.20,
    "NVIDIA": 0.15,
    ...
}}

2. **매수/매도 액션 리스트**:
- 매수: [종목명] - [이유] - [목표비중]
- 매도: [종목명] - [이유] - [현재비중 → 목표비중]

3. **전략 핵심 근거**:
- 시장 상황 분석
- 사용자 프로필 부합성
- 리스크 관리 방안

4. **성과 예측**:
- 예상 연수익률: [범위]
- 예상 변동성: [수치]
- 최대 손실 가능성: [MDD]

5. **구체적 실행 계획**:
- 단계별 리밸런싱 방법
- 모니터링 지표
- 재조정 시점

응답은 한국어로, 전문적이면서도 이해하기 쉽게 작성해주세요.
"""
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            ai_response = response.content[0].text
            strategy = self._parse_advanced_ai_response(ai_response)
            
            logger.info("Successfully generated advanced strategy with Claude")
            return strategy
            
        except Exception as e:
            logger.error(f"Error with advanced Claude API: {str(e)}")
            raise
            
    def _check_ollama_availability(self) -> bool:
        """Ollama 서비스 가용성 체크"""
        try:
            if not ollama:
                logger.info("Ollama package not installed")
                return False
                
            # Simple health check
            import requests
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama service is available")
                return True
            else:
                logger.warning(f"Ollama service returned status {response.status_code}")
                return False
        except Exception as e:
            logger.info(f"Ollama not available: {str(e)}")
            return False
    
    async def _generate_strategy_with_ollama(self, context: str) -> Dict[str, Any]:
        """무료 Ollama LLM을 사용한 전략 생성"""
        try:
            if not self.ollama_available:
                raise Exception("Ollama is not available")
                
            prompt = f"""당신은 전문 투자 분석가입니다. 다음 정보를 바탕으로 실용적인 포트폴리오 리밸런싱 전략을 제안해주세요.

{context}

다음 형식으로 응답해주세요:

**추천 포트폴리오 비중**
- 삼성전자: 25%
- Apple: 20%  
- NVIDIA: 15%
- 기타...

**주요 액션**
- 매수: [종목명] - [이유]
- 매도: [종목명] - [이유]

**전략 근거**
- 현재 시장 상황 분석
- 사용자 프로필에 맞는 이유
- 리스크 관리 방안

**성과 예측**
- 예상 연수익률: 10-15%
- 예상 변동성: 15-20%
- 최대 손실: 10-15%

한국어로 구체적이고 실행 가능한 조언을 해주세요."""

            # Call Ollama API
            import requests
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 2000
                    }
                },
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
                
            result = response.json()
            ai_response = result.get("response", "")
            
            if not ai_response:
                raise Exception("Empty response from Ollama")
                
            # Parse the response
            strategy = self._parse_ollama_response(ai_response)
            
            logger.info("Successfully generated strategy with Ollama")
            return strategy
            
        except Exception as e:
            logger.error(f"Error with Ollama API: {str(e)}")
            # Fallback to rule-based strategy
            raise
    
    def _parse_ollama_response(self, ai_response: str) -> Dict[str, Any]:
        """Ollama 응답 파싱"""
        try:
            # Extract portfolio allocation
            portfolio_allocation = {}
            lines = ai_response.split('\n')
            
            in_portfolio_section = False
            for line in lines:
                line = line.strip()
                
                if "추천 포트폴리오" in line or "포트폴리오 비중" in line:
                    in_portfolio_section = True
                    continue
                elif "주요 액션" in line or "전략 근거" in line:
                    in_portfolio_section = False
                    continue
                    
                if in_portfolio_section and line and ":" in line:
                    parts = line.replace("-", "").strip().split(":")
                    if len(parts) == 2:
                        stock = parts[0].strip()
                        weight_str = parts[1].strip().replace("%", "").replace(" ", "")
                        try:
                            weight = float(weight_str) / 100.0
                            if 0 <= weight <= 1:
                                portfolio_allocation[stock] = weight
                        except ValueError:
                            continue
            
            # Extract actions
            actions = self._extract_actions_from_response(ai_response)
            
            # Extract rationale
            rationale = self._extract_rationale(ai_response)
            
            # Extract performance predictions
            performance = self._extract_performance_predictions(ai_response)
            
            return {
                "portfolio_allocation": portfolio_allocation,
                "actions": actions,
                "rationale": rationale,
                "expected_return": performance.get("return", "10-15%"),
                "expected_volatility": performance.get("volatility", "15-20%"),
                "max_drawdown": performance.get("mdd", "10-15%"),
                "risk_level": self._determine_risk_level(portfolio_allocation),
                "generated_at": datetime.now().isoformat(),
                "strategy_type": "ollama_free"
            }
            
        except Exception as e:
            logger.error(f"Error parsing Ollama response: {str(e)}")
            return self._create_fallback_parsed_response(ai_response)

    def _parse_advanced_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """고도화된 AI 응답 파싱"""
        try:
            # JSON 패턴 추출
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, ai_response)
            
            portfolio_allocation = {}
            if json_matches:
                try:
                    portfolio_allocation = json.loads(json_matches[0])
                except json.JSONDecodeError:
                    # 수동 파싱 시도
                    portfolio_allocation = self._manual_parse_allocation(json_matches[0])
            
            # 액션 추출
            actions = self._extract_actions_from_response(ai_response)
            
            # 성과 예측 추출
            performance = self._extract_performance_predictions(ai_response)
            
            # 전략 근거 추출
            rationale = self._extract_rationale(ai_response)
            
            return {
                "portfolio_allocation": portfolio_allocation,
                "actions": actions,
                "rationale": rationale,
                "expected_return": performance.get("return", "10-15%"),
                "expected_volatility": performance.get("volatility", "15-20%"),
                "max_drawdown": performance.get("mdd", "10-15%"),
                "risk_level": self._determine_risk_level(portfolio_allocation),
                "implementation_plan": self._extract_implementation_plan(ai_response),
                "monitoring_indicators": self._extract_monitoring_indicators(ai_response),
                "generated_at": datetime.now().isoformat(),
                "strategy_type": "ai_advanced"
            }
            
        except Exception as e:
            logger.error(f"Error parsing advanced AI response: {str(e)}")
            return self._create_fallback_parsed_response(ai_response)

    def _manual_parse_allocation(self, json_text: str) -> Dict[str, float]:
        """수동으로 포트폴리오 배분 파싱"""
        allocation = {}
        lines = json_text.split('\n')
        
        for line in lines:
            if ':' in line and any(char.isdigit() for char in line):
                parts = line.split(':')
                if len(parts) == 2:
                    stock = parts[0].strip().replace('"', '').replace('{', '').replace(',', '')
                    weight_str = parts[1].strip().replace('"', '').replace('}', '').replace(',', '')
                    
                    try:
                        weight = float(weight_str)
                        if weight > 1:  # 백분율로 표시된 경우
                            weight = weight / 100
                        allocation[stock] = weight
                    except ValueError:
                        continue
        
        return allocation

    def _extract_actions_from_response(self, response: str) -> List[Dict[str, Any]]:
        """응답에서 액션 추출"""
        actions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(('매수:', '- 매수:', '매도:', '- 매도:')):
                action_type = "매수" if "매수" in line else "매도"
                
                # 종목명과 이유 추출 (간단한 파싱)
                parts = line.replace('매수:', '').replace('매도:', '').replace('- ', '').split(' - ')
                
                if parts:
                    stock = parts[0].strip()
                    reason = parts[1] if len(parts) > 1 else "AI 추천"
                    target_weight = parts[2] if len(parts) > 2 else "적정 비중"
                    
                    actions.append({
                        "action": action_type,
                        "stock": stock,
                        "reason": reason,
                        "target_weight": target_weight
                    })
        
        return actions

    def _extract_performance_predictions(self, response: str) -> Dict[str, str]:
        """성과 예측 추출"""
        performance = {}
        lines = response.split('\n')
        
        for line in lines:
            line = line.lower()
            if '수익률' in line and '%' in line:
                performance["return"] = self._extract_percentage_from_line(line)
            elif '변동성' in line and '%' in line:
                performance["volatility"] = self._extract_percentage_from_line(line)
            elif 'mdd' in line or '최대' in line and '손실' in line:
                performance["mdd"] = self._extract_percentage_from_line(line)
        
        return performance

    def _extract_percentage_from_line(self, line: str) -> str:
        """라인에서 퍼센트 추출"""
        import re
        percentages = re.findall(r'\d+(?:\.\d+)?%', line)
        if percentages:
            return percentages[0]
        
        # 범위 패턴 찾기 (예: 10-15%)
        range_pattern = re.findall(r'\d+(?:\.\d+)?-\d+(?:\.\d+)?%', line)
        if range_pattern:
            return range_pattern[0]
        
        return "정보 없음"

    def _extract_rationale(self, response: str) -> str:
        """전략 근거 추출"""
        lines = response.split('\n')
        rationale_section = False
        rationale_lines = []
        
        for line in lines:
            if '근거' in line or '이유' in line or '전략' in line:
                rationale_section = True
                continue
            elif rationale_section and line.strip():
                if line.startswith(('4.', '5.', '#')):  # 다음 섹션 시작
                    break
                rationale_lines.append(line.strip())
        
        return ' '.join(rationale_lines) if rationale_lines else response[:500]

    def _extract_implementation_plan(self, response: str) -> List[str]:
        """실행 계획 추출"""
        lines = response.split('\n')
        plan_section = False
        plan_items = []
        
        for line in lines:
            if '실행' in line or '구체적' in line:
                plan_section = True
                continue
            elif plan_section and line.strip():
                if line.startswith('-') or line.strip().startswith('•'):
                    plan_items.append(line.strip())
                elif not line[0].isdigit() and not line.startswith('-'):
                    break
        
        return plan_items

    def _extract_monitoring_indicators(self, response: str) -> List[str]:
        """모니터링 지표 추출"""
        indicators = []
        if '모니터링' in response:
            lines = response.split('\n')
            monitoring_section = False
            
            for line in lines:
                if '모니터링' in line:
                    monitoring_section = True
                    continue
                elif monitoring_section and line.strip():
                    if line.startswith('-') or '지표' in line:
                        indicators.append(line.strip())
        
        # 기본 지표들
        if not indicators:
            indicators = [
                "월별 성과 검토",
                "포트폴리오 리밸런싱 (분기별)",
                "리스크 지표 모니터링",
                "시장 상황 변화 추적"
            ]
        
        return indicators

    def _determine_risk_level(self, portfolio_allocation: Dict[str, float]) -> str:
        """포트폴리오 위험 수준 결정"""
        if not portfolio_allocation:
            return "중간"
        
        # 고위험 자산 비중 계산
        high_risk_assets = ["Tesla", "NVIDIA", "비트코인", "성장주", "신흥시장"]
        high_risk_weight = sum(
            weight for stock, weight in portfolio_allocation.items()
            if any(risk_asset in stock for risk_asset in high_risk_assets)
        )
        
        if high_risk_weight > 0.4:
            return "높음"
        elif high_risk_weight > 0.2:
            return "중간"
        else:
            return "낮음"

    async def _generate_enhanced_rule_based_strategy(
        self, 
        processed_data: pd.DataFrame,
        user_profile: Dict[str, Any],
        user_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """강화된 규칙 기반 전략 (AI 백업용)"""
        try:
            investment_style = user_profile.get('investment_style', 'moderate')
            target_return = user_profile.get('target_return', 'moderate')
            
            # 기본 자산 배분
            base_allocations = {
                'conservative': {
                    "삼성전자": 0.20, "Apple": 0.15, "Microsoft": 0.10,
                    "Johnson & Johnson": 0.10, "Coca-Cola": 0.10,
                    "채권ETF": 0.25, "현금": 0.10
                },
                'moderate': {
                    "삼성전자": 0.18, "Apple": 0.15, "Microsoft": 0.12,
                    "NVIDIA": 0.12, "Amazon": 0.08, "Google": 0.08,
                    "NAVER": 0.08, "SK하이닉스": 0.10, "채권ETF": 0.09
                },
                'aggressive': {
                    "NVIDIA": 0.20, "Tesla": 0.15, "Apple": 0.12,
                    "Amazon": 0.10, "삼성전자": 0.13, "TSMC": 0.10,
                    "NAVER": 0.08, "성장주ETF": 0.12
                }
            }
            
            # 시장 상황에 따른 조정
            if not processed_data.empty:
                market_adjustment = self._calculate_market_adjustment(processed_data)
                allocation = self._adjust_allocation_for_market(
                    base_allocations[investment_style], 
                    market_adjustment
                )
            else:
                allocation = base_allocations[investment_style]
            
            # 사용자 인사이트 반영
            if user_insights and user_insights.get("key_learnings"):
                allocation = self._adjust_for_user_insights(allocation, user_insights)
            
            # 액션 생성
            actions = self._generate_rebalancing_actions(allocation)
            
            return {
                "portfolio_allocation": allocation,
                "actions": actions,
                "rationale": f"{investment_style} 성향 기반 최적화된 포트폴리오 전략",
                "expected_return": self._calculate_expected_return(allocation),
                "expected_volatility": self._calculate_expected_volatility(allocation),
                "risk_level": investment_style,
                "generated_at": datetime.now().isoformat(),
                "strategy_type": "enhanced_rule_based"
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced rule-based strategy: {str(e)}")
            return self._generate_fallback_strategy(user_profile)

    def _calculate_market_adjustment(self, processed_data: pd.DataFrame) -> Dict[str, float]:
        """시장 상황 분석 및 조정 계수 계산"""
        try:
            # 전체 시장 트렌드 계산
            market_returns = processed_data.groupby('Symbol')['Daily_Return'].mean()
            market_volatility = processed_data.groupby('Symbol')['Volatility_30D'].mean()
            
            # RSI 기반 과매수/과매도 판단
            avg_rsi = processed_data.groupby('Symbol')['RSI'].last().mean()
            
            # 조정 계수 계산
            adjustment = {
                "growth_bias": 1.1 if market_returns.mean() > 0.005 else 0.9,  # 상승장이면 성장주 비중 증가
                "defensive_bias": 1.1 if avg_rsi > 70 else 0.9,  # 과매수시 방어주 비중 증가
                "volatility_factor": 0.9 if market_volatility.mean() > 0.03 else 1.0
            }
            
            return adjustment
            
        except Exception as e:
            logger.error(f"Error calculating market adjustment: {str(e)}")
            return {"growth_bias": 1.0, "defensive_bias": 1.0, "volatility_factor": 1.0}

    def _adjust_allocation_for_market(
        self, 
        base_allocation: Dict[str, float], 
        adjustment: Dict[str, float]
    ) -> Dict[str, float]:
        """시장 상황을 반영한 배분 조정"""
        adjusted_allocation = base_allocation.copy()
        
        growth_stocks = ["NVIDIA", "Tesla", "Amazon", "성장주ETF"]
        defensive_stocks = ["Johnson & Johnson", "Coca-Cola", "채권ETF", "현금"]
        
        for stock in adjusted_allocation:
            if any(growth in stock for growth in growth_stocks):
                adjusted_allocation[stock] *= adjustment["growth_bias"]
            elif any(defensive in stock for defensive in defensive_stocks):
                adjusted_allocation[stock] *= adjustment["defensive_bias"]
            
            adjusted_allocation[stock] *= adjustment["volatility_factor"]
        
        # 정규화하여 총합이 1이 되도록 조정
        total = sum(adjusted_allocation.values())
        if total > 0:
            adjusted_allocation = {k: v/total for k, v in adjusted_allocation.items()}
        
        return adjusted_allocation

    def _adjust_for_user_insights(
        self, 
        allocation: Dict[str, float], 
        user_insights: Dict[str, Any]
    ) -> Dict[str, float]:
        """사용자 인사이트를 반영한 배분 조정"""
        # 사용자의 선호도나 특별한 요구사항 반영
        # 이 부분은 실제로는 더 복잡한 NLP 분석을 통해 구현될 것
        
        key_learnings = user_insights.get("key_learnings", [])
        
        for learning in key_learnings:
            learning_lower = learning.lower()
            
            # ESG 투자 선호
            if 'esg' in learning_lower or '지속가능' in learning_lower:
                allocation["Apple"] = allocation.get("Apple", 0) * 1.2
                allocation["Microsoft"] = allocation.get("Microsoft", 0) * 1.2
            
            # 기술주 선호
            if '기술' in learning_lower or 'tech' in learning_lower:
                allocation["NVIDIA"] = allocation.get("NVIDIA", 0) * 1.3
                allocation["Apple"] = allocation.get("Apple", 0) * 1.2
            
            # 안정성 중시
            if '안정' in learning_lower or '보수' in learning_lower:
                allocation["채권ETF"] = allocation.get("채권ETF", 0) * 1.3
                allocation["현금"] = allocation.get("현금", 0) * 1.2
        
        # 정규화
        total = sum(allocation.values())
        if total > 0:
            allocation = {k: v/total for k, v in allocation.items()}
        
        return allocation

    def _generate_rebalancing_actions(self, target_allocation: Dict[str, float]) -> List[Dict[str, Any]]:
        """리밸런싱 액션 생성"""
        actions = []
        
        for stock, target_weight in target_allocation.items():
            if target_weight > 0.05:  # 5% 이상인 종목만
                actions.append({
                    "action": "매수" if target_weight > 0.1 else "소량매수",
                    "stock": stock,
                    "target_weight": target_weight,
                    "reason": f"목표 비중 {target_weight:.1%} 달성을 위한 조정",
                    "priority": "high" if target_weight > 0.15 else "medium"
                })
        
        return sorted(actions, key=lambda x: x["target_weight"], reverse=True)

    def _calculate_expected_return(self, allocation: Dict[str, float]) -> str:
        """포트폴리오 예상 수익률 계산"""
        # 간단한 추정 모델 (실제로는 더 정교한 모델 사용)
        expected_returns = {
            "NVIDIA": 0.25, "Tesla": 0.22, "Apple": 0.15, "Microsoft": 0.14,
            "Amazon": 0.18, "Google": 0.16, "삼성전자": 0.12, "SK하이닉스": 0.15,
            "NAVER": 0.10, "TSMC": 0.18, "채권ETF": 0.04, "현금": 0.02
        }
        
        weighted_return = 0
        for stock, weight in allocation.items():
            stock_return = expected_returns.get(stock, 0.10)  # 기본값 10%
            weighted_return += weight * stock_return
        
        lower_bound = max(0.05, weighted_return - 0.03)
        upper_bound = weighted_return + 0.03
        
        return f"{lower_bound:.1%}-{upper_bound:.1%}"

    def _calculate_expected_volatility(self, allocation: Dict[str, float]) -> str:
        """포트폴리오 예상 변동성 계산"""
        # 간단한 추정 모델
        volatilities = {
            "NVIDIA": 0.35, "Tesla": 0.40, "Apple": 0.25, "Microsoft": 0.22,
            "Amazon": 0.28, "Google": 0.24, "삼성전자": 0.20, "SK하이닉스": 0.25,
            "NAVER": 0.22, "TSMC": 0.30, "채권ETF": 0.05, "현금": 0.01
        }
        
        weighted_volatility = 0
        for stock, weight in allocation.items():
            stock_vol = volatilities.get(stock, 0.20)  # 기본값 20%
            weighted_volatility += weight * (stock_vol ** 2)
        
        portfolio_volatility = np.sqrt(weighted_volatility)
        
        return f"{portfolio_volatility:.1%}"

    async def _validate_and_optimize_strategy(
        self, 
        strategy: Dict[str, Any], 
        processed_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """전략 검증 및 최적화"""
        try:
            # 1. 배분 합계 검증
            allocation = strategy.get("portfolio_allocation", {})
            total_weight = sum(allocation.values())
            
            if abs(total_weight - 1.0) > 0.01:  # 1% 오차 허용
                # 정규화
                normalized_allocation = {k: v/total_weight for k, v in allocation.items()} if total_weight > 0 else allocation
                strategy["portfolio_allocation"] = normalized_allocation
                strategy["validation_notes"] = [f"포트폴리오 비중 정규화 완료 (원래 합계: {total_weight:.2%})"]
            
            # 2. 최소/최대 비중 제한
            optimized_allocation = {}
            for stock, weight in strategy["portfolio_allocation"].items():
                # 최소 1%, 최대 30% 제한
                optimized_weight = max(0.01, min(0.30, weight))
                optimized_allocation[stock] = optimized_weight
            
            # 3. 재정규화
            total_optimized = sum(optimized_allocation.values())
            strategy["portfolio_allocation"] = {k: v/total_optimized for k, v in optimized_allocation.items()}
            
            # 4. 다양성 점수 계산
            diversification_score = len([w for w in strategy["portfolio_allocation"].values() if w > 0.05])
            strategy["diversification_score"] = diversification_score
            
            # 5. 최적화 노트 추가
            optimization_notes = strategy.get("validation_notes", [])
            optimization_notes.append(f"다양성 점수: {diversification_score} (5% 이상 종목 수)")
            
            if diversification_score < 5:
                optimization_notes.append("권장: 더 많은 종목으로 분산 투자 고려")
            
            strategy["validation_notes"] = optimization_notes
            strategy["validated_at"] = datetime.now().isoformat()
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error validating strategy: {str(e)}")
            return strategy

    async def _perform_risk_analysis(
        self, 
        strategy: Dict[str, Any], 
        processed_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """리스크 분석 수행"""
        try:
            allocation = strategy.get("portfolio_allocation", {})
            
            # 1. 집중도 리스크
            max_weight = max(allocation.values()) if allocation else 0
            concentration_risk = "높음" if max_weight > 0.25 else "보통" if max_weight > 0.15 else "낮음"
            
            # 2. 섹터 집중도
            tech_weight = sum(
                weight for stock, weight in allocation.items()
                if any(tech in stock for tech in ["Apple", "NVIDIA", "Microsoft", "Amazon", "Google", "NAVER", "삼성전자"])
            )
            sector_concentration = "높음" if tech_weight > 0.6 else "보통" if tech_weight > 0.4 else "낮음"
            
            # 3. 유동성 리스크 (간단한 추정)
            liquid_weight = sum(
                weight for stock, weight in allocation.items()
                if any(liquid in stock for liquid in ["Apple", "Microsoft", "삼성전자", "NVIDIA"])
            )
            liquidity_risk = "낮음" if liquid_weight > 0.5 else "보통"
            
            # 4. 통화 리스크
            foreign_weight = sum(
                weight for stock, weight in allocation.items()
                if not any(korean in stock for korean in ["삼성", "SK", "NAVER", "카카오", "현대"])
            )
            currency_risk = "높음" if foreign_weight > 0.7 else "보통" if foreign_weight > 0.4 else "낮음"
            
            # 5. 전체 리스크 스코어
            risk_scores = {
                "높음": 3, "보통": 2, "낮음": 1
            }
            
            total_risk_score = (
                risk_scores[concentration_risk] + 
                risk_scores[sector_concentration] + 
                risk_scores[liquidity_risk] + 
                risk_scores[currency_risk]
            ) / 4
            
            overall_risk = "높음" if total_risk_score > 2.5 else "보통" if total_risk_score > 1.5 else "낮음"
            
            return {
                "concentration_risk": concentration_risk,
                "max_position_weight": f"{max_weight:.1%}",
                "sector_concentration": sector_concentration,
                "tech_sector_weight": f"{tech_weight:.1%}",
                "liquidity_risk": liquidity_risk,
                "currency_risk": currency_risk,
                "foreign_exposure": f"{foreign_weight:.1%}",
                "overall_risk_level": overall_risk,
                "risk_score": round(total_risk_score, 2),
                "risk_mitigation_suggestions": [
                    "정기적인 리밸런싱 (분기별 권장)" if concentration_risk == "높음" else None,
                    "섹터 분산 확대 고려" if sector_concentration == "높음" else None,
                    "환헤지 전략 검토" if currency_risk == "높음" else None
                ]
            }
            
        except Exception as e:
            logger.error(f"Error performing risk analysis: {str(e)}")
            return {
                "overall_risk_level": "보통",
                "error": "리스크 분석 중 오류 발생"
            }

    # Helper methods for data processing
    async def _search_google_for_learning(self, keyword: str) -> List[Dict[str, Any]]:
        """Google Search API for learning purposes"""
        if not self.google_search_api_key:
            return []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_search_api_key,
                'cx': self.google_search_engine_id,
                'q': f"{keyword} 투자 전략 분석 2024",
                'num': 5,
                'lr': 'lang_ko'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [
                            {
                                'title': item.get('title', ''),
                                'url': item.get('link', ''),
                                'snippet': item.get('snippet', '')
                            }
                            for item in data.get('items', [])
                        ]
            return []
            
        except Exception as e:
            logger.error(f"Error in Google search: {str(e)}")
            return []

    async def _extract_web_content(self, url: str) -> Optional[Dict[str, Any]]:
        """웹 콘텐츠 추출"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.extract()
                        
                        text = soup.get_text()
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        clean_text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return {
                            "url": url,
                            "content": clean_text[:8000],  # 처음 8000자
                            "title": soup.find('title').get_text() if soup.find('title') else ""
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting web content from {url}: {str(e)}")
            return None

    async def _download_and_extract_ebook(self, url: str) -> Optional[str]:
        """E-book 다운로드 및 텍스트 추출"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # PDF인 경우 텍스트 추출
                        if url.lower().endswith('.pdf'):
                            return self._extract_text_from_pdf_bytes(content)
                        else:
                            # 일반 텍스트로 처리
                            return content.decode('utf-8', errors='ignore')
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading ebook from {url}: {str(e)}")
            return None

    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """PDF에서 텍스트 추출"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages[:10]:  # 처음 10페이지만
                text += page.extract_text() + "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""

    def _extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """PDF 바이트에서 텍스트 추출"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages[:10]:  # 처음 10페이지만
                text += page.extract_text() + "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting PDF bytes text: {str(e)}")
            return ""

    async def _search_arxiv_papers(self, keyword: str) -> List[Dict[str, Any]]:
        """arXiv 논문 검색"""
        try:
            search = arxiv.Search(
                query=f"all:{keyword} AND cat:q-fin*",
                max_results=5,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            papers = []
            for result in search.results():
                papers.append({
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "url": result.entry_id,
                    "published": result.published.isoformat()
                })
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv papers: {str(e)}")
            return []

    async def _analyze_content_with_claude(self, content: str, analysis_prompt: str) -> str:
        """Claude를 사용한 콘텐츠 분석"""
        if not self.client:
            return "AI 분석 서비스를 사용할 수 없습니다."
        
        try:
            prompt = f"""
다음 콘텐츠를 분석해주세요:

{analysis_prompt}

콘텐츠:
{content[:6000]}

핵심 투자 인사이트와 실용적인 전략을 3-5개 문장으로 요약해주세요.
"""
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error analyzing content with Claude: {str(e)}")
            return f"콘텐츠 분석 중 오류: {str(e)}"

    def _split_content_into_chunks(self, content: str, max_chunk_size: int = 8000) -> List[str]:
        """콘텐츠를 청크로 분할"""
        chunks = []
        current_chunk = ""
        
        sentences = content.split('. ')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _extract_key_learnings(self, insights: List[Dict[str, Any]]) -> List[str]:
        """인사이트에서 핵심 학습 내용 추출"""
        key_learnings = []
        
        for insight in insights[-5:]:  # 최근 5개
            analysis = insight.get("analysis", "")
            if analysis and len(analysis) > 50:
                # 첫 번째 문장 또는 핵심 포인트 추출
                first_sentence = analysis.split('.')[0] + '.'
                if len(first_sentence) > 20:
                    key_learnings.append(first_sentence)
        
        return key_learnings

    def _get_relevant_expert_strategies(self, investment_style: str) -> List[Dict[str, Any]]:
        """관련 전문가 전략 조회"""
        try:
            conn = sqlite3.connect(self.expert_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT expert_name, strategy_name, rationale, allocation_json, performance_metrics
                FROM expert_strategies 
                WHERE investment_style = ? OR investment_style = 'moderate'
                ORDER BY created_at DESC
                LIMIT 5
            ''', (investment_style,))
            
            results = cursor.fetchall()
            conn.close()
            
            strategies = []
            for result in results:
                strategies.append({
                    "expert_name": result[0],
                    "strategy_name": result[1],
                    "rationale": result[2],
                    "allocation": json.loads(result[3]) if result[3] else {},
                    "performance_metrics": json.loads(result[4]) if result[4] else {}
                })
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting expert strategies: {str(e)}")
            return []

    def _analyze_market_trend(self, processed_data: pd.DataFrame) -> str:
        """시장 트렌드 분석"""
        try:
            if processed_data.empty:
                return "시장 데이터가 충분하지 않습니다."
            
            # 전체 시장 평균 수익률
            avg_return = processed_data['Daily_Return'].mean()
            avg_volatility = processed_data['Volatility_30D'].mean()
            
            # RSI 평균
            avg_rsi = processed_data['RSI'].mean()
            
            # 트렌드 판단
            if avg_return > 0.01:
                trend = "강한 상승"
            elif avg_return > 0.005:
                trend = "상승"
            elif avg_return > -0.005:
                trend = "횡보"
            else:
                trend = "하락"
            
            volatility_level = "높음" if avg_volatility > 0.03 else "보통" if avg_volatility > 0.02 else "낮음"
            market_sentiment = "과매수" if avg_rsi > 70 else "과매도" if avg_rsi < 30 else "중립"
            
            return f"시장 트렌드: {trend}, 변동성: {volatility_level}, 심리: {market_sentiment}"
            
        except Exception as e:
            logger.error(f"Error analyzing market trend: {str(e)}")
            return "시장 분석 중 오류가 발생했습니다."

    def _integrate_learning_results(self, training_results: Dict[str, Any]) -> Dict[str, Any]:
        """학습 결과 통합"""
        integrated = {
            "total_insights": 0,
            "learning_sources": [],
            "key_themes": [],
            "confidence_score": 0.0
        }
        
        for source, results in training_results.items():
            if isinstance(results, dict) and not results.get("error"):
                if "insights_count" in results:
                    integrated["total_insights"] += results["insights_count"]
                    integrated["learning_sources"].append(source)
                
                if "key_learnings" in results:
                    integrated["key_themes"].extend(results["key_learnings"][:2])
        
        # 신뢰도 점수 계산 (간단한 휴리스틱)
        integrated["confidence_score"] = min(1.0, integrated["total_insights"] / 20)
        
        return integrated

    def _generate_fallback_strategy(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """폴백 전략 생성"""
        investment_style = user_profile.get('investment_style', 'moderate')
        
        fallback_allocations = {
            'conservative': {
                "삼성전자": 0.25, "Apple": 0.20, "Microsoft": 0.15,
                "Johnson & Johnson": 0.10, "채권ETF": 0.20, "현금": 0.10
            },
            'moderate': {
                "삼성전자": 0.20, "Apple": 0.18, "Microsoft": 0.15,
                "NVIDIA": 0.12, "Amazon": 0.10, "Google": 0.10,
                "NAVER": 0.08, "채권ETF": 0.07
            },
            'aggressive': {
                "NVIDIA": 0.22, "Tesla": 0.18, "Apple": 0.15,
                "Amazon": 0.12, "삼성전자": 0.13, "TSMC": 0.10,
                "성장주ETF": 0.10
            }
        }
        
        allocation = fallback_allocations.get(investment_style, fallback_allocations['moderate'])
        
        return {
            "portfolio_allocation": allocation,
            "actions": [
                {
                    "action": "검토",
                    "stock": "전체 포트폴리오",
                    "reason": "기본 전략 적용, 전문가 상담 권장"
                }
            ],
            "rationale": f"{investment_style} 성향에 맞춘 기본 포트폴리오 전략입니다. AI 분석이 제한적이므로 전문가와의 상담을 권장합니다.",
            "expected_return": "8-12%" if investment_style == 'conservative' else "12-18%",
            "risk_level": investment_style,
            "generated_at": datetime.now().isoformat(),
            "strategy_type": "fallback",
            "warning": "제한된 분석으로 생성된 기본 전략입니다."
        }

    def _create_fallback_parsed_response(self, ai_response: str) -> Dict[str, Any]:
        """AI 응답 파싱 실패시 폴백 응답 생성"""
        return {
            "portfolio_allocation": {
                "삼성전자": 0.20,
                "Apple": 0.15,
                "Microsoft": 0.12,
                "NVIDIA": 0.10,
                "Amazon": 0.10,
                "Google": 0.08,
                "NAVER": 0.08,
                "채권ETF": 0.10,
                "현금": 0.07
            },
            "actions": [
                {
                    "action": "검토",
                    "stock": "AI 응답 파싱",
                    "reason": "AI 응답 처리 중 오류 발생"
                }
            ],
            "rationale": f"AI 응답: {ai_response[:300]}...",
            "expected_return": "10-15%",
            "expected_volatility": "15-20%",
            "risk_level": "중간",
            "generated_at": datetime.now().isoformat(),
            "strategy_type": "ai_parsed_fallback",
            "parsing_error": True
        }
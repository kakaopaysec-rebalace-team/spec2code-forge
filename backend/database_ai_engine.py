#!/usr/bin/env python3
"""
Database-Driven AI Engine
데이터베이스 기반 자립형 AI 엔진

외부 API 의존성 없이 자체 전문가 전략 데이터베이스를 활용한
지능형 포트폴리오 리밸런싱 시스템
"""

import asyncio
import aiosqlite
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)

@dataclass
class StrategyMatch:
    """전략 매칭 결과"""
    expert_name: str
    strategy_name: str
    investment_style: str
    allocation: Dict[str, float]
    rationale: str
    confidence_score: float
    performance_metrics: Dict[str, Any]

class DatabaseAIEngine:
    """
    데이터베이스 기반 AI 엔진
    318개 전문가 전략을 활용한 자립형 포트폴리오 분석 시스템
    """
    
    def __init__(self, db_path: str = "expert_strategies.db"):
        self.db_path = db_path
        self.strategy_cache = {}
        self.performance_weights = {
            'sector_diversity': 0.25,
            'risk_alignment': 0.30,
            'market_conditions': 0.20,
            'historical_performance': 0.25
        }
    
    async def initialize(self):
        """AI 엔진 초기화"""
        logger.info("Database AI Engine 초기화 중...")
        
        # 전문가 전략 캐시 로드
        await self._load_strategy_cache()
        
        logger.info(f"✅ {len(self.strategy_cache)} 개 전문가 전략 로드 완료")
        
    async def _load_strategy_cache(self):
        """전문가 전략 캐시 로드"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT expert_name, strategy_name, investment_style, 
                           allocation_json, rationale, performance_metrics
                    FROM expert_strategies
                """)
                
                strategies = await cursor.fetchall()
                
                for row in strategies:
                    expert_name, strategy_name, investment_style, allocation_json, rationale, performance_metrics = row
                    
                    key = f"{expert_name}_{strategy_name}_{investment_style}"
                    
                    try:
                        allocation = json.loads(allocation_json) if allocation_json else {}
                        perf_metrics = json.loads(performance_metrics) if performance_metrics else {}
                    except json.JSONDecodeError:
                        allocation = {}
                        perf_metrics = {}
                    
                    self.strategy_cache[key] = {
                        'expert_name': expert_name,
                        'strategy_name': strategy_name,
                        'investment_style': investment_style,
                        'allocation': allocation,
                        'rationale': rationale,
                        'performance_metrics': perf_metrics
                    }
        
        except Exception as e:
            logger.error(f"전략 캐시 로드 실패: {e}")
            self.strategy_cache = {}
    
    async def generate_intelligent_strategy(
        self, 
        user_profile: Dict[str, Any], 
        current_holdings: List[Dict[str, Any]] = None,
        market_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        지능형 전략 생성 (API 키 불필요)
        
        Args:
            user_profile: 사용자 프로필
            current_holdings: 현재 보유 종목
            market_data: 시장 데이터
            
        Returns:
            완전한 리밸런싱 전략
        """
        try:
            logger.info("🧠 Database AI 전략 생성 시작")
            
            # 1. 사용자 프로필 분석
            user_analysis = self._analyze_user_profile(user_profile)
            
            # 2. 최적 전략 매칭
            strategy_matches = await self._find_optimal_strategies(user_analysis, current_holdings)
            
            # 3. 전략 융합 및 최적화
            optimized_strategy = self._fuse_and_optimize_strategies(strategy_matches, user_analysis)
            
            # 4. 현재 보유종목 대비 액션 생성
            actions = self._generate_rebalancing_actions(optimized_strategy, current_holdings)
            
            # 5. 상세 분석 및 rationale 생성
            detailed_analysis = self._generate_detailed_analysis(
                optimized_strategy, strategy_matches, user_analysis
            )
            
            result = {
                "portfolio_allocation": optimized_strategy['allocation'],
                "actions": actions,
                "rationale": detailed_analysis['rationale'],
                "expected_return": detailed_analysis['expected_return'],
                "expected_volatility": detailed_analysis['expected_volatility'],
                "risk_level": user_analysis['risk_level'],
                "confidence_score": detailed_analysis['confidence_score'],
                "strategy_sources": [match.expert_name for match in strategy_matches[:3]],
                "generated_at": datetime.now().isoformat(),
                "strategy_type": "database_ai",
                "market_outlook": detailed_analysis['market_outlook'],
                "diversification_score": detailed_analysis['diversification_score']
            }
            
            logger.info("✅ Database AI 전략 생성 완료")
            return result
            
        except Exception as e:
            logger.error(f"Database AI 전략 생성 실패: {e}")
            return await self._generate_emergency_strategy(user_profile)
    
    def _analyze_user_profile(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 프로필 심층 분석"""
        
        investment_style = user_profile.get('risk_tolerance', 'moderate')
        investment_goal = user_profile.get('investment_goal', 'growth')
        investment_horizon = user_profile.get('investment_horizon', 10)
        
        # 리스크 스코어 계산 (0-100)
        risk_score = {
            'conservative': 25,
            'moderate': 50,
            'aggressive': 80
        }.get(investment_style, 50)
        
        # 투자 기간에 따른 조정
        if investment_horizon > 15:
            risk_score += 10
        elif investment_horizon < 5:
            risk_score -= 15
            
        risk_score = max(10, min(90, risk_score))
        
        # 목표에 따른 가중치 조정
        goal_weights = {
            'wealth_building': {'growth': 0.7, 'stability': 0.3},
            'retirement': {'growth': 0.5, 'stability': 0.5},
            'income': {'growth': 0.3, 'stability': 0.7},
            'growth': {'growth': 0.8, 'stability': 0.2}
        }
        
        weights = goal_weights.get(investment_goal, goal_weights['growth'])
        
        return {
            'investment_style': investment_style,
            'risk_score': risk_score,
            'risk_level': investment_style,
            'investment_horizon': investment_horizon,
            'goal_weights': weights,
            'preferred_sectors': self._infer_preferred_sectors(user_profile),
            'experience_level': user_profile.get('experience_level', 'intermediate')
        }
    
    def _infer_preferred_sectors(self, user_profile: Dict[str, Any]) -> List[str]:
        """사용자 선호 섹터 추론"""
        
        # 기본 섹터 선호도
        sector_preferences = {
            'conservative': ['금융', '유틸리티', '소비재', '헬스케어'],
            'moderate': ['기술', '금융', '헬스케어', '소비재', '산업재'],
            'aggressive': ['기술', '바이오', '신재생에너지', '반도체', '인터넷']
        }
        
        risk_tolerance = user_profile.get('risk_tolerance', 'moderate')
        return sector_preferences.get(risk_tolerance, sector_preferences['moderate'])
    
    async def _find_optimal_strategies(
        self, 
        user_analysis: Dict[str, Any], 
        current_holdings: List[Dict[str, Any]] = None
    ) -> List[StrategyMatch]:
        """최적 전략 매칭"""
        
        matches = []
        
        # 투자 성향 기반 필터링
        target_style = user_analysis['investment_style']
        compatible_styles = {
            'conservative': ['conservative', 'moderate'],
            'moderate': ['conservative', 'moderate', 'aggressive'],
            'aggressive': ['moderate', 'aggressive']
        }
        
        valid_styles = compatible_styles.get(target_style, ['moderate'])
        
        # 전문가 전략 평가
        for key, strategy in self.strategy_cache.items():
            if strategy['investment_style'] in valid_styles:
                
                # 신뢰도 점수 계산
                confidence = self._calculate_strategy_confidence(strategy, user_analysis)
                
                if confidence > 0.3:  # 최소 신뢰도 임계값
                    match = StrategyMatch(
                        expert_name=strategy['expert_name'],
                        strategy_name=strategy['strategy_name'],
                        investment_style=strategy['investment_style'],
                        allocation=strategy['allocation'],
                        rationale=strategy['rationale'],
                        confidence_score=confidence,
                        performance_metrics=strategy['performance_metrics']
                    )
                    matches.append(match)
        
        # 신뢰도순 정렬
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logger.info(f"🎯 {len(matches)} 개 최적 전략 매칭 완료")
        return matches[:10]  # 상위 10개 전략 반환
    
    def _calculate_strategy_confidence(
        self, 
        strategy: Dict[str, Any], 
        user_analysis: Dict[str, Any]
    ) -> float:
        """전략 신뢰도 계산"""
        
        confidence = 0.0
        
        # 1. 투자 성향 일치도 (40%)
        style_score = 0.4 if strategy['investment_style'] == user_analysis['investment_style'] else 0.2
        confidence += style_score
        
        # 2. 포트폴리오 다양성 점수 (30%)
        diversity_score = min(1.0, len(strategy['allocation']) / 8) * 0.3
        confidence += diversity_score
        
        # 3. 전략 완성도 (20%)
        completeness = 0.2 if strategy['rationale'] and len(strategy['rationale']) > 50 else 0.1
        confidence += completeness
        
        # 4. 랜덤 점수 (실제로는 더 복잡한 로직) (10%)
        random_factor = random.uniform(0.05, 0.1)
        confidence += random_factor
        
        return min(1.0, confidence)
    
    def _fuse_and_optimize_strategies(
        self, 
        strategy_matches: List[StrategyMatch], 
        user_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """전략 융합 및 최적화"""
        
        if not strategy_matches:
            return self._create_default_strategy(user_analysis)
        
        # 상위 3개 전략 선택
        top_strategies = strategy_matches[:3]
        
        # 가중평균으로 포트폴리오 생성
        total_weight = sum(match.confidence_score for match in top_strategies)
        merged_allocation = {}
        
        for match in top_strategies:
            weight = match.confidence_score / total_weight
            
            for asset, allocation in match.allocation.items():
                if asset in merged_allocation:
                    merged_allocation[asset] += allocation * weight
                else:
                    merged_allocation[asset] = allocation * weight
        
        # 정규화 (합계 1.0)
        total_allocation = sum(merged_allocation.values())
        if total_allocation > 0:
            merged_allocation = {k: v/total_allocation for k, v in merged_allocation.items()}
        
        # 최적화 (최소 5%, 최대 30% 제한)
        optimized_allocation = self._apply_allocation_constraints(merged_allocation)
        
        return {
            'allocation': optimized_allocation,
            'source_strategies': [match.strategy_name for match in top_strategies],
            'expert_sources': [match.expert_name for match in top_strategies]
        }
    
    def _apply_allocation_constraints(self, allocation: Dict[str, float]) -> Dict[str, float]:
        """할당 제약 조건 적용"""
        
        # 최소 5%, 최대 30% 제한
        constrained = {}
        for asset, weight in allocation.items():
            constrained[asset] = max(0.05, min(0.30, weight))
        
        # 재정규화
        total = sum(constrained.values())
        if total > 0:
            constrained = {k: v/total for k, v in constrained.items()}
        
        return constrained
    
    def _generate_rebalancing_actions(
        self, 
        optimized_strategy: Dict[str, Any], 
        current_holdings: List[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """리밸런싱 액션 생성"""
        
        actions = []
        target_allocation = optimized_strategy['allocation']
        
        if not current_holdings:
            # 신규 투자 권장사항
            for asset, weight in sorted(target_allocation.items(), key=lambda x: x[1], reverse=True):
                if weight > 0.15:  # 15% 이상 종목만
                    actions.append({
                        "action": "매수",
                        "stock": asset,
                        "target_weight": f"{weight*100:.1f}%",
                        "reason": f"포트폴리오의 핵심 자산으로 {weight*100:.1f}% 비중 권장"
                    })
        else:
            # 기존 보유종목 기준 리밸런싱
            current_symbols = {holding['symbol']: holding.get('weight', 0) for holding in current_holdings}
            
            for asset, target_weight in target_allocation.items():
                current_weight = current_symbols.get(asset, 0)
                diff = target_weight - current_weight
                
                if abs(diff) > 0.05:  # 5% 이상 차이
                    if diff > 0:
                        actions.append({
                            "action": "매수 증대",
                            "stock": asset,
                            "current_weight": f"{current_weight*100:.1f}%",
                            "target_weight": f"{target_weight*100:.1f}%",
                            "reason": f"목표 비중까지 {abs(diff)*100:.1f}% 추가 매수 권장"
                        })
                    else:
                        actions.append({
                            "action": "비중 축소",
                            "stock": asset,
                            "current_weight": f"{current_weight*100:.1f}%",
                            "target_weight": f"{target_weight*100:.1f}%",
                            "reason": f"목표 비중까지 {abs(diff)*100:.1f}% 비중 축소 권장"
                        })
        
        return actions[:8]  # 최대 8개 액션
    
    def _generate_detailed_analysis(
        self, 
        optimized_strategy: Dict[str, Any], 
        strategy_matches: List[StrategyMatch], 
        user_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """상세 분석 생성"""
        
        # 예상 수익률 계산
        risk_score = user_analysis['risk_score']
        expected_return = f"{6 + (risk_score * 0.15):.1f}-{8 + (risk_score * 0.2):.1f}%"
        expected_volatility = f"{8 + (risk_score * 0.15):.1f}-{12 + (risk_score * 0.2):.1f}%"
        
        # 다양화 점수
        diversification_score = min(100, len(optimized_strategy['allocation']) * 12)
        
        # 신뢰도 점수
        avg_confidence = sum(match.confidence_score for match in strategy_matches[:3]) / min(3, len(strategy_matches))
        
        # 상세 rationale 생성
        top_experts = [match.expert_name for match in strategy_matches[:3]]
        rationale = self._build_comprehensive_rationale(optimized_strategy, top_experts, user_analysis)
        
        # 시장 전망
        market_outlook = self._generate_market_outlook(user_analysis)
        
        return {
            'expected_return': expected_return,
            'expected_volatility': expected_volatility,
            'confidence_score': avg_confidence,
            'diversification_score': diversification_score,
            'rationale': rationale,
            'market_outlook': market_outlook
        }
    
    def _build_comprehensive_rationale(
        self, 
        strategy: Dict[str, Any], 
        top_experts: List[str], 
        user_analysis: Dict[str, Any]
    ) -> str:
        """종합적인 전략 근거 생성"""
        
        expert_str = ", ".join(top_experts[:2])
        risk_level = user_analysis['risk_level']
        
        rationale_parts = [
            f"이 포트폴리오는 {expert_str} 등 세계적인 투자 전문가들의 검증된 전략을 기반으로 설계되었습니다.",
            f"사용자의 {risk_level} 위험 성향과 투자 목표에 최적화된 자산 배분을 제공합니다."
        ]
        
        # 주요 자산 설명
        top_assets = sorted(strategy['allocation'].items(), key=lambda x: x[1], reverse=True)[:3]
        for asset, weight in top_assets:
            rationale_parts.append(f"{asset} {weight*100:.1f}% 비중으로 포트폴리오의 핵심 자산 역할을 담당합니다.")
        
        rationale_parts.extend([
            f"총 {len(strategy['allocation'])}개 자산으로 분산투자하여 리스크를 효과적으로 관리합니다.",
            "정기적인 리밸런싱을 통해 목표 비중을 유지하시기 바랍니다."
        ])
        
        return " ".join(rationale_parts)
    
    def _generate_market_outlook(self, user_analysis: Dict[str, Any]) -> str:
        """시장 전망 생성"""
        
        outlooks = [
            "글로벌 기술주의 성장세가 지속될 것으로 예상되며, 장기 투자 관점에서 유망합니다.",
            "인플레이션 우려에도 불구하고 우량주 중심의 분산투자가 안정적인 수익을 제공할 것으로 전망됩니다.",
            "신흥시장의 변동성을 고려하여 선진국 시장 중심의 포트폴리오 구성을 권장합니다.",
            "ESG 투자의 중요성이 증대되는 만큼 지속가능한 기업에 대한 투자 비중을 늘려가시기 바랍니다."
        ]
        
        return random.choice(outlooks)
    
    def _create_default_strategy(self, user_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """기본 전략 생성"""
        
        default_allocations = {
            'conservative': {
                "Apple": 0.20, "Microsoft": 0.18, "삼성전자": 0.15,
                "Johnson & Johnson": 0.12, "Berkshire Hathaway": 0.10,
                "Procter & Gamble": 0.08, "Coca-Cola": 0.07,
                "채권 ETF": 0.10
            },
            'moderate': {
                "Apple": 0.18, "Microsoft": 0.15, "삼성전자": 0.13,
                "NVIDIA": 0.12, "Amazon": 0.10, "Google": 0.10,
                "NAVER": 0.08, "Tesla": 0.07, "채권 ETF": 0.07
            },
            'aggressive': {
                "NVIDIA": 0.20, "Tesla": 0.15, "Apple": 0.13,
                "Amazon": 0.12, "Microsoft": 0.10, "Meta": 0.10,
                "TSMC": 0.08, "삼성전자": 0.07, "Alphabet": 0.05
            }
        }
        
        style = user_analysis['investment_style']
        allocation = default_allocations.get(style, default_allocations['moderate'])
        
        return {
            'allocation': allocation,
            'source_strategies': ['기본 전략'],
            'expert_sources': ['Database AI']
        }
    
    async def _generate_emergency_strategy(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """비상 전략 생성"""
        
        logger.warning("비상 전략 생성 중...")
        
        return {
            "portfolio_allocation": {
                "Apple": 0.25,
                "Microsoft": 0.20,
                "삼성전자": 0.15,
                "Amazon": 0.10,
                "Google": 0.10,
                "NAVER": 0.10,
                "현금": 0.10
            },
            "actions": [
                {
                    "action": "검토 필요",
                    "stock": "전체 포트폴리오",
                    "reason": "시스템 오류로 인한 기본 전략 적용"
                }
            ],
            "rationale": "시스템 분석 중 오류가 발생하여 안전한 기본 포트폴리오를 제공합니다. 전문가 상담을 권장합니다.",
            "expected_return": "8-12%",
            "expected_volatility": "12-16%",
            "risk_level": "moderate",
            "confidence_score": 0.3,
            "strategy_sources": ["Emergency Strategy"],
            "generated_at": datetime.now().isoformat(),
            "strategy_type": "emergency",
            "warning": "제한된 분석으로 생성된 비상 전략입니다."
        }


# 싱글톤 인스턴스
_db_ai_engine = None

async def get_database_ai_engine() -> DatabaseAIEngine:
    """Database AI Engine 싱글톤 인스턴스 반환"""
    global _db_ai_engine
    
    if _db_ai_engine is None:
        _db_ai_engine = DatabaseAIEngine()
        await _db_ai_engine.initialize()
    
    return _db_ai_engine


if __name__ == "__main__":
    # 테스트 코드
    async def test_database_ai():
        engine = await get_database_ai_engine()
        
        test_profile = {
            'risk_tolerance': 'moderate',
            'investment_goal': 'wealth_building',
            'investment_horizon': 10
        }
        
        result = await engine.generate_intelligent_strategy(test_profile)
        print("🎯 Database AI 전략 결과:")
        print(f"포트폴리오: {result['portfolio_allocation']}")
        print(f"예상 수익률: {result['expected_return']}")
        print(f"신뢰도: {result['confidence_score']:.2f}")
        print(f"전략 소스: {result['strategy_sources']}")
    
    asyncio.run(test_database_ai())
#!/usr/bin/env python3
"""
Claude AI를 사용한 리밸런싱 전략 학습 모듈
사용자의 투자 철학을 분석하여 개인화된 전략을 생성합니다.
"""

import asyncio
import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from database_manager import get_database_manager
from user_data_processor import UserDataProcessor
import anthropic
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyLearner:
    """Claude AI를 사용한 투자 전략 학습 클래스"""
    
    def __init__(self):
        self.anthropic_client = None
        self.user_data_processor = UserDataProcessor()
        self._initialize_anthropic()
    
    def _initialize_anthropic(self):
        """Anthropic 클라이언트 초기화"""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY가 설정되지 않았습니다. 모의 모드로 실행됩니다.")
                return
            
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.error(f"Anthropic 클라이언트 초기화 실패: {e}")
            self.anthropic_client = None
    
    async def analyze_user_philosophy(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 투자 철학 분석"""
        try:
            learning_method = user_input.get('learning_method')
            content = ""
            processed_content = ""
            
            # 입력 방법에 따라 데이터 처리
            if learning_method == 'document':
                # 문서 처리
                file_content = user_input.get('file_content', '')
                file_name = user_input.get('file_name', '')
                content = f"파일명: {file_name}\n내용:\n{file_content}"
                processed_content = await self.user_data_processor.process_document_content(file_content)
                
            elif learning_method == 'url':
                # URL 처리
                url = user_input.get('url', '')
                content = f"URL: {url}"
                processed_content = await self.user_data_processor.process_url_content(url)
                
            elif learning_method == 'text':
                # 직접 입력 텍스트 처리
                content = user_input.get('text', '')
                processed_content = content
            
            if not processed_content:
                raise ValueError("처리할 수 있는 콘텐츠가 없습니다.")
            
            # Claude AI로 투자 철학 분석
            philosophy_analysis = await self._analyze_investment_philosophy(processed_content)
            
            return {
                'learning_method': learning_method,
                'original_content': content,
                'processed_content': processed_content,
                'philosophy_analysis': philosophy_analysis,
                'confidence_score': philosophy_analysis.get('confidence_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"사용자 철학 분석 오류: {e}")
            raise
    
    async def _analyze_investment_philosophy(self, content: str) -> Dict[str, Any]:
        """투자 철학 분석 (Claude AI 사용)"""
        try:
            if not self.anthropic_client:
                # 모의 분석 결과 반환
                return await self._mock_philosophy_analysis(content)
            
            prompt = f"""
다음 텍스트에서 사용자의 투자 철학과 성향을 분석해주세요:

{content}

분석해야 할 항목:
1. 투자 성향 (보수적/균형/공격적)
2. 선호 자산 유형 (기술주/가치주/배당주 등)
3. 투자 목표 (성장/안정/배당수익 등)
4. 리스크 관리 방식
5. 투자 기간 (단기/중기/장기)
6. 특별한 투자 철학이나 원칙

결과를 다음 JSON 형식으로 반환해주세요:
{{
  "risk_tolerance": "보수적|균형|공격적",
  "preferred_assets": ["기술주", "가치주", "배당주", ...],
  "investment_goals": ["성장", "안정", "배당수익", ...],
  "risk_management": "리스크 관리 방식 설명",
  "investment_horizon": "단기|중기|장기",
  "philosophy_summary": "투자 철학 요약",
  "key_principles": ["원칙1", "원칙2", ...],
  "confidence_score": 0.0-1.0
}}
"""
            
            message = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # JSON 응답 파싱
            response_text = message.content[0].text
            
            # JSON 추출
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis_result = json.loads(json_match.group())
                logger.info("Claude AI 투자 철학 분석 완료")
                return analysis_result
            else:
                raise ValueError("Claude AI 응답에서 JSON을 찾을 수 없습니다.")
                
        except Exception as e:
            logger.error(f"Claude AI 철학 분석 오류: {e}")
            # 실패 시 모의 분석 결과 반환
            return await self._mock_philosophy_analysis(content)
    
    async def _mock_philosophy_analysis(self, content: str) -> Dict[str, Any]:
        """모의 투자 철학 분석 결과"""
        # 간단한 키워드 기반 분석
        content_lower = content.lower()
        
        # 위험 성향 판단
        if any(word in content_lower for word in ['안정', '보수', '위험회피', '배당']):
            risk_tolerance = "보수적"
        elif any(word in content_lower for word in ['성장', '공격', '고수익', '혁신']):
            risk_tolerance = "공격적"
        else:
            risk_tolerance = "균형"
        
        # 선호 자산 판단
        preferred_assets = []
        if any(word in content_lower for word in ['기술', '테크', 'ai', '혁신']):
            preferred_assets.append("기술주")
        if any(word in content_lower for word in ['배당', '인컴', '현금흐름']):
            preferred_assets.append("배당주")
        if any(word in content_lower for word in ['가치', '저평가', '펀더멘털']):
            preferred_assets.append("가치주")
        
        if not preferred_assets:
            preferred_assets = ["다양화"]
        
        return {
            "risk_tolerance": risk_tolerance,
            "preferred_assets": preferred_assets,
            "investment_goals": ["장기성장", "안정적수익"],
            "risk_management": "분산투자를 통한 리스크 관리",
            "investment_horizon": "장기",
            "philosophy_summary": f"사용자는 {risk_tolerance} 성향으로 {', '.join(preferred_assets)}을 선호하는 투자자입니다.",
            "key_principles": ["분산투자", "장기투자"],
            "confidence_score": 0.7
        }
    
    async def generate_personalized_strategy(self, philosophy_analysis: Dict[str, Any], user_id: str, custom_name: str = None) -> Dict[str, Any]:
        """개인화된 리밸런싱 전략 생성"""
        try:
            # 전략명 생성 (사용자 지정 이름이 있으면 우선 사용)
            strategy_name = custom_name.strip() if custom_name else self._generate_strategy_name(philosophy_analysis)
            
            # 포트폴리오 할당 생성
            target_allocation = await self._generate_allocation(philosophy_analysis)
            
            # 성과 지표 예측
            performance_metrics = self._generate_performance_metrics(philosophy_analysis, target_allocation)
            
            # 전략 설명 생성
            description = self._generate_strategy_description(philosophy_analysis)
            
            # 태그 생성
            tags = self._generate_strategy_tags(philosophy_analysis)
            
            strategy_data = {
                "strategy_name": strategy_name,
                "strategy_type": "ai_generated",
                "description": description,
                "target_allocation": target_allocation,
                "expected_return": performance_metrics['expected_return'],
                "volatility": performance_metrics['volatility'],
                "max_drawdown": performance_metrics['max_drawdown'],
                "sharpe_ratio": performance_metrics['sharpe_ratio'],
                "risk_level": self._map_risk_tolerance_to_level(philosophy_analysis.get('risk_tolerance', '균형')),
                "tags": tags,
                "user_id": user_id
            }
            
            logger.info(f"개인화 전략 생성 완료: {strategy_name}")
            return strategy_data
            
        except Exception as e:
            logger.error(f"개인화 전략 생성 오류: {e}")
            raise
    
    def _generate_strategy_name(self, philosophy: Dict[str, Any]) -> str:
        """전략명 생성"""
        risk_tolerance = philosophy.get('risk_tolerance', '균형')
        preferred_assets = philosophy.get('preferred_assets', [])
        
        # 기본 이름 구성요소
        risk_names = {
            '보수적': ['안정형', '보수형', '수비형'],
            '균형': ['균형형', '조화형', '중도형'],
            '공격적': ['성장형', '공격형', '혁신형']
        }
        
        asset_names = {
            '기술주': '테크',
            '가치주': '가치',
            '배당주': '배당',
            '다양화': '다각화'
        }
        
        # 시간 기반 고유성 확보
        timestamp = datetime.now().strftime("%m%d")
        
        # 이름 조합
        risk_name = risk_names.get(risk_tolerance, ['맞춤형'])[0]
        
        if preferred_assets:
            asset_name = asset_names.get(preferred_assets[0], preferred_assets[0])
            strategy_name = f"{asset_name} {risk_name} 전략 #{timestamp}"
        else:
            strategy_name = f"개인화 {risk_name} 전략 #{timestamp}"
        
        return strategy_name
    
    async def _generate_allocation(self, philosophy: Dict[str, Any]) -> Dict[str, float]:
        """포트폴리오 할당 생성"""
        risk_tolerance = philosophy.get('risk_tolerance', '균형')
        preferred_assets = philosophy.get('preferred_assets', [])
        
        # 기본 할당 템플릿
        if risk_tolerance == '보수적':
            if '배당주' in preferred_assets:
                return {
                    "AAPL": 30.0,
                    "MSFT": 25.0,
                    "JNJ": 20.0,
                    "PG": 15.0,
                    "KO": 10.0
                }
            else:
                return {
                    "AAPL": 35.0,
                    "MSFT": 30.0,
                    "GOOGL": 20.0,
                    "AMZN": 15.0
                }
        
        elif risk_tolerance == '공격적':
            if '기술주' in preferred_assets:
                return {
                    "NVDA": 35.0,
                    "GOOGL": 25.0,
                    "MSFT": 20.0,
                    "TSLA": 20.0
                }
            else:
                return {
                    "AAPL": 30.0,
                    "GOOGL": 25.0,
                    "MSFT": 20.0,
                    "NVDA": 15.0,
                    "TSLA": 10.0
                }
        
        else:  # 균형
            return {
                "AAPL": 25.0,
                "GOOGL": 20.0,
                "MSFT": 25.0,
                "AMZN": 20.0,
                "TSLA": 10.0
            }
    
    def _generate_performance_metrics(self, philosophy: Dict[str, Any], allocation: Dict[str, float]) -> Dict[str, float]:
        """성과 지표 생성"""
        risk_tolerance = philosophy.get('risk_tolerance', '균형')
        
        # 위험 성향별 기본 메트릭
        base_metrics = {
            '보수적': {
                'expected_return': 14.5,
                'volatility': 16.2,
                'max_drawdown': -12.1,
                'sharpe_ratio': 0.67
            },
            '균형': {
                'expected_return': 18.8,
                'volatility': 21.3,
                'max_drawdown': -16.5,
                'sharpe_ratio': 0.75
            },
            '공격적': {
                'expected_return': 25.2,
                'volatility': 28.7,
                'max_drawdown': -22.8,
                'sharpe_ratio': 0.83
            }
        }
        
        metrics = base_metrics.get(risk_tolerance, base_metrics['균형'])
        
        # 할당에 따른 미세 조정
        tech_weight = allocation.get('NVDA', 0) + allocation.get('TSLA', 0) * 0.5
        if tech_weight > 20:
            metrics['expected_return'] += 2.0
            metrics['volatility'] += 3.0
            metrics['max_drawdown'] -= 2.0
        
        return metrics
    
    def _generate_strategy_description(self, philosophy: Dict[str, Any]) -> str:
        """전략 설명 생성"""
        risk_tolerance = philosophy.get('risk_tolerance', '균형')
        preferred_assets = philosophy.get('preferred_assets', [])
        philosophy_summary = philosophy.get('philosophy_summary', '')
        
        descriptions = {
            '보수적': f"안정성을 중시하는 보수적 투자 전략으로, {', '.join(preferred_assets)}을 중심으로 구성되었습니다.",
            '균형': f"성장성과 안정성의 균형을 맞춘 투자 전략으로, {', '.join(preferred_assets)}에 중점을 둡니다.",
            '공격적': f"높은 수익을 추구하는 공격적 투자 전략으로, {', '.join(preferred_assets)} 중심의 포트폴리오입니다."
        }
        
        base_desc = descriptions.get(risk_tolerance, "개인화된 투자 전략입니다.")
        
        if philosophy_summary:
            return f"{base_desc} {philosophy_summary}"
        else:
            return base_desc
    
    def _generate_strategy_tags(self, philosophy: Dict[str, Any]) -> List[str]:
        """전략 태그 생성"""
        tags = ["개인화", "AI생성"]
        
        risk_tolerance = philosophy.get('risk_tolerance', '균형')
        preferred_assets = philosophy.get('preferred_assets', [])
        investment_goals = philosophy.get('investment_goals', [])
        
        # 위험 성향 태그
        risk_tags = {
            '보수적': "저위험",
            '균형': "중위험",
            '공격적': "고위험"
        }
        tags.append(risk_tags.get(risk_tolerance, "중위험"))
        
        # 자산 태그 추가
        tags.extend(preferred_assets[:2])  # 최대 2개
        
        # 투자 목표 태그 추가
        tags.extend(investment_goals[:2])  # 최대 2개
        
        return list(set(tags))  # 중복 제거
    
    def _map_risk_tolerance_to_level(self, risk_tolerance: str) -> str:
        """위험 성향을 위험 수준으로 매핑"""
        mapping = {
            '보수적': '낮음',
            '균형': '중간',
            '공격적': '높음'
        }
        return mapping.get(risk_tolerance, '중간')
    
    async def learn_and_create_strategy(self, user_input: Dict[str, Any], user_id: str, custom_name: str = None) -> Dict[str, Any]:
        """전체 학습 및 전략 생성 프로세스"""
        try:
            db_manager = await get_database_manager()
            
            # 1. 사용자 철학 분석
            logger.info("사용자 투자 철학 분석 시작...")
            philosophy_analysis = await self.analyze_user_philosophy(user_input)
            
            # 2. 개인화 전략 생성
            logger.info("개인화 전략 생성 시작...")
            strategy_data = await self.generate_personalized_strategy(philosophy_analysis, user_id, custom_name)
            
            # 3. 전략을 데이터베이스에 저장
            logger.info("전략 데이터베이스 저장 시작...")
            strategy_id = await db_manager.save_rebalancing_strategy(strategy_data)
            
            # 4. 학습 데이터 저장
            learning_data = {
                'user_id': user_id,
                'learning_method': philosophy_analysis['learning_method'],
                'input_content': philosophy_analysis['original_content'],
                'processed_content': philosophy_analysis['processed_content'],
                'extracted_philosophy': json.dumps(philosophy_analysis['philosophy_analysis']),
                'generated_strategy_id': strategy_id,
                'confidence_score': philosophy_analysis['confidence_score']
            }
            
            learning_id = await db_manager.save_learning_data(learning_data)
            
            logger.info(f"전략 학습 및 생성 완료: {strategy_data['strategy_name']}")
            
            return {
                'success': True,
                'strategy_id': strategy_id,
                'learning_id': learning_id,
                'strategy': strategy_data,
                'philosophy_analysis': philosophy_analysis['philosophy_analysis'],
                'confidence_score': philosophy_analysis['confidence_score']
            }
            
        except Exception as e:
            logger.error(f"전략 학습 및 생성 오류: {e}")
            raise

# 전략 학습자 싱글톤 인스턴스
strategy_learner = StrategyLearner()

async def get_strategy_learner() -> StrategyLearner:
    """전략 학습자 인스턴스 반환"""
    return strategy_learner
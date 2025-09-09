import asyncio
import aiofiles
from typing import Dict, List, Optional, Any, Union
import logging
from pathlib import Path
import tempfile
import os
from datetime import datetime
import json
import re

# PDF 처리
import PyPDF2
import io

# 웹 스크래핑
import httpx
from bs4 import BeautifulSoup

# 텍스트 처리
import nltk
from collections import Counter

# 데이터베이스
from database_manager import get_database_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserDataProcessor:
    """
    사용자 업로드 데이터 처리 클래스
    PDF, URL, 텍스트 데이터를 분석하고 투자 관련 정보를 추출
    """
    
    def __init__(self):
        self.supported_file_types = ['.pdf', '.txt', '.docx']
        self.investment_keywords = [
            '투자', '포트폴리오', '자산배분', '리밸런싱', '주식', '채권', '펀드',
            '수익률', '위험', '분산투자', '성장', '가치', '배당', '부동산',
            '금', '원자재', '현금', '예금', '적금', '연금', '보험',
            'investment', 'portfolio', 'asset allocation', 'rebalancing',
            'stocks', 'bonds', 'funds', 'return', 'risk', 'diversification'
        ]
        
    async def process_user_data(self, user_id: str, data_type: str, 
                               data_input: Union[str, bytes], 
                               filename: str = None) -> Dict[str, Any]:
        """
        사용자 데이터 통합 처리 함수
        
        Args:
            user_id: 사용자 ID
            data_type: 데이터 타입 ('pdf', 'url', 'text', 'file')
            data_input: 처리할 데이터 (URL, 텍스트, 파일 바이트)
            filename: 파일명 (파일 업로드시)
        
        Returns:
            처리 결과 딕셔너리
        """
        try:
            db_manager = await get_database_manager()
            start_time = datetime.now()
            
            # 데이터 타입별 처리
            if data_type == 'pdf':
                result = await self._process_pdf(data_input, filename)
            elif data_type == 'url':
                result = await self._process_url(data_input)
            elif data_type == 'text':
                result = await self._process_text(data_input)
            elif data_type == 'file':
                result = await self._process_file(data_input, filename)
            else:
                raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")
            
            # 투자 관련 정보 추출 (AI 강화)
            investment_insights = await self._extract_investment_insights(result['content'])
            
            # 무료 LLM으로 더 지능적인 분석 시도
            try:
                enhanced_insights = await self._enhance_insights_with_ai(result['content'], investment_insights)
                if enhanced_insights:
                    investment_insights.update(enhanced_insights)
            except Exception as e:
                logger.info(f"AI 강화 분석 건너뜀: {e}")
                
            result['investment_insights'] = investment_insights
            
            # 메타데이터 생성
            metadata = {
                'data_type': data_type,
                'filename': filename,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'content_length': len(result['content']),
                'investment_score': investment_insights.get('investment_relevance_score', 0),
                'processed_at': datetime.now().isoformat()
            }
            
            # 데이터베이스에 저장
            data_id = await db_manager.save_user_data(
                user_id=user_id,
                data_type=data_type,
                content=str(data_input)[:1000],  # 원본 데이터 일부만 저장
                processed_content=result['content'],
                metadata=metadata
            )
            
            # 처리 로그 저장
            await db_manager.log_processing(
                user_id=user_id,
                process_type=f"user_data_{data_type}",
                status="success",
                input_data={'data_type': data_type, 'filename': filename},
                output_data={'data_id': data_id, 'content_length': len(result['content'])},
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            result['data_id'] = data_id
            result['metadata'] = metadata
            
            logger.info(f"사용자 데이터 처리 완료: {user_id} - {data_type}")
            return result
            
        except Exception as e:
            logger.error(f"사용자 데이터 처리 오류: {e}")
            
            # 오류 로그 저장
            db_manager = await get_database_manager()
            await db_manager.log_processing(
                user_id=user_id,
                process_type=f"user_data_{data_type}",
                status="error",
                input_data={'data_type': data_type, 'filename': filename},
                error_message=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            return {
                'success': False,
                'error': str(e),
                'content': '',
                'metadata': {'error': True}
            }
    
    async def _process_pdf(self, pdf_data: bytes, filename: str) -> Dict[str, Any]:
        """PDF 파일 처리"""
        try:
            pdf_stream = io.BytesIO(pdf_data)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            # 모든 페이지의 텍스트 추출
            full_text = ""
            page_contents = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        full_text += page_text + "\n"
                        page_contents.append({
                            'page': page_num + 1,
                            'content': page_text.strip()
                        })
                except Exception as e:
                    logger.warning(f"PDF 페이지 {page_num + 1} 처리 오류: {e}")
                    continue
            
            if not full_text.strip():
                raise ValueError("PDF에서 텍스트를 추출할 수 없습니다")
            
            # PDF 메타데이터
            pdf_info = pdf_reader.metadata if pdf_reader.metadata else {}
            
            result = {
                'success': True,
                'content': full_text.strip(),
                'page_count': len(pdf_reader.pages),
                'pages': page_contents,
                'pdf_metadata': {
                    'title': pdf_info.get('/Title', ''),
                    'author': pdf_info.get('/Author', ''),
                    'subject': pdf_info.get('/Subject', ''),
                    'creator': pdf_info.get('/Creator', ''),
                    'creation_date': str(pdf_info.get('/CreationDate', '')),
                    'modification_date': str(pdf_info.get('/ModDate', ''))
                }
            }
            
            logger.info(f"PDF 처리 완료: {filename}, 페이지 수: {len(pdf_reader.pages)}")
            return result
            
        except Exception as e:
            logger.error(f"PDF 처리 오류: {e}")
            raise
    
    async def _process_url(self, url: str) -> Dict[str, Any]:
        """URL 웹페이지 처리"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # HTML 파싱
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 불필요한 태그 제거
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.extract()
                
                # 메타데이터 추출
                title = soup.find('title')
                meta_description = soup.find('meta', attrs={'name': 'description'})
                meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                
                # 본문 텍스트 추출
                main_content = ""
                
                # 주요 콘텐츠 영역 찾기
                content_selectors = [
                    'main', 'article', '.content', '#content', 
                    '.post', '.entry-content', '.article-content'
                ]
                
                main_element = None
                for selector in content_selectors:
                    main_element = soup.select_one(selector)
                    if main_element:
                        break
                
                if main_element:
                    main_content = main_element.get_text(strip=True, separator='\n')
                else:
                    # 전체 body에서 텍스트 추출
                    body = soup.find('body')
                    if body:
                        main_content = body.get_text(strip=True, separator='\n')
                
                # 텍스트 정리
                main_content = re.sub(r'\n+', '\n', main_content)
                main_content = re.sub(r'\s+', ' ', main_content)
                
                result = {
                    'success': True,
                    'content': main_content.strip(),
                    'url': url,
                    'title': title.get_text().strip() if title else '',
                    'meta_description': meta_description.get('content', '') if meta_description else '',
                    'meta_keywords': meta_keywords.get('content', '') if meta_keywords else '',
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(main_content)
                }
                
                logger.info(f"URL 처리 완료: {url}")
                return result
                
        except Exception as e:
            logger.error(f"URL 처리 오류: {e}")
            raise
    
    async def _process_text(self, text: str) -> Dict[str, Any]:
        """일반 텍스트 처리"""
        try:
            # 텍스트 정리
            cleaned_text = re.sub(r'\s+', ' ', text.strip())
            
            # 기본 텍스트 분석
            word_count = len(cleaned_text.split())
            char_count = len(cleaned_text)
            line_count = len(cleaned_text.split('\n'))
            
            result = {
                'success': True,
                'content': cleaned_text,
                'word_count': word_count,
                'char_count': char_count,
                'line_count': line_count
            }
            
            logger.info(f"텍스트 처리 완료: {word_count} 단어")
            return result
            
        except Exception as e:
            logger.error(f"텍스트 처리 오류: {e}")
            raise
    
    async def _process_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """일반 파일 처리"""
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.pdf':
                return await self._process_pdf(file_data, filename)
            elif file_ext in ['.txt', '.md']:
                text_content = file_data.decode('utf-8', errors='ignore')
                return await self._process_text(text_content)
            else:
                # 지원하지 않는 파일 형식
                return {
                    'success': False,
                    'error': f"지원하지 않는 파일 형식: {file_ext}",
                    'content': '',
                    'filename': filename,
                    'file_extension': file_ext
                }
                
        except Exception as e:
            logger.error(f"파일 처리 오류: {e}")
            raise
    
    async def _extract_investment_insights(self, content: str) -> Dict[str, Any]:
        """텍스트에서 투자 관련 인사이트 추출"""
        try:
            # 투자 관련 키워드 매칭
            keyword_matches = {}
            investment_score = 0
            
            for keyword in self.investment_keywords:
                count = len(re.findall(keyword, content, re.IGNORECASE))
                if count > 0:
                    keyword_matches[keyword] = count
                    investment_score += count
            
            # 투자 관련도 점수 계산 (0-100)
            max_score = len(content.split()) * 0.1  # 전체 단어수의 10%를 최대로 가정
            relevance_score = min(100, (investment_score / max_score * 100)) if max_score > 0 else 0
            
            # 숫자 패턴 추출 (수익률, 비율 등)
            number_patterns = re.findall(r'(\d+(?:\.\d+)?)\s*%', content)
            percentages = [float(x) for x in number_patterns]
            
            # 통화 패턴 추출
            currency_patterns = re.findall(r'[₩$¥€£]\s*[\d,]+(?:\.\d+)?', content)
            
            # 날짜 패턴 추출
            date_patterns = re.findall(r'\d{4}[년\-\/]\d{1,2}[월\-\/]\d{1,2}[일]?', content)
            
            # 주요 문장 추출 (투자 키워드가 포함된 문장)
            sentences = re.split(r'[.!?]', content)
            investment_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword in sentence.lower() for keyword in self.investment_keywords[:10]):
                    if len(sentence) > 20 and len(sentence) < 200:
                        investment_sentences.append(sentence)
            
            result = {
                'investment_relevance_score': round(relevance_score, 2),
                'keyword_matches': keyword_matches,
                'total_keywords_found': investment_score,
                'percentages': percentages,
                'currency_mentions': currency_patterns,
                'date_mentions': date_patterns,
                'key_sentences': investment_sentences[:5],  # 상위 5개 문장
                'content_analysis': {
                    'word_count': len(content.split()),
                    'char_count': len(content),
                    'investment_keyword_density': round(investment_score / len(content.split()) * 100, 2) if content.split() else 0
                }
            }
            
            logger.info(f"투자 인사이트 추출 완료: 관련도 점수 {relevance_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"투자 인사이트 추출 오류: {e}")
            return {
                'investment_relevance_score': 0,
                'keyword_matches': {},
                'error': str(e)
            }
    
    async def analyze_user_data_batch(self, user_id: str) -> Dict[str, Any]:
        """사용자의 모든 업로드 데이터를 종합 분석"""
        try:
            db_manager = await get_database_manager()
            user_data_list = await db_manager.get_user_data(user_id)
            
            if not user_data_list:
                return {
                    'success': False,
                    'message': '분석할 데이터가 없습니다',
                    'total_data_count': 0
                }
            
            # 전체 텍스트 결합
            combined_content = ""
            data_summary = {
                'pdf_count': 0,
                'url_count': 0,
                'text_count': 0,
                'total_content_length': 0
            }
            
            all_keywords = Counter()
            all_percentages = []
            all_sentences = []
            
            for data in user_data_list:
                content = data.get('processed_content', '')
                data_type = data.get('data_type', '')
                
                if content:
                    combined_content += content + "\n\n"
                    data_summary['total_content_length'] += len(content)
                    data_summary[f'{data_type}_count'] += 1
                    
                    # 메타데이터에서 인사이트 추출
                    metadata = data.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    
                    # 키워드와 통계 집계
                    if 'investment_insights' in metadata:
                        insights = metadata['investment_insights']
                        if 'keyword_matches' in insights:
                            all_keywords.update(insights['keyword_matches'])
                        if 'percentages' in insights:
                            all_percentages.extend(insights['percentages'])
                        if 'key_sentences' in insights:
                            all_sentences.extend(insights['key_sentences'])
            
            # 종합 분석
            if combined_content:
                comprehensive_insights = await self._extract_investment_insights(combined_content)
            else:
                comprehensive_insights = {}
            
            # 최종 결과 구성
            analysis_result = {
                'success': True,
                'user_id': user_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_summary': data_summary,
                'comprehensive_insights': comprehensive_insights,
                'aggregated_statistics': {
                    'top_keywords': dict(all_keywords.most_common(20)),
                    'percentage_range': {
                        'min': min(all_percentages) if all_percentages else 0,
                        'max': max(all_percentages) if all_percentages else 0,
                        'avg': sum(all_percentages) / len(all_percentages) if all_percentages else 0,
                        'count': len(all_percentages)
                    },
                    'key_insights': all_sentences[:10]
                },
                'recommendations': await self._generate_data_recommendations(comprehensive_insights, data_summary)
            }
            
            logger.info(f"사용자 데이터 종합 분석 완료: {user_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"사용자 데이터 종합 분석 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id
            }
    
    async def _enhance_insights_with_ai(self, content: str, basic_insights: Dict[str, Any]) -> Dict[str, Any]:
        """무료 LLM을 사용한 투자 인사이트 강화"""
        try:
            # Ollama를 사용한 AI 분석
            ollama_host = "http://localhost:11434"
            
            # 간단한 가용성 체크
            import requests
            health_check = requests.get(f"{ollama_host}/api/tags", timeout=3)
            if health_check.status_code != 200:
                logger.info("Ollama 서비스 사용 불가")
                return {}
                
            prompt = f"""다음은 사용자가 제공한 투자 관련 문서/텍스트입니다. 이를 분석해서 투자 성향, 목표, 선호하는 투자 전략을 파악해주세요.

텍스트: {content[:2000]}  # 처음 2000자만 사용

다음 형식으로 분석해주세요:
**투자 성향**: 보수적/중간/공격적
**투자 목표**: 은퇴준비/자산증대/수익창출/성장추구
**투자 기간**: 단기/중기/장기
**선호 자산**: 주식, 채권, 부동산 등
**리스크 선호도**: 1-10 점수
**핵심 전략**: 2-3줄 요약

간단하고 명확하게 한국어로 답해주세요."""

            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "max_tokens": 500}
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return {}
                
            result = response.json()
            ai_response = result.get("response", "")
            
            if not ai_response:
                return {}
            
            # AI 응답 파싱
            enhanced_insights = {}
            lines = ai_response.split('\n')
            
            for line in lines:
                line = line.strip()
                if "투자 성향" in line and ":" in line:
                    enhanced_insights['investment_style'] = line.split(":")[-1].strip()
                elif "투자 목표" in line and ":" in line:
                    enhanced_insights['investment_goal'] = line.split(":")[-1].strip()
                elif "투자 기간" in line and ":" in line:
                    enhanced_insights['investment_period'] = line.split(":")[-1].strip()
                elif "선호 자산" in line and ":" in line:
                    enhanced_insights['preferred_assets'] = line.split(":")[-1].strip()
                elif "리스크 선호도" in line and ":" in line:
                    risk_text = line.split(":")[-1].strip()
                    # 숫자 추출
                    import re
                    risk_scores = re.findall(r'\d+', risk_text)
                    if risk_scores:
                        enhanced_insights['risk_score'] = int(risk_scores[0])
                elif "핵심 전략" in line and ":" in line:
                    enhanced_insights['key_strategy'] = line.split(":")[-1].strip()
            
            # AI 분석 완료 플래그
            enhanced_insights['ai_enhanced'] = True
            enhanced_insights['ai_model'] = 'ollama_llama3.1'
            
            logger.info("AI 강화 투자 인사이트 추출 완료")
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"AI 강화 분석 실패: {e}")
            return {}

    async def _generate_data_recommendations(self, insights: Dict[str, Any], 
                                           summary: Dict[str, Any]) -> List[str]:
        """데이터 분석 기반 추천사항 생성"""
        recommendations = []
        
        try:
            relevance_score = insights.get('investment_relevance_score', 0)
            keyword_count = len(insights.get('keyword_matches', {}))
            
            # 투자 관련도에 따른 추천
            if relevance_score < 20:
                recommendations.append("투자 관련 정보가 부족합니다. 투자 철학이나 목표를 담은 문서를 추가로 업로드해보세요.")
            elif relevance_score > 70:
                recommendations.append("풍부한 투자 정보를 제공해주셨습니다. 이 정보를 바탕으로 맞춤형 포트폴리오 분석이 가능합니다.")
            
            # 데이터 다양성에 따른 추천
            data_types = sum([summary.get(f'{dt}_count', 0) > 0 for dt in ['pdf', 'url', 'text']])
            if data_types == 1:
                recommendations.append("다양한 형태의 투자 정보(PDF, 웹페이지, 텍스트)를 추가하시면 더 정확한 분석이 가능합니다.")
            
            # 키워드 분석 기반 추천
            if keyword_count > 10:
                recommendations.append("다양한 투자 용어가 포함되어 있어 포괄적인 투자 전략 수립이 가능합니다.")
            
            # 수치 정보에 따른 추천
            percentages = insights.get('percentages', [])
            if len(percentages) > 5:
                recommendations.append("구체적인 수치 정보가 충분하여 정량적 분석이 가능합니다.")
            elif len(percentages) == 0:
                recommendations.append("목표 수익률이나 자산 비중 등 수치적 목표를 포함한 정보를 추가하시면 도움이 됩니다.")
            
            if not recommendations:
                recommendations.append("업로드하신 정보를 바탕으로 개인화된 투자 분석을 진행하겠습니다.")
                
        except Exception as e:
            logger.error(f"추천사항 생성 오류: {e}")
            recommendations = ["데이터 분석을 완료했습니다. 추가 분석을 위해 더 많은 정보를 제공해주세요."]
        
        return recommendations

# 사용자 데이터 프로세서 인스턴스
user_data_processor = UserDataProcessor()

async def get_user_data_processor() -> UserDataProcessor:
    """사용자 데이터 프로세서 인스턴스 반환"""
    return user_data_processor
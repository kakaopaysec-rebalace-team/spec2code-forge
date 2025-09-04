# AI Asset Rebalancing System - Backend

한국어 기반의 AI 자산 리밸런싱 시스템 백엔드 API 서버입니다. Claude AI와 통합된 포트폴리오 분석 및 투자 전략 제안 시스템을 제공합니다.

## 🚀 주요 기능

### 1. AI 기반 포트폴리오 분석
- **Claude AI 통합**: Anthropic Claude API를 활용한 고도화된 투자 전략 분석
- **다중 소스 학습**: 웹 검색, PDF 분석, 학술 논문 검색을 통한 종합적인 투자 인사이트
- **개인화된 전략**: 사용자 프로필과 투자 철학을 반영한 맞춤형 리밸런싱 전략

### 2. 종합 시뮬레이션 엔진
- **백테스팅**: 과거 데이터 기반의 포트폴리오 성과 분석
- **스트레스 테스트**: 극한 시장 상황에서의 포트폴리오 복원력 평가
- **리스크 분석**: VaR, 샤프 비율, 최대 손실폭 등 다양한 위험 지표 계산

### 3. 시장 데이터 통합
- **실시간 데이터**: yfinance를 통한 글로벌 금융 시장 데이터
- **한국 시장 지원**: KRX API 연동으로 한국 증시 데이터 제공
- **대체 데이터 소스**: investing.com 스크래핑을 통한 보완적 데이터 수집

### 4. 사용자 데이터 처리
- **PDF 분석**: 투자 관련 문서의 자동 텍스트 추출 및 분석
- **URL 스크래핑**: 투자 관련 웹페이지 내용 분석
- **텍스트 분석**: 사용자 제공 투자 철학 및 목표 분석

### 5. 데이터베이스 통합
- **SQLite 기반**: 경량화된 데이터베이스로 빠른 개발 및 배포
- **사용자 관리**: 완전한 사용자 정보 및 포트폴리오 저장
- **분석 이력**: 모든 분석 결과 및 추천 이력 관리

## 🏗️ 시스템 아키텍처

```
├── app.py                    # FastAPI 메인 애플리케이션
├── data_processor.py         # 시장 데이터 수집 및 전처리
├── ai_model_trainer.py       # Claude AI 통합 및 전략 생성
├── simulation_analyzer.py    # 백테스팅 및 시뮬레이션 엔진
├── database_manager.py       # 데이터베이스 관리 및 ORM
├── user_data_processor.py    # 사용자 데이터 처리 및 분석
├── start_backend.py          # 자동화된 시작 스크립트
├── requirements.txt          # Python 의존성
├── .env.example             # 환경 변수 템플릿
└── README.md               # 이 파일
```

## 📋 사전 요구사항

### 시스템 요구사항
- **Python**: 3.8 이상
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 4GB RAM (8GB 권장)
- **저장공간**: 최소 2GB 여유 공간

### API 키 (선택사항)
- **Anthropic API Key**: Claude AI 기능 사용시 필수
- **KRX API Key**: 한국 거래소 데이터 사용시
- **Google Search API Key**: 웹 검색 기능 사용시

## 🛠️ 설치 및 실행

### 1. 자동 설치 및 실행 (권장)

```bash
# 저장소 클론
git clone <repository-url>
cd spec2code-forge/backend

# 자동 설정 및 서버 시작
python start_backend.py
```

자동 스크립트가 다음을 수행합니다:
- Python 버전 확인
- 가상환경 생성
- 의존성 패키지 설치
- 환경 파일 설정
- 기본 테스트 실행
- 서버 시작

### 2. 수동 설치

```bash
# 1. 가상환경 생성
python -m venv venv

# 2. 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 입력

# 5. 서버 시작
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 환경 변수 설정

`.env` 파일에서 다음 키들을 설정하세요:

```bash
# 필수 설정
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 선택적 설정
KRX_API_KEY=your_krx_api_key_here
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

## 🔧 설정 옵션

### 시작 스크립트 옵션

```bash
# 기본 실행
python start_backend.py

# 호스트 및 포트 지정
python start_backend.py --host 127.0.0.1 --port 8080

# 테스트 건너뛰기
python start_backend.py --skip-tests

# 설정만 수행 (서버 시작 안함)
python start_backend.py --setup-only

# 자동 리로드 비활성화
python start_backend.py --no-reload
```

### 환경별 설정

개발 환경:
```bash
DEBUG=True
MOCK_DATA_ENABLED=True
LOG_LEVEL=INFO
```

프로덕션 환경:
```bash
DEBUG=False
MOCK_DATA_ENABLED=False
LOG_LEVEL=WARNING
```

## 📡 API 엔드포인트

### 인증 및 사용자 관리
- `POST /users/register` - 사용자 등록
- `GET /users/{user_id}` - 사용자 정보 조회
- `PUT /users/{user_id}` - 사용자 정보 업데이트
- `GET /users/{user_id}/statistics` - 사용자 통계

### 포트폴리오 관리
- `POST /portfolios` - 포트폴리오 생성
- `GET /portfolios/{portfolio_id}` - 포트폴리오 조회
- `GET /users/{user_id}/portfolios` - 사용자 포트폴리오 목록

### 시장 데이터
- `GET /market-data/{symbol}` - 개별 종목 데이터
- `POST /market-data/batch` - 다수 종목 데이터
- `GET /market-data/{symbol}/history` - 과거 데이터

### 사용자 데이터 처리
- `POST /user-data/upload` - 텍스트/URL 업로드
- `POST /user-data/upload-file` - 파일 업로드
- `GET /users/{user_id}/data` - 사용자 데이터 조회
- `POST /users/{user_id}/data/analyze` - 데이터 종합 분석

### AI 분석 및 전략
- `POST /ai/train` - AI 모델 학습
- `POST /ai/generate-strategy` - 투자 전략 생성
- `POST /analysis/comprehensive` - 종합 포트폴리오 분석
- `POST /analysis/simulation` - 시뮬레이션 실행

### 분석 결과 관리
- `GET /users/{user_id}/analyses` - 분석 결과 목록
- `GET /analysis/{analysis_id}` - 특정 분석 결과

### 유틸리티
- `GET /health` - 시스템 상태 확인
- `GET /strategies/templates` - 투자 전략 템플릿
- `POST /system/cleanup` - 시스템 정리

## 📊 API 사용 예제

### 사용자 등록
```python
import requests

# 사용자 등록
user_data = {
    "name": "김투자",
    "email": "kim@example.com",
    "risk_tolerance": "moderate",
    "investment_goal": "retirement",
    "investment_horizon": 20,
    "preferred_asset_types": ["stocks", "bonds"]
}

response = requests.post(
    "http://localhost:8000/users/register",
    json=user_data
)
user_id = response.json()["user_id"]
```

### 종합 포트폴리오 분석
```python
# 분석 요청
analysis_request = {
    "user_id": user_id,
    "user_profile": {
        "investment_style": "moderate",
        "investment_goal": "retirement",
        "investment_period": "long"
    },
    "current_portfolio": [
        {"symbol": "AAPL", "weight": 30},
        {"symbol": "GOOGL", "weight": 25},
        {"symbol": "BND", "weight": 45}
    ],
    "analysis_type": "comprehensive",
    "include_stress_test": True
}

response = requests.post(
    "http://localhost:8000/analysis/comprehensive",
    json=analysis_request
)
analysis_result = response.json()
```

### 파일 업로드
```python
# PDF 파일 업로드
files = {"file": open("investment_plan.pdf", "rb")}
data = {"user_id": user_id}

response = requests.post(
    "http://localhost:8000/user-data/upload-file",
    files=files,
    data=data
)
```

## 🧪 테스트

### 기본 테스트 실행
```bash
# 자동 테스트 (시작 스크립트 사용)
python start_backend.py --setup-only

# 수동 테스트
python -c "
import sys
sys.path.append('.')
from app import app
from data_processor import DataProcessor
from ai_model_trainer import AIModelTrainer
print('✅ 모든 모듈 임포트 성공')
"
```

### API 테스트
```bash
# 서버 상태 확인
curl http://localhost:8000/health

# API 문서 접속
open http://localhost:8000/docs
```

## 📁 데이터베이스 스키마

### 주요 테이블
- **users**: 사용자 정보
- **user_portfolios**: 포트폴리오 데이터
- **user_data**: 업로드된 사용자 데이터
- **analysis_results**: AI 분석 결과
- **rebalancing_recommendations**: 리밸런싱 추천
- **simulation_results**: 시뮬레이션 결과
- **processing_logs**: 처리 로그

## 🔍 로깅 및 모니터링

### 로그 파일 위치
- 애플리케이션 로그: `logs/app.log`
- 오류 로그: 콘솔 및 로그 파일
- 데이터베이스: `asset_rebalancing.db`

### 로그 레벨 설정
```bash
# .env 파일에서
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## ⚡ 성능 최적화

### 추천 설정
```bash
# 동시 연결 수 증가 (운영 환경)
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

# 메모리 사용량 모니터링
python -c "
import psutil
print(f'메모리 사용량: {psutil.virtual_memory().percent}%')
"
```

### 캐싱 설정
- 시장 데이터: 5분 캐시
- AI 분석 결과: 세션 기반 캐시
- 사용자 데이터: 메모리 캐시

## 🛡️ 보안 고려사항

### API 키 보안
- `.env` 파일을 버전 관리에 포함하지 마세요
- 프로덕션 환경에서는 환경 변수 사용 권장

### 파일 업로드 보안
- 지원 파일 형식: PDF, TXT, MD
- 최대 파일 크기: 10MB
- 파일 스캔 및 검증 수행

### 데이터베이스 보안
- SQLite 파일 권한 설정
- 정기적인 백업 수행
- 개인정보 암호화 저장

## 🚨 문제 해결

### 일반적인 오류

**1. 포트 사용 중 오류**
```bash
# 다른 포트 사용
python start_backend.py --port 8001
```

**2. 의존성 설치 오류**
```bash
# pip 업그레이드 후 재설치
pip install --upgrade pip
pip install --force-reinstall -r requirements.txt
```

**3. API 키 설정 오류**
```bash
# .env 파일 확인
cat .env | grep ANTHROPIC_API_KEY
```

**4. 데이터베이스 연결 오류**
```bash
# 데이터베이스 파일 권한 확인
ls -la asset_rebalancing.db
```

### 디버깅 모드
```bash
# 디버그 로그 활성화
DEBUG=True LOG_LEVEL=DEBUG python start_backend.py
```

## 📚 추가 자료

### API 문서
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 외부 API 문서
- [Anthropic Claude API](https://docs.anthropic.com/)
- [yfinance 라이브러리](https://github.com/ranaroussi/yfinance)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)

### 관련 논문 및 자료
- Modern Portfolio Theory
- Asset Allocation Strategies
- Risk Parity Portfolios

## 🤝 기여 방법

1. 이슈 보고: GitHub Issues 사용
2. 기능 제안: Pull Request 생성
3. 코드 리뷰: 코딩 스타일 가이드 준수
4. 테스트: 모든 기능에 대한 테스트 포함

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

## 📞 지원 및 연락처

기술적 문제나 질문이 있으시면 GitHub Issues를 통해 문의하세요.

**개발 정보**
- 언어: Python 3.8+
- 프레임워크: FastAPI
- 데이터베이스: SQLite
- AI: Anthropic Claude
- 버전: 2.0.0
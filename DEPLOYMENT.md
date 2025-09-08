# 🚀 Database AI 시스템 배포 가이드

## 📋 개요

이 시스템은 **API 키가 완전히 불필요한 자립형 AI 투자 분석 시스템**입니다.
318개의 세계적인 투자 전문가 전략을 데이터베이스에 저장하여 Claude API 없이도 고품질 포트폴리오 분석을 제공합니다.

## ⚡ 빠른 시작 (권장)

### 1단계: 자동 배포 스크립트 실행
```bash
# 실행 권한 부여
chmod +x deploy-database-ai.sh

# 자동 배포 시작
./deploy-database-ai.sh
```

### 2단계: 접속 확인
- **웹 서비스**: http://localhost:8080
- **API 서버**: http://localhost:8003
- **Database AI 전용 API**: http://localhost:8003/database-ai/generate-strategy

## 🔧 수동 배포 방법

### 1. 시스템 요구사항
- **OS**: Linux (Rocky Linux, Ubuntu, CentOS 등) 또는 macOS
- **Python**: 3.8 이상
- **Node.js**: 16 이상
- **메모리**: 최소 2GB RAM
- **저장공간**: 최소 1GB

### 2. 백엔드 설정
```bash
cd backend

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 환경 설정 (API 키 불필요!)
cp .env.example .env

# 데이터베이스 초기화
cd ..
./init-db.sh
```

### 3. 프론트엔드 설정
```bash
# Node.js 의존성 설치
npm install

# 프로덕션 빌드
npm run build
```

### 4. 서버 시작
```bash
# 통합 시작 스크립트
./start.sh

# 또는 개별 실행
# 백엔드: cd backend && source venv/bin/activate && python start_backend.py
# 프론트엔드: npm run preview
```

## 🐳 Docker 배포 (선택사항)

### Docker Compose 사용
```bash
# Docker 컨테이너 빌드 및 시작
docker-compose up -d

# 서비스 확인
docker-compose ps
```

### 개별 Docker 빌드
```bash
# 백엔드 컨테이너
docker build -t database-ai-backend -f Dockerfile.backend .

# 프론트엔드 컨테이너  
docker build -t database-ai-frontend -f Dockerfile.frontend .
```

## 📊 Database AI 시스템 특징

### ✅ 완전 자립형
- **Claude API 키 불필요**
- **외부 의존성 제로**
- **100% 오프라인 작동 가능**

### 🧠 지능형 분석
- **318개 전문가 전략** 활용
- **워런 버핏, 피터 린치, 레이 달리오** 등 세계적 투자자 전략 융합
- **실시간 포트폴리오 최적화**

### 🎯 높은 신뢰도
- **67-71% 신뢰도 점수**
- **다단계 전략 매칭**
- **스마트 리스크 조정**

## 📱 API 사용법

### Database AI 전용 엔드포인트
```bash
curl -X POST "http://localhost:8003/database-ai/generate-strategy" \
-H "Content-Type: application/json" \
-d '{
  "user_profile": {
    "risk_tolerance": "moderate",
    "investment_goal": "wealth_building",
    "investment_horizon": 10
  },
  "current_holdings": []
}'
```

### 응답 예시
```json
{
  "status": "success",
  "strategy": {
    "portfolio_allocation": {
      "삼성전자": 0.15,
      "Apple": 0.12,
      "NVIDIA": 0.10,
      "장기채권": 0.08
    },
    "expected_return": "13.5-18.0%",
    "confidence_score": 0.67,
    "strategy_sources": ["레이 달리오", "피터 린치"],
    "strategy_type": "database_ai"
  }
}
```

## 🔧 관리 명령어

### 서비스 관리
```bash
./start.sh      # 서비스 시작
./stop.sh       # 서비스 중지  
./restart.sh    # 서비스 재시작
./status.sh     # 상태 확인
```

### 진단 및 디버깅
```bash
./check-server-config.sh    # 종합 시스템 진단
tail -f backend.log         # 백엔드 로그 실시간 확인
tail -f frontend.log        # 프론트엔드 로그 실시간 확인
```

### 데이터베이스 관리
```bash
./init-db.sh           # 데이터베이스 초기화
./quick-db-fix.sh      # 빠른 DB 수정
./fix-db-schema.sh     # 스키마 수정
```

## 🌍 프로덕션 배포 가이드

### Rocky Linux 서버 배포
```bash
# 1. 서버 접속
ssh user@your-server.com

# 2. 프로젝트 클론
git clone https://github.com/your-repo/database-ai-system.git
cd database-ai-system

# 3. 자동 배포 실행
chmod +x deploy-database-ai.sh
./deploy-database-ai.sh
```

### 방화벽 설정
```bash
# Rocky Linux/CentOS
sudo firewall-cmd --permanent --add-port=8003/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# Ubuntu
sudo ufw allow 8003
sudo ufw allow 8080
```

### 서비스 등록 (systemd)
```bash
# 백엔드 서비스 파일 생성
sudo tee /etc/systemd/system/database-ai-backend.service > /dev/null << 'EOF'
[Unit]
Description=Database AI Backend
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/database-ai-system/backend
ExecStart=/path/to/database-ai-system/backend/venv/bin/python start_backend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable database-ai-backend
sudo systemctl start database-ai-backend
```

## 📈 성능 최적화

### 데이터베이스 성능
```bash
# SQLite 성능 최적화
sqlite3 backend/expert_strategies.db "PRAGMA optimize;"
sqlite3 backend/asset_rebalancing.db "PRAGMA optimize;"
```

### 메모리 사용량 모니터링
```bash
# 메모리 사용량 확인
ps aux | grep -E "(python|node)" | head -10
free -h
```

## 🚨 문제 해결

### 일반적인 문제
1. **포트 충돌**: `./stop.sh` 실행 후 재시작
2. **데이터베이스 오류**: `./fix-db-schema.sh` 실행
3. **의존성 오류**: `./fix-dependencies.sh` 실행
4. **권한 오류**: `chmod +x *.sh` 실행

### 로그 확인
```bash
# 백엔드 로그
tail -50 backend.log | grep ERROR

# 프론트엔드 로그  
tail -50 frontend.log | grep ERROR

# 시스템 진단
./check-server-config.sh
```

## 🎯 핵심 장점

### 💰 비용 효율성
- **API 사용료 0원**
- **무제한 분석 요청**
- **월간 운영비 최소화**

### 🔒 데이터 보안
- **완전 오프라인 처리**
- **외부 API 호출 없음**
- **사용자 데이터 외부 유출 방지**

### ⚡ 빠른 응답속도
- **로컬 데이터베이스 처리**
- **네트워크 지연 없음**
- **실시간 전략 생성**

### 📊 전문가급 품질
- **318개 검증된 전략**
- **세계적 투자자 노하우**
- **지속적인 전략 업데이트**

---

## 📞 지원

- **GitHub Issues**: 버그 신고 및 기능 요청
- **문서**: 이 README 파일 참조
- **로그 분석**: `./check-server-config.sh` 실행 결과 제공

**🚀 Database AI 시스템으로 무료이면서도 전문가급 포트폴리오 분석을 경험해보세요!**
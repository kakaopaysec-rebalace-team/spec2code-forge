# 🐧 Rocky Linux Docker 배포 가이드

## 📋 개요

Rocky Linux Docker 환경에서 **Database AI 시스템**을 구동하기 위한 전용 가이드입니다.
API 키 없이도 318개 전문가 전략을 활용한 포트폴리오 분석이 가능합니다.

## 🚀 빠른 시작

### 1단계: 원클릭 배포
```bash
# 저장소 클론
git clone https://github.com/kakaopaysec-rebalace-team/spec2code-forge.git
cd spec2code-forge

# 권한 설정
chmod +x deploy-rocky-docker.sh

# Rocky Linux Docker 자동 배포
./deploy-rocky-docker.sh
```

### 2단계: 접속 확인
- **웹 애플리케이션**: http://localhost:8080
- **Database AI API**: http://localhost:8003/database-ai/generate-strategy
- **API 문서**: http://localhost:8003/docs

## 🔧 수동 설치 방법

### Docker 설치 (Rocky Linux)
```bash
# Docker 저장소 추가
sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo

# Docker 설치
sudo dnf install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
```

### 컨테이너 빌드 및 실행
```bash
# 이미지 빌드
docker compose -f docker-compose.rocky-linux.yml build

# 컨테이너 실행
docker compose -f docker-compose.rocky-linux.yml up -d
```

## 🐳 Docker 관리 명령어

### 기본 관리
```bash
# 컨테이너 상태 확인
docker ps

# 컨테이너 중지
docker compose -f docker-compose.rocky-linux.yml down

# 컨테이너 재시작  
docker compose -f docker-compose.rocky-linux.yml restart

# 로그 실시간 확인
docker compose -f docker-compose.rocky-linux.yml logs -f
```

### 고급 관리
```bash
# 컨테이너 내부 접속
docker exec -it database-ai-rocky-linux bash

# 리소스 사용량 확인
docker stats database-ai-rocky-linux

# 이미지 재빌드 (캐시 무시)
docker compose -f docker-compose.rocky-linux.yml build --no-cache

# 볼륨 포함 완전 삭제
docker compose -f docker-compose.rocky-linux.yml down -v
```

## 📊 컨테이너 사양

### 시스템 요구사항
- **CPU**: 2 코어 이상 권장
- **메모리**: 2GB 이상 권장  
- **저장공간**: 5GB 이상 권장
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상

### 포트 설정
- **8003**: Backend API 서버
- **8080**: Frontend 웹 서버

### 환경 변수
```yaml
environment:
  - NODE_ENV=production
  - PORT=8003
  - FRONTEND_PORT=8080
  - PYTHONUNBUFFERED=1
  - PYTHONDONTWRITEBYTECODE=1
```

## 🧪 테스트 방법

### 1. 헬스체크
```bash
curl http://localhost:8003/health
```

### 2. Database AI 사용법 확인
```bash
curl http://localhost:8003/database-ai/generate-strategy
```

### 3. 실제 전략 생성 테스트
```bash
curl -X POST "http://localhost:8003/database-ai/generate-strategy" \
-H "Content-Type: application/json" \
-d '{
  "user_profile": {
    "risk_tolerance": "moderate",
    "investment_goal": "wealth_building",
    "investment_horizon": 10
  }
}'
```

### 4. 응답 결과 예시
```json
{
  "status": "success",
  "strategy": {
    "portfolio_allocation": {
      "삼성전자": 0.15,
      "Apple": 0.12,
      "NVIDIA": 0.10
    },
    "expected_return": "13.5-18.0%",
    "confidence_score": 0.67,
    "strategy_sources": ["레이 달리오", "피터 린치"],
    "strategy_type": "database_ai"
  },
  "message": "Database AI 기반 전략 생성 완료 (API 키 불필요)"
}
```

## 🔍 문제 해결

### 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
docker logs database-ai-rocky-linux

# 포트 충돌 확인
sudo lsof -i :8003
sudo lsof -i :8080

# 기존 컨테이너 완전 제거 후 재시작
docker compose -f docker-compose.rocky-linux.yml down -v
./deploy-rocky-docker.sh --clean
```

### 서비스가 응답하지 않는 경우
```bash
# 컨테이너 내부 진단
docker exec -it database-ai-rocky-linux bash
cd /app
./rocky-linux-diagnostic.sh

# 프로세스 상태 확인
docker exec -it database-ai-rocky-linux ps aux
```

### 메모리 부족 현상
```bash
# 메모리 사용량 확인
docker stats database-ai-rocky-linux

# Docker 메모리 제한 설정 (docker-compose.yml 수정)
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

## 🌟 Docker 배포의 장점

### ✅ 완전한 격리
- **의존성 충돌 방지** - 호스트 시스템과 완전 분리
- **일관된 환경** - 개발/테스트/프로덕션 동일 환경
- **쉬운 배포** - 한 번의 명령으로 전체 시스템 구동

### ✅ Rocky Linux 최적화
- **Rocky Linux 9 베이스** - 최신 안정 버전
- **DNF 패키지 관리자** - 빠른 의존성 설치
- **SELinux 호환성** - 보안 정책 준수

### ✅ Database AI 특화
- **318개 전문가 전략** 미리 구축
- **API 키 불필요** - 완전 자립형 시스템
- **즉시 사용 가능** - 추가 설정 불요

## 📈 성능 최적화

### Docker 설정 최적화
```bash
# Docker daemon 메모리 설정
sudo systemctl edit docker
# 다음 내용 추가:
# [Service]
# ExecStart=
# ExecStart=/usr/bin/dockerd --default-runtime=runc --storage-opt dm.basesize=20G

# cgroup 메모리 제한 해제 (필요시)
sudo grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=0"
```

### 컨테이너 성능 튜닝
```yaml
# docker-compose.rocky-linux.yml에 추가
deploy:
  resources:
    limits:
      cpus: "2.0"
      memory: 4G
    reservations:
      cpus: "1.0"
      memory: 2G
```

## 🚀 프로덕션 배포

### 1. 방화벽 설정
```bash
sudo firewall-cmd --permanent --add-port=8003/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

### 2. 시스템 서비스 등록
```bash
# systemd 서비스 파일 생성
sudo tee /etc/systemd/system/database-ai-docker.service > /dev/null << EOF
[Unit]
Description=Database AI Docker Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/spec2code-forge
ExecStart=/usr/bin/docker compose -f docker-compose.rocky-linux.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.rocky-linux.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable database-ai-docker
sudo systemctl start database-ai-docker
```

### 3. 자동 업데이트 설정
```bash
# 업데이트 스크립트 생성
cat > update-database-ai.sh << 'EOF'
#!/bin/bash
cd /path/to/spec2code-forge
git pull origin main
docker compose -f docker-compose.rocky-linux.yml pull
docker compose -f docker-compose.rocky-linux.yml up -d --build
EOF

chmod +x update-database-ai.sh

# 크론탭 등록 (매주 일요일 새벽 3시)
echo "0 3 * * 0 /path/to/update-database-ai.sh" | crontab -
```

## 📞 지원

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **컨테이너 로그**: `docker logs database-ai-rocky-linux`
- **진단 도구**: 컨테이너 내부에서 `./rocky-linux-diagnostic.sh` 실행

---

**🐧 Rocky Linux + 🐳 Docker + 🤖 Database AI = 완벽한 조합!**

*API 키 없이도 세계적 수준의 포트폴리오 분석을 경험해보세요!*
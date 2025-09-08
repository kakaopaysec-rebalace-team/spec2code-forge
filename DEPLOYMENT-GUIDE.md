# 🚀 AI Asset Rebalancing System - 배포 가이드

여러 상황에 맞는 다양한 배포 옵션을 제공합니다.

## 🎯 배포 옵션 선택 가이드

### ✅ 권장 순서

1. **로컬 개발 서버** (가장 안전) → `./start.sh`
2. **직접 배포** (Docker + 로컬 빌드) → `./deploy-simple-direct.sh`  
3. **컨테이너 빌드** (완전 자동화) → `./deploy-container-build.sh`
4. **긴급 배포** (최후 수단) → `./deploy-emergency.sh`

---

## 🥇 1. 로컬 개발 서버 (권장)

가장 안정적이고 빠른 방법입니다.

```bash
./start.sh
```

**접속:**
- 프론트엔드: http://localhost:8080
- 백엔드: http://localhost:8003  
- API 문서: http://localhost:8003/docs

**특징:**
- ✅ 네트워크 문제 없음
- ✅ 실시간 개발 가능
- ✅ 빠른 시작
- ❌ 프로덕션 환경 아님

---

## 🥈 2. 직접 배포 (Docker + 로컬 빌드)

로컬에서 빌드 후 Docker 컨테이너로 배포합니다.

```bash
./deploy-simple-direct.sh
```

**전제 조건:**
- Docker 설치됨
- Node.js/npm 설치됨 (또는 dist/ 폴더 존재)

**과정:**
1. 로컬에서 프론트엔드 빌드
2. 최소한의 Python 패키지만 설치
3. Docker 이미지 생성 및 실행

**특징:**
- ✅ 네트워크 의존성 최소화
- ✅ 컨테이너 격리
- ✅ 포트 80으로 서비스
- ❌ 로컬 Node.js 필요

---

## 🥉 3. 컨테이너 빌드 (완전 자동화)

Docker 내부에서 모든 빌드를 수행합니다.

```bash
./deploy-container-build.sh
```

**특징:**
- ✅ 완전 자동화
- ✅ 다중 fallback 전략
- ✅ 오프라인 wheels 지원
- ❌ 네트워크 연결 필요
- ❌ DNS 문제 가능성

**Fallback 전략:**
1. 표준 PyPI
2. 중국 미러 서버들
3. 개별 패키지 설치
4. 필수 패키지만 설치

---

## 🚨 4. 긴급 배포 (최후 수단)

모든 방법이 실패했을 때 사용합니다.

```bash
./deploy-emergency.sh
```

**특징:**
- ✅ 최소한의 의존성
- ✅ HTTP 서버 fallback
- ✅ 기본 HTML 생성
- ❌ 기능 제한적

---

## 🛠️ 추가 도구

### 오프라인 Wheels 생성
```bash
./create-offline-wheels.sh
```
네트워크 연결이 있는 환경에서 실행하여 오프라인 패키지를 준비합니다.

### 시스템 관리
```bash
./stop.sh      # 시스템 중지
./restart.sh   # 시스템 재시작  
./status.sh    # 상태 확인
```

---

## 🔧 문제 해결

### DNS 문제
```bash
# Docker DNS 설정 확인
cat /etc/docker/daemon.json

# 수동 DNS 설정
echo '{"dns": ["8.8.8.8", "8.8.4.4"]}' > /etc/docker/daemon.json
systemctl restart docker
```

### 방화벽 문제
```bash
# 포트 80, 8000, 8003 열기
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --permanent --add-port=8003/tcp
firewall-cmd --reload
```

### Python 의존성 문제
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic
python app.py
```

---

## 📋 현재 상황별 추천

| 상황 | 추천 방법 | 명령어 |
|------|-----------|---------|
| 개발/테스트 | 로컬 서버 | `./start.sh` |
| 프로덕션 (네트워크 OK) | 컨테이너 빌드 | `./deploy-container-build.sh` |
| 프로덕션 (네트워크 문제) | 직접 배포 | `./deploy-simple-direct.sh` |
| 완전 오프라인 | 긴급 배포 | `./deploy-emergency.sh` |

---

## 🎉 성공 확인

배포 후 다음 URL들이 응답하는지 확인:

- `http://localhost/` - 메인 페이지
- `http://localhost/docs` - API 문서  
- `http://localhost/health` - 상태 확인

**모든 방법이 실패하면 GitHub Issues에 로그와 함께 문의해주세요!**
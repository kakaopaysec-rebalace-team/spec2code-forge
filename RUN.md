# 🚀 AI 리밸런싱 시스템 실행 가이드

## 빠른 시작

### 1. 시스템 시작
```bash
./start.sh
```

### 2. 시스템 상태 확인
```bash
./status.sh
```

### 3. 시스템 종료
```bash
./stop.sh
```

### 4. 시스템 재시작
```bash
./restart.sh
```

## 📱 접속 URL

- **메인 애플리케이션**: http://localhost:8080
- **백엔드 API**: http://localhost:8003  
- **API 문서**: http://localhost:8003/docs

## 🔧 문제 해결

### 포트가 이미 사용 중인 경우
```bash
# 먼저 프로세스 종료
./stop.sh

# 잠시 대기 후 재시작
./start.sh
```

### 로그 확인
```bash
# 백엔드 로그 확인
tail -f backend.log

# 프론트엔드 로그 확인  
tail -f frontend.log

# 실시간 로그 모니터링
tail -f backend.log frontend.log
```

### 수동 프로세스 확인
```bash
# 포트 사용 프로세스 확인
lsof -i:8003  # 백엔드
lsof -i:8080  # 프론트엔드

# 관련 프로세스 확인
ps aux | grep -E "(uvicorn|vite)"
```

## 💡 유용한 팁

1. **처음 실행 시**: `./start.sh`가 자동으로 가상환경과 의존성을 설정합니다.

2. **개발 중**: `./status.sh`로 시스템 상태를 수시로 확인할 수 있습니다.

3. **문제 발생 시**: `./restart.sh`로 전체 시스템을 깔끔하게 재시작할 수 있습니다.

4. **종료 시**: `./stop.sh`로 모든 관련 프로세스를 안전하게 종료할 수 있습니다.
#!/bin/bash

echo "🔍 Rocky Linux - Ollama 통신 상태 종합 점검"
echo "=================================================="

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 점검 결과 저장
RESULTS=()
ERROR_COUNT=0

# 로그 함수
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    RESULTS+=("✅ $1")
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    RESULTS+=("❌ $1")
    ((ERROR_COUNT++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    RESULTS+=("⚠️  $1")
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo ""
echo "1. 📋 시스템 기본 정보"
echo "===================="
log_info "OS 정보: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
log_info "커널 버전: $(uname -r)"
log_info "현재 시간: $(date '+%Y-%m-%d %H:%M:%S')"
log_info "서버 IP: $(hostname -I | awk '{print $1}')"

echo ""
echo "2. 🔌 네트워크 연결 점검"
echo "======================"

# 포트 11434 상태 확인
if ss -tlnp | grep -q ":11434"; then
    PORT_INFO=$(ss -tlnp | grep ":11434")
    log_success "포트 11434 활성화됨"
    log_info "포트 상세: $PORT_INFO"
else
    log_error "포트 11434가 비활성화 상태"
    log_info "해결방법: systemctl start ollama 또는 ollama serve"
fi

# localhost 연결 테스트
if curl -s --connect-timeout 3 http://localhost:11434 >/dev/null 2>&1; then
    log_success "localhost:11434 연결 가능"
else
    log_error "localhost:11434 연결 실패"
fi

echo ""
echo "3. 🤖 Ollama 서비스 상태"
echo "======================"

# systemctl 상태 확인
if systemctl is-active --quiet ollama 2>/dev/null; then
    log_success "Ollama systemd 서비스 활성화됨"
    OLLAMA_STATUS=$(systemctl status ollama --no-pager -l | head -10)
    log_info "서비스 상태:"
    echo "$OLLAMA_STATUS" | while read line; do
        echo "    $line"
    done
else
    log_warning "Ollama systemd 서비스가 비활성화되었거나 수동 실행 중"
fi

# 프로세스 확인
if pgrep -f "ollama" >/dev/null; then
    OLLAMA_PROC=$(ps aux | grep ollama | grep -v grep)
    log_success "Ollama 프로세스 실행 중"
    log_info "프로세스 정보:"
    echo "$OLLAMA_PROC" | while read line; do
        echo "    $line"
    done
else
    log_error "Ollama 프로세스가 실행되지 않음"
fi

echo ""
echo "4. 📦 설치된 모델 확인"
echo "===================="

# API를 통한 모델 목록 조회
MODEL_RESPONSE=$(curl -s --connect-timeout 10 http://localhost:11434/api/tags 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$MODEL_RESPONSE" ]; then
    MODEL_COUNT=$(echo "$MODEL_RESPONSE" | grep -o '"name"' | wc -l)
    if [ "$MODEL_COUNT" -gt 0 ]; then
        log_success "모델 목록 조회 성공 - $MODEL_COUNT개 모델 설치됨"
        
        # 모델 상세 정보 파싱
        echo "$MODEL_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for model in data.get('models', []):
        name = model.get('name', 'Unknown')
        size = model.get('size', 0)
        size_mb = size // 1000000
        modified = model.get('modified_at', '')[:19].replace('T', ' ')
        print(f'    📦 {name} ({size_mb}MB) - 수정일: {modified}')
except:
    pass
" 2>/dev/null || log_info "모델 상세 정보 파싱 실패"
    else
        log_warning "설치된 모델이 없습니다"
    fi
else
    log_error "모델 목록 조회 실패 - Ollama API 응답 없음"
fi

echo ""
echo "5. 🧪 실제 AI 생성 테스트"
echo "======================="

# 실제 생성 테스트
log_info "AI 생성 테스트 시작 (최대 60초 대기)..."

AI_TEST_START=$(date +%s)
AI_RESPONSE=$(timeout 60 curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama3.1:8b",
        "prompt": "안녕하세요. 한국 투자자를 위한 간단한 조언 한 줄 부탁해요.",
        "stream": false,
        "options": {"temperature": 0.1, "max_tokens": 50}
    }' 2>/dev/null)

AI_TEST_END=$(date +%s)
AI_TEST_DURATION=$((AI_TEST_END - AI_TEST_START))

if [ $? -eq 0 ] && [ -n "$AI_RESPONSE" ]; then
    # 응답에서 실제 텍스트 추출
    AI_TEXT=$(echo "$AI_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    response = data.get('response', '').strip()
    if response:
        print(response[:100] + ('...' if len(response) > 100 else ''))
except:
    pass
" 2>/dev/null)
    
    if [ -n "$AI_TEXT" ]; then
        log_success "AI 생성 테스트 성공 (소요시간: ${AI_TEST_DURATION}초)"
        log_info "응답 내용: $AI_TEXT"
    else
        log_error "AI 응답은 받았으나 내용이 비어있음"
        log_info "원본 응답: ${AI_RESPONSE:0:200}..."
    fi
else
    log_error "AI 생성 테스트 실패 (소요시간: ${AI_TEST_DURATION}초)"
    if [ "$AI_TEST_DURATION" -ge 60 ]; then
        log_warning "타임아웃 발생 - Ollama가 과부하 상태이거나 응답이 느림"
    fi
fi

echo ""
echo "6. 🔧 Python 환경 점검"
echo "===================="

# Python 패키지 확인
if python3 -c "import requests" 2>/dev/null; then
    log_success "requests 패키지 설치됨"
else
    log_error "requests 패키지 미설치"
    log_info "설치방법: pip install requests"
fi

if python3 -c "import httpx" 2>/dev/null; then
    log_success "httpx 패키지 설치됨"
else
    log_warning "httpx 패키지 미설치 (비동기 통신용)"
    log_info "설치방법: pip install httpx"
fi

if python3 -c "import ollama" 2>/dev/null; then
    log_success "ollama 패키지 설치됨"
else
    log_warning "ollama 패키지 미설치 (선택사항)"
    log_info "설치방법: pip install ollama"
fi

echo ""
echo "7. 💾 시스템 리소스 상태"
echo "======================="

# 메모리 사용량
MEMORY_INFO=$(free -h | grep "Mem:")
log_info "메모리 상태: $MEMORY_INFO"

# 디스크 사용량 (Ollama 모델 저장 위치)
DISK_INFO=$(df -h /home 2>/dev/null || df -h /)
log_info "디스크 상태:"
echo "$DISK_INFO" | while read line; do
    echo "    $line"
done

# CPU 로드
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}')
log_info "CPU 로드 평균:$LOAD_AVG"

echo ""
echo "8. 🔍 방화벽 및 보안 점검"
echo "======================="

# firewalld 상태
if systemctl is-active --quiet firewalld; then
    log_info "firewalld 활성화됨"
    if firewall-cmd --list-ports 2>/dev/null | grep -q "11434"; then
        log_success "포트 11434가 방화벽에서 허용됨"
    else
        log_warning "포트 11434가 방화벽에서 차단될 수 있음"
        log_info "허용방법: firewall-cmd --add-port=11434/tcp --permanent && firewall-cmd --reload"
    fi
else
    log_info "firewalld 비활성화됨"
fi

# SELinux 상태
if command -v getenforce >/dev/null 2>&1; then
    SELINUX_STATUS=$(getenforce 2>/dev/null)
    log_info "SELinux 상태: $SELINUX_STATUS"
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        log_warning "SELinux가 강제 모드로 실행 중 - 통신 문제 가능성"
    fi
fi

echo ""
echo "📊 점검 결과 요약"
echo "================"

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 모든 점검 항목이 정상입니다!${NC}"
    echo "Ollama가 정상적으로 작동하고 있습니다."
else
    echo -e "${RED}⚠️  $ERROR_COUNT 개의 문제가 발견되었습니다.${NC}"
    echo "아래 해결방법을 참고하세요:"
    echo ""
    echo "주요 해결방법:"
    echo "1. Ollama 서비스 시작: systemctl start ollama"
    echo "2. Ollama 수동 실행: ollama serve"
    echo "3. 모델 설치: ollama pull llama3.1:8b"
    echo "4. Python 패키지: pip install requests httpx"
    echo "5. 방화벽 허용: firewall-cmd --add-port=11434/tcp --permanent"
fi

echo ""
echo "상세 점검 결과:"
printf '%s\n' "${RESULTS[@]}"

echo ""
echo "점검 완료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "로그 저장 위치: 이 스크립트 출력을 파일로 리다이렉트하여 저장 가능"
echo "사용법: ./test-ollama-rocky.sh > ollama-check-$(date +%Y%m%d-%H%M%S).log 2>&1"
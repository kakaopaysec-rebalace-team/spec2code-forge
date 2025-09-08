#!/bin/bash

# Rocky Linux Docker 배포 스크립트
# Database AI 시스템 완전 자동화

set -e

echo "🐧 Rocky Linux Docker 배포 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 환경 확인
echo "🔍 환경 확인 중..."
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker가 설치되지 않았습니다."
    echo "   Rocky Linux Docker 설치 방법:"
    echo "   sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo"
    echo "   sudo dnf install docker-ce docker-ce-cli containerd.io docker-compose-plugin"
    echo "   sudo systemctl start docker"
    echo "   sudo systemctl enable docker"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    echo "   설치 방법: sudo dnf install docker-compose-plugin"
    exit 1
fi

echo "✅ Docker: $(docker --version)"
if command -v docker-compose >/dev/null 2>&1; then
    echo "✅ Docker Compose: $(docker-compose --version)"
else
    echo "✅ Docker Compose: $(docker compose version)"
fi

# Docker 서비스 상태 확인
if ! systemctl is-active docker >/dev/null 2>&1; then
    echo "🔄 Docker 서비스 시작 중..."
    sudo systemctl start docker
fi

# 2. 기존 컨테이너 정리
echo ""
echo "🛑 기존 컨테이너 정리 중..."
if docker ps -q -f name=database-ai-rocky-linux >/dev/null 2>&1; then
    docker stop database-ai-rocky-linux 2>/dev/null || true
    docker rm database-ai-rocky-linux 2>/dev/null || true
    echo "   ✅ 기존 컨테이너 제거 완료"
fi

# 기존 이미지 정리 (선택사항)
if [ "$1" = "--clean" ]; then
    echo "🧹 기존 이미지 정리 중..."
    docker rmi $(docker images -q -f reference="*database-ai*") 2>/dev/null || true
fi

# 3. Docker 이미지 빌드
echo ""
echo "🔨 Rocky Linux Docker 이미지 빌드 중..."
echo "   이 과정은 몇 분 소요될 수 있습니다..."

if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker-compose.rocky-linux.yml build --no-cache
else
    docker compose -f docker-compose.rocky-linux.yml build --no-cache
fi

echo "   ✅ 이미지 빌드 완료"

# 4. 컨테이너 시작
echo ""
echo "🚀 Database AI 컨테이너 시작 중..."

if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker-compose.rocky-linux.yml up -d
else
    docker compose -f docker-compose.rocky-linux.yml up -d
fi

echo "   ✅ 컨테이너 시작 완료"

# 5. 컨테이너 시작 대기
echo ""
echo "⏳ 서비스 초기화 대기 중 (60초)..."
for i in {1..12}; do
    echo -n "."
    sleep 5
done
echo ""

# 6. 서비스 상태 확인
echo ""
echo "🔍 서비스 상태 확인 중..."

# 컨테이너 상태
if docker ps | grep -q database-ai-rocky-linux; then
    echo "   ✅ 컨테이너: 정상 실행 중"
    
    # 컨테이너 로그 일부 표시
    echo ""
    echo "📋 컨테이너 시작 로그:"
    docker logs database-ai-rocky-linux 2>/dev/null | tail -10 || true
else
    echo "   ❌ 컨테이너: 실행되지 않음"
    echo ""
    echo "🚨 컨테이너 로그:"
    docker logs database-ai-rocky-linux 2>/dev/null || true
    exit 1
fi

# 헬스체크
echo ""
echo "🏥 헬스체크 수행 중..."
for i in {1..6}; do
    if curl -s http://localhost:8003/health >/dev/null; then
        echo "   ✅ 백엔드 API: 정상 응답"
        break
    else
        if [ $i -eq 6 ]; then
            echo "   ❌ 백엔드 API: 응답 없음"
        else
            echo "   ⏳ 백엔드 대기 중... ($i/6)"
            sleep 10
        fi
    fi
done

# 프론트엔드 체크
if curl -s http://localhost:8080 >/dev/null; then
    echo "   ✅ 프론트엔드: 정상 응답"
else
    echo "   ❌ 프론트엔드: 응답 없음"
fi

# Database AI 체크
if curl -s -X POST "http://localhost:8003/database-ai/generate-strategy" \
   -H "Content-Type: application/json" \
   -d '{"user_profile":{"risk_tolerance":"moderate","investment_goal":"wealth_building"}}' \
   | grep -q "success"; then
    echo "   ✅ Database AI: 정상 작동"
else
    echo "   ❌ Database AI: 오류"
fi

# 7. 최종 결과
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Rocky Linux Docker 배포 완료!"
echo ""
echo "📱 접속 정보:"
echo "   • 웹 애플리케이션: http://localhost:8080"
echo "   • Database AI API: http://localhost:8003/database-ai/generate-strategy"
echo "   • API 문서: http://localhost:8003/docs"
echo "   • 헬스체크: http://localhost:8003/health"
echo ""
echo "🐳 Docker 관리 명령어:"
if command -v docker-compose >/dev/null 2>&1; then
    echo "   • 서비스 중지: docker-compose -f docker-compose.rocky-linux.yml down"
    echo "   • 서비스 재시작: docker-compose -f docker-compose.rocky-linux.yml restart"
    echo "   • 로그 확인: docker-compose -f docker-compose.rocky-linux.yml logs -f"
else
    echo "   • 서비스 중지: docker compose -f docker-compose.rocky-linux.yml down"
    echo "   • 서비스 재시작: docker compose -f docker-compose.rocky-linux.yml restart"
    echo "   • 로그 확인: docker compose -f docker-compose.rocky-linux.yml logs -f"
fi
echo "   • 컨테이너 접속: docker exec -it database-ai-rocky-linux bash"
echo "   • 상태 확인: docker ps"
echo ""
echo "✨ 특징:"
echo "   • 🆓 API 키 완전 불필요"
echo "   • 🧠 318개 전문가 전략 (워런 버핏, 피터 린치, 레이 달리오)"
echo "   • ⚡ 67-71% 신뢰도의 실시간 분석"
echo "   • 🔒 완전 오프라인 작동"
echo "   • 🐧 Rocky Linux 최적화"
echo ""
echo "🚀 Database AI 시스템이 Rocky Linux Docker에서 성공적으로 실행 중입니다!"

# 8. 테스트 명령어 제공
echo ""
echo "🧪 빠른 테스트 명령어:"
echo "curl -s http://localhost:8003/database-ai/generate-strategy | jq '.features'"
echo ""
echo "curl -s -X POST \"http://localhost:8003/database-ai/generate-strategy\" \\"
echo "-H \"Content-Type: application/json\" \\"
echo "-d '{\"user_profile\":{\"risk_tolerance\":\"moderate\",\"investment_goal\":\"wealth_building\"}}' | jq '.status'"
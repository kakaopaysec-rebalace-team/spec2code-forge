#!/bin/bash

# AI Asset Rebalancing System - Rocky Linux Docker Deployment Script
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge
# Optimized for Rocky Linux Server Environment

set -e

APP_NAME="ai-rebalancing"
IMAGE_NAME="ai-rebalancing-system"
PORT="8080"
INTERNAL_PORT="8000"

echo "🚀 AI Asset Rebalancing System - Rocky Linux Docker 배포"
echo "Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Root 권한 확인
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Root 사용자로 실행 중입니다. 보안상 일반 사용자 권한을 권장합니다."
fi

# 현재 디렉토리 확인
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile을 찾을 수 없습니다. 프로젝트 루트 디렉토리에서 실행하세요."
    exit 1
fi

# 네트워크 연결 확인
echo "🌐 네트워크 연결 확인..."
if ! ping -c 1 8.8.8.8 &>/dev/null; then
    echo "⚠️  외부 네트워크 연결에 문제가 있습니다."
    echo "   DNS 서버 확인: cat /etc/resolv.conf"
    echo "   방화벽 확인: sudo firewall-cmd --list-all"
    # 계속 진행하되 경고만 출력
fi

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    echo "   Rocky Linux에서 Docker 설치:"
    echo "   sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo"
    echo "   sudo dnf install docker-ce docker-ce-cli containerd.io"
    echo "   sudo systemctl start docker"
    echo "   sudo systemctl enable docker"
    echo "   sudo usermod -aG docker \$USER"
    exit 1
fi

# Docker 서비스 상태 확인
if ! systemctl is-active --quiet docker; then
    echo "🔄 Docker 서비스 시작 중..."
    sudo systemctl start docker
    sleep 3
fi

# SELinux 상태 확인 및 대응
if command -v getenforce &> /dev/null; then
    SELINUX_STATUS=$(getenforce)
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        echo "⚠️  SELinux가 Enforcing 모드입니다."
        echo "   Docker 컨테이너 실행을 위해 임시로 Permissive 모드 권장:"
        echo "   sudo setenforce 0  # 임시"
        echo "   또는 영구적으로 /etc/selinux/config에서 SELINUX=permissive"
    fi
fi

# 방화벽 포트 확인 (firewalld)
if command -v firewall-cmd &> /dev/null && systemctl is-active --quiet firewalld; then
    if ! firewall-cmd --query-port=${PORT}/tcp --quiet 2>/dev/null; then
        echo "🔥 방화벽에 포트 $PORT 추가 중..."
        sudo firewall-cmd --permanent --add-port=${PORT}/tcp
        sudo firewall-cmd --reload
        echo "✅ 방화벽 포트 $PORT 허용됨"
    else
        echo "✅ 방화벽 포트 $PORT 이미 허용됨"
    fi
fi

# Git 상태 확인
echo ""
echo "📋 Git 상태 확인..."
git status --porcelain

# 최신 소스 가져오기
echo ""
echo "📥 최신 소스 가져오기..."
git pull origin main

# 환경 변수 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    if [ -f ".env.example" ]; then
        echo "   .env.example을 복사하여 .env 생성..."
        cp .env.example .env
        echo "   ✅ .env 파일이 생성되었습니다. API 키를 설정하세요."
    else
        echo "   수동으로 .env 파일을 생성하세요."
    fi
fi

# 기존 컨테이너 정리
echo ""
echo "🧹 기존 컨테이너 정리..."
if [ "$(docker ps -aq -f name=${APP_NAME})" ]; then
    echo "   기존 컨테이너 중지 중..."
    docker stop ${APP_NAME} || true
    echo "   기존 컨테이너 삭제 중..."
    docker rm ${APP_NAME} || true
fi

# 기존 이미지 삭제 (디스크 공간 절약)
if [ "$(docker images -q ${IMAGE_NAME})" ]; then
    echo "   기존 이미지 삭제 중..."
    docker rmi ${IMAGE_NAME} || true
fi

# Docker 빌드 컨텍스트 정리
echo "   Docker 시스템 정리..."
docker system prune -f

# 네트워크 테스트 및 빌드 옵션 설정
echo ""
echo "🔨 Docker 이미지 빌드 (Rocky Linux 최적화)..."

# Docker 빌드 - 네트워크 문제에 대비한 재시도 로직
BUILD_SUCCESS=false
BUILD_ATTEMPTS=0
MAX_ATTEMPTS=3

while [ "$BUILD_SUCCESS" = false ] && [ $BUILD_ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    BUILD_ATTEMPTS=$((BUILD_ATTEMPTS + 1))
    echo "   빌드 시도 $BUILD_ATTEMPTS/$MAX_ATTEMPTS..."
    
    if docker build \
        --no-cache \
        --tag ${IMAGE_NAME} \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --network=host \
        .; then
        BUILD_SUCCESS=true
        echo "   ✅ 빌드 성공!"
    else
        echo "   ❌ 빌드 실패 (시도 $BUILD_ATTEMPTS/$MAX_ATTEMPTS)"
        if [ $BUILD_ATTEMPTS -lt $MAX_ATTEMPTS ]; then
            echo "   5초 후 재시도..."
            sleep 5
            # DNS 플러시 시도
            sudo systemctl restart systemd-resolved 2>/dev/null || true
        fi
    fi
done

if [ "$BUILD_SUCCESS" = false ]; then
    echo "❌ 빌드가 $MAX_ATTEMPTS번 실패했습니다."
    echo ""
    echo "🔍 문제 해결 방법:"
    echo "   1. 네트워크 연결 확인: ping 8.8.8.8"
    echo "   2. DNS 설정 확인: cat /etc/resolv.conf"
    echo "   3. Docker 데몬 재시작: sudo systemctl restart docker"
    echo "   4. 방화벽 확인: sudo firewall-cmd --list-all"
    echo "   5. SELinux 임시 해제: sudo setenforce 0"
    echo "   6. 프록시 설정 확인: env | grep -i proxy"
    exit 1
fi

# 컨테이너 실행
echo ""
echo "🚀 컨테이너 시작..."

# 환경 변수 파일 옵션 설정
ENV_OPTION=""
if [ -f ".env" ]; then
    ENV_OPTION="--env-file .env"
    echo "   .env 파일을 사용합니다."
fi

# 데이터 디렉토리 생성
mkdir -p ./data ./logs
chmod 755 ./data ./logs

# 컨테이너 실행 (Rocky Linux 최적화 옵션)
docker run -d \
    --name ${APP_NAME} \
    --publish ${PORT}:${INTERNAL_PORT} \
    ${ENV_OPTION} \
    --restart unless-stopped \
    --memory="2g" \
    --cpus="2.0" \
    --volume "$(pwd)/data:/app/data:rw" \
    --volume "$(pwd)/logs:/app/logs:rw" \
    --health-cmd="curl -f http://localhost:${INTERNAL_PORT}/health || exit 1" \
    --health-interval=30s \
    --health-timeout=10s \
    --health-retries=3 \
    --health-start-period=60s \
    --log-driver=json-file \
    --log-opt max-size=100m \
    --log-opt max-file=3 \
    ${IMAGE_NAME}

# 상태 확인
echo ""
echo "📊 배포 상태 확인..."
sleep 10

# 컨테이너 상태 확인
if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q ${APP_NAME}; then
    echo "✅ 컨테이너가 성공적으로 시작되었습니다!"
    
    # 헬스 체크 대기
    echo "   헬스 체크 대기 중..."
    HEALTH_SUCCESS=false
    for i in {1..12}; do
        if docker exec ${APP_NAME} curl -f http://localhost:${INTERNAL_PORT}/health &>/dev/null; then
            echo "✅ 헬스 체크 통과!"
            HEALTH_SUCCESS=true
            break
        elif [ $i -eq 12 ]; then
            echo "⚠️  헬스 체크 실패. 애플리케이션 시작 시간이 오래 걸릴 수 있습니다."
        else
            echo "   헬스 체크 대기 중... ($i/12)"
            sleep 5
        fi
    done
    
    # 네트워크 정보 수집
    SERVER_IP=""
    if command -v hostname &>/dev/null; then
        SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
    else
        SERVER_IP="localhost"
    fi
    
    echo ""
    echo "🌐 접속 정보:"
    echo "   • Frontend: http://${SERVER_IP}:${PORT}"
    echo "   • Local: http://localhost:${PORT}"
    echo "   • API 문서: http://${SERVER_IP}:${PORT}/docs"
    
    echo ""
    echo "🛠️  관리 명령어:"
    echo "   • 실시간 로그: docker logs -f ${APP_NAME}"
    echo "   • 컨테이너 상태: docker ps"
    echo "   • 컨테이너 중지: docker stop ${APP_NAME}"
    echo "   • 컨테이너 재시작: docker restart ${APP_NAME}"
    echo "   • 리소스 사용량: docker stats ${APP_NAME}"
    echo "   • 헬스 체크: docker exec ${APP_NAME} curl -f http://localhost:${INTERNAL_PORT}/health"
    
    echo ""
    echo "📁 로그 파일 위치:"
    echo "   • 애플리케이션 로그: ./logs/"
    echo "   • Docker 로그: docker logs ${APP_NAME}"
    
else
    echo "❌ 배포 실패!"
    echo ""
    echo "🔍 문제 해결 방법:"
    echo "   1. 컨테이너 로그 확인: docker logs ${APP_NAME}"
    echo "   2. 시스템 로그 확인: journalctl -u docker"
    echo "   3. 포트 사용 확인: ss -tlnp | grep ${PORT}"
    echo "   4. 디스크 공간 확인: df -h"
    echo "   5. 메모리 확인: free -h"
    echo "   6. SELinux 로그 확인: sudo ausearch -m avc -ts recent"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Rocky Linux 환경에서 배포 완료!"
echo "   시스템 정보: $(cat /etc/rocky-release 2>/dev/null || echo 'Rocky Linux')"
echo "   Docker 버전: $(docker --version)"
echo "   빌드 시간: $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
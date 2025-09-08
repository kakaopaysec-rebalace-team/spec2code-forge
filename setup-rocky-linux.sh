#!/bin/bash

# AI Asset Rebalancing System - Rocky Linux Environment Setup Script
# Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge
# Rocky Linux 서버 환경 설정 자동화 스크립트

set -e

echo "🏔️  AI Asset Rebalancing System - Rocky Linux 환경 설정"
echo "Repository: https://github.com/kakaopaysec-rebalace-team/spec2code-forge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Root 권한 확인
if [[ $EUID -ne 0 ]]; then
    echo "❌ 이 스크립트는 root 권한으로 실행해야 합니다: sudo $0"
    exit 1
fi

# Rocky Linux 버전 확인
if [ -f "/etc/rocky-release" ]; then
    echo "✅ Rocky Linux 확인됨: $(cat /etc/rocky-release)"
else
    echo "⚠️  Rocky Linux가 아닌 시스템에서 실행 중입니다."
fi

# 시스템 업데이트
echo ""
echo "📦 시스템 패키지 업데이트..."
dnf update -y

# 필수 패키지 설치
echo ""
echo "🛠️  필수 패키지 설치..."
dnf install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    firewalld \
    policycoreutils-python-utils \
    yum-utils \
    device-mapper-persistent-data \
    lvm2

# Docker 설치
echo ""
echo "🐳 Docker 설치..."

# Docker 저장소 추가
if [ ! -f "/etc/yum.repos.d/docker-ce.repo" ]; then
    echo "   Docker 저장소 추가 중..."
    dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
fi

# Docker 설치
echo "   Docker 패키지 설치 중..."
dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin

# Docker 서비스 시작 및 활성화
echo "   Docker 서비스 설정 중..."
systemctl start docker
systemctl enable docker

# Docker 그룹에 사용자 추가 (현재 sudo를 실행한 사용자)
ORIGINAL_USER=${SUDO_USER:-$USER}
if [ "$ORIGINAL_USER" != "root" ]; then
    echo "   사용자 '$ORIGINAL_USER'를 docker 그룹에 추가 중..."
    usermod -aG docker $ORIGINAL_USER
    echo "   ✅ 로그아웃 후 재로그인하여 docker 명령어를 사용하세요."
fi

# Git 설치 및 설정 확인
echo ""
echo "📝 Git 설정 확인..."
if ! git --version &>/dev/null; then
    echo "   Git 설치 중..."
    dnf install -y git
fi

# Git 글로벌 설정 확인 (선택사항)
if [ "$ORIGINAL_USER" != "root" ]; then
    echo "   Git 사용자 설정을 확인하세요:"
    echo "   sudo -u $ORIGINAL_USER git config --global user.name 'Your Name'"
    echo "   sudo -u $ORIGINAL_USER git config --global user.email 'your.email@example.com'"
fi

# 방화벽 설정
echo ""
echo "🔥 방화벽 설정..."
systemctl start firewalld
systemctl enable firewalld

# 포트 8080 허용
echo "   포트 8080 허용 중..."
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload
echo "   ✅ 포트 8080이 허용되었습니다."

# SELinux 설정
echo ""
echo "🛡️  SELinux 설정..."
SELINUX_STATUS=$(getenforce)
echo "   현재 SELinux 상태: $SELINUX_STATUS"

if [ "$SELINUX_STATUS" = "Enforcing" ]; then
    echo "   SELinux가 Enforcing 모드입니다."
    echo "   Docker와의 호환성을 위해 포트 허용 중..."
    semanage port -a -t http_port_t -p tcp 8080 2>/dev/null || echo "   포트 8080이 이미 허용되어 있습니다."
fi

# Node.js 설치 (선택사항 - 개발 환경용)
echo ""
echo "📦 Node.js 설치 (개발 환경용)..."
if ! node --version &>/dev/null; then
    echo "   Node.js 18 설치 중..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
    dnf install -y nodejs
    echo "   ✅ Node.js 설치 완료: $(node --version)"
    echo "   ✅ npm 설치 완료: $(npm --version)"
else
    echo "   ✅ Node.js가 이미 설치되어 있습니다: $(node --version)"
fi

# Python 3 및 pip 설치
echo ""
echo "🐍 Python 환경 설정..."
if ! python3 --version &>/dev/null; then
    echo "   Python 3 설치 중..."
    dnf install -y python3 python3-pip python3-venv
fi
echo "   ✅ Python 설치 완료: $(python3 --version)"
echo "   ✅ pip 설치 완료: $(pip3 --version)"

# 시스템 정보 표시
echo ""
echo "📊 시스템 정보:"
echo "   • OS: $(cat /etc/rocky-release 2>/dev/null || echo 'Unknown')"
echo "   • Kernel: $(uname -r)"
echo "   • Docker: $(docker --version 2>/dev/null || echo 'Not installed')"
echo "   • Git: $(git --version 2>/dev/null || echo 'Not installed')"
echo "   • Node.js: $(node --version 2>/dev/null || echo 'Not installed')"
echo "   • Python: $(python3 --version 2>/dev/null || echo 'Not installed')"
echo "   • 메모리: $(free -h | grep '^Mem:' | awk '{print $2}')"
echo "   • 디스크: $(df -h / | grep -v Filesystem | awk '{print $4}') 사용 가능"

# 설치 완료 안내
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Rocky Linux 환경 설정 완료!"
echo ""
echo "📋 다음 단계:"
echo "   1. 로그아웃 후 재로그인하여 Docker 권한 적용"
echo "   2. 프로젝트 클론: git clone https://github.com/kakaopaysec-rebalace-team/spec2code-forge"
echo "   3. 프로젝트 디렉토리로 이동: cd spec2code-forge"
echo "   4. 환경 변수 설정: cp .env.example .env && vi .env"
echo "   5. 배포 실행: ./deploy.sh"
echo ""
echo "🔧 유용한 명령어:"
echo "   • Docker 상태 확인: systemctl status docker"
echo "   • 방화벽 상태 확인: firewall-cmd --list-all"
echo "   • SELinux 상태 확인: sestatus"
echo "   • 시스템 리소스 확인: htop"
echo ""
echo "⚠️  보안 권장사항:"
echo "   • SSH 키 기반 인증 사용"
echo "   • 불필요한 포트 차단"
echo "   • 정기적인 시스템 업데이트"
echo "   • fail2ban 설치 고려"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
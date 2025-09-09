#!/bin/bash

echo "🔧 포트 80 설정 안내 (Rocky Linux)"
echo "=================================="

echo "⚠️ 포트 80은 관리자 권한이 필요한 특권 포트입니다."
echo ""

echo "🔐 방법 1: sudo로 실행 (권장)"
echo "sudo ./start-rocky.sh"
echo ""

echo "🔥 방법 2: 방화벽 포트 허용"
echo "sudo firewall-cmd --permanent --add-service=http"
echo "sudo firewall-cmd --permanent --add-port=80/tcp"
echo "sudo firewall-cmd --reload"
echo ""

echo "🚪 방법 3: 포트 권한 설정 (고급)"
echo "sudo setcap CAP_NET_BIND_SERVICE=+eip /usr/bin/node"
echo "또는"
echo "sudo sysctl net.ipv4.ip_unprivileged_port_start=80"
echo ""

echo "📋 확인 방법:"
echo "sudo ss -tlnp | grep :80"
echo "curl http://localhost"
echo "curl http://$(hostname -I | awk '{print $1}')"
echo ""

echo "✨ 포트 80 접속 후 URL:"
echo "🌐 http://$(hostname -I | awk '{print $1}') (포트 번호 없이 접속 가능!)"
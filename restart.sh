#!/bin/bash

echo "🔄 시스템 재시작 중..."

# 기존 프로세스 종료
./stop.sh

# 잠시 대기
sleep 3

# 시스템 시작
./start.sh
#!/bin/bash

# AI Asset Rebalancing System - Manual Build Script
# 수동 단계별 빌드 및 진단 스크립트

echo "🔧 수동 빌드 및 진단 스크립트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 환경 확인
echo "1️⃣  환경 확인"
echo "   Node.js: $(node --version 2>/dev/null || echo '❌ 설치되지 않음')"
echo "   npm: $(npm --version 2>/dev/null || echo '❌ 설치되지 않음')"
echo "   Docker: $(docker --version 2>/dev/null || echo '❌ 설치되지 않음')"
echo "   현재 디렉토리: $(pwd)"
echo "   Git 브랜치: $(git branch --show-current 2>/dev/null || echo '❌ Git 저장소 아님')"

# 2. package.json 확인
echo ""
echo "2️⃣  package.json 확인"
if [ -f "package.json" ]; then
    echo "   ✅ package.json 존재"
    echo "   프로젝트명: $(grep -o '"name": "[^"]*' package.json | cut -d'"' -f4)"
    echo "   빌드 스크립트:"
    grep -A 10 '"scripts"' package.json | grep -E '(build|dev)' | head -5
else
    echo "   ❌ package.json 없음"
    exit 1
fi

# 3. Vite 설정 확인
echo ""
echo "3️⃣  Vite 설정 확인"
if [ -f "vite.config.ts" ]; then
    echo "   ✅ vite.config.ts 존재"
    echo "   빌드 설정:"
    grep -A 5 -B 5 "build" vite.config.ts | head -10
elif [ -f "vite.config.js" ]; then
    echo "   ✅ vite.config.js 존재"
    echo "   빌드 설정:"
    grep -A 5 -B 5 "build" vite.config.js | head -10
else
    echo "   ❌ vite.config 파일 없음"
fi

# 4. 기존 파일 정리
echo ""
echo "4️⃣  기존 파일 정리"
if [ -d "node_modules" ]; then
    echo "   node_modules 삭제 중..."
    rm -rf node_modules
fi
if [ -d "dist" ]; then
    echo "   기존 dist 삭제 중..."
    rm -rf dist
fi
if [ -d "build" ]; then
    echo "   기존 build 삭제 중..."
    rm -rf build
fi
echo "   ✅ 정리 완료"

# 5. npm 설치
echo ""
echo "5️⃣  npm 의존성 설치"
echo "   명령어 실행: npm install"
if npm install; then
    echo "   ✅ npm install 성공"
    echo "   설치된 패키지 수: $(find node_modules -maxdepth 1 -type d | wc -l)"
else
    echo "   ❌ npm install 실패"
    echo "   package-lock.json 삭제 후 재시도..."
    rm -f package-lock.json
    if npm install; then
        echo "   ✅ 재시도 성공"
    else
        echo "   ❌ 재시도도 실패"
        exit 1
    fi
fi

# 6. 개발 의존성 확인
echo ""
echo "6️⃣  중요 개발 의존성 확인"
echo "   Vite: $(npm list vite 2>/dev/null | grep vite || echo '❌ 설치되지 않음')"
echo "   TypeScript: $(npm list typescript 2>/dev/null | grep typescript || echo '❌ 설치되지 않음')"
echo "   React: $(npm list react 2>/dev/null | grep react | head -1 || echo '❌ 설치되지 않음')"

# 7. 빌드 실행 (상세 로그)
echo ""
echo "7️⃣  빌드 실행 (상세 모드)"
echo "   명령어 실행: npm run build"
echo "   ─────────────────────────────────────────────────────────"

if npm run build; then
    echo "   ─────────────────────────────────────────────────────────"
    echo "   ✅ npm run build 성공"
else
    echo "   ─────────────────────────────────────────────────────────"
    echo "   ❌ npm run build 실패"
    
    # 대체 빌드 시도
    echo ""
    echo "   대체 빌드 시도: npx vite build"
    if npx vite build; then
        echo "   ✅ npx vite build 성공"
    else
        echo "   ❌ npx vite build도 실패"
        exit 1
    fi
fi

# 8. 빌드 결과 확인
echo ""
echo "8️⃣  빌드 결과 확인"

# dist 디렉토리 확인
if [ -d "dist" ]; then
    echo "   ✅ dist 디렉토리 존재"
    echo "   파일 수: $(find dist -type f | wc -l)"
    echo "   전체 크기: $(du -sh dist | cut -f1)"
    echo ""
    echo "   주요 파일들:"
    ls -la dist/ | head -10
    
    # index.html 내용 확인
    if [ -f "dist/index.html" ]; then
        echo ""
        echo "   index.html 내용 확인:"
        head -10 dist/index.html | grep -E "(title|script|link)" || echo "   기본 HTML 구조"
        
        # 업데이트된 내용 확인
        if grep -qi "rebalancing\|strategy\|portfolio" dist/index.html; then
            echo "   ✅ 업데이트된 키워드 발견"
        else
            echo "   ⚠️  업데이트된 키워드 없음"
        fi
    else
        echo "   ❌ index.html 없음"
    fi
    
elif [ -d "build" ]; then
    echo "   ✅ build 디렉토리 존재 (dist 대신)"
    echo "   dist로 이름 변경 중..."
    mv build dist
    echo "   파일 수: $(find dist -type f | wc -l)"
    echo "   전체 크기: $(du -sh dist | cut -f1)"
else
    echo "   ❌ 빌드 결과물 없음 (dist, build 모두 없음)"
    echo ""
    echo "   현재 디렉토리 내용:"
    ls -la | grep -E "(dist|build|out)"
    exit 1
fi

# 9. Docker 파일 확인
echo ""
echo "9️⃣  Docker 파일 확인"
if [ -f "Dockerfile.offline" ]; then
    echo "   ✅ Dockerfile.offline 존재"
    echo "   프론트엔드 복사 라인:"
    grep -n "COPY dist" Dockerfile.offline || echo "   COPY dist 라인 없음"
else
    echo "   ❌ Dockerfile.offline 없음"
fi

# 10. 최종 확인
echo ""
echo "🔟 최종 배포 준비 상태"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

READY=true

if [ ! -d "dist" ]; then
    echo "   ❌ dist 디렉토리 없음"
    READY=false
fi

if [ ! -f "dist/index.html" ]; then
    echo "   ❌ dist/index.html 없음"
    READY=false
fi

if [ ! -f "Dockerfile.offline" ]; then
    echo "   ❌ Dockerfile.offline 없음"
    READY=false
fi

if [ "$READY" = true ]; then
    echo "   ✅ 모든 준비 완료!"
    echo ""
    echo "   다음 단계:"
    echo "   1. Docker 빌드 테스트: docker build -f Dockerfile.offline -t test-image ."
    echo "   2. 전체 배포 실행: ./deploy-offline.sh"
else
    echo "   ❌ 배포 준비 미완료"
    echo ""
    echo "   필요한 조치:"
    echo "   - npm run build가 성공적으로 dist 디렉토리를 생성하는지 확인"
    echo "   - Dockerfile.offline이 올바른 경로를 참조하는지 확인"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
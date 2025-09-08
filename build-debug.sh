#!/bin/bash

# AI Asset Rebalancing System - Build Debug Script
# npm run build 실패 원인 정확한 진단

echo "🔍 Build Debug - npm run build 실패 원인 분석"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 현재 상태 확인
echo "📋 현재 상태:"
echo "   현재 디렉토리: $(pwd)"
echo "   dist 디렉토리: $([ -d "dist" ] && echo "✅ 존재" || echo "❌ 없음")"
echo "   build 디렉토리: $([ -d "build" ] && echo "✅ 존재" || echo "❌ 없음")"

# Node.js 환경 재확인
echo ""
echo "🔧 Node.js 환경:"
echo "   Node.js: $(node --version)"
echo "   npm: $(npm --version)"
echo "   현재 PATH: $PATH"

# package.json 빌드 스크립트 정확한 확인
echo ""
echo "📦 package.json 빌드 설정:"
if [ -f "package.json" ]; then
    echo "   빌드 스크립트:"
    grep -A 3 -B 1 '"build"' package.json
    
    echo ""
    echo "   전체 scripts 섹션:"
    sed -n '/"scripts"/,/}/p' package.json
else
    echo "   ❌ package.json 없음"
    exit 1
fi

# vite.config 파일 상세 확인
echo ""
echo "⚙️  Vite 설정 파일:"
if [ -f "vite.config.ts" ]; then
    echo "   vite.config.ts 내용:"
    cat vite.config.ts
elif [ -f "vite.config.js" ]; then
    echo "   vite.config.js 내용:"
    cat vite.config.js
else
    echo "   ❌ vite.config 파일 없음"
fi

# 기존 파일 완전 정리
echo ""
echo "🧹 완전 정리:"
rm -rf node_modules dist build .vite
echo "   모든 관련 디렉토리 삭제 완료"

# npm cache 완전 정리
echo ""
echo "💾 npm 캐시 완전 정리:"
npm cache clean --force
npm cache verify
echo "   npm 캐시 정리 완료"

# npm 설치 (자세한 로그)
echo ""
echo "📥 npm 설치 (상세 모드):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if npm install --verbose; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   ✅ npm install 성공"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   ❌ npm install 실패"
    exit 1
fi

# vite 명령어 직접 확인
echo ""
echo "🔨 Vite 명령어 확인:"
echo "   npx vite --version:"
npx vite --version 2>&1 || echo "   ❌ vite 명령어 없음"

echo ""
echo "   node_modules/.bin/vite 확인:"
if [ -f "node_modules/.bin/vite" ]; then
    echo "   ✅ node_modules/.bin/vite 존재"
    ./node_modules/.bin/vite --version
else
    echo "   ❌ node_modules/.bin/vite 없음"
fi

# 빌드 시도 1: npm run build
echo ""
echo "🚀 빌드 시도 1: npm run build"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
BUILD1_SUCCESS=false
if npm run build 2>&1; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    BUILD1_SUCCESS=true
    echo "   ✅ npm run build 명령어 완료"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   ❌ npm run build 실패"
fi

# 결과 확인
echo ""
echo "📊 빌드 결과 확인 (시도 1):"
if [ -d "dist" ]; then
    echo "   ✅ dist 디렉토리 생성됨"
    echo "   파일 수: $(find dist -type f | wc -l)"
    ls -la dist/
elif [ -d "build" ]; then
    echo "   ✅ build 디렉토리 생성됨 (dist 아님)"
    echo "   파일 수: $(find build -type f | wc -l)"
    ls -la build/
else
    echo "   ❌ 빌드 결과물 없음"
    
    echo ""
    echo "   현재 디렉토리 상태:"
    ls -la | grep -E "(dist|build|out|public)"
fi

# 빌드 시도 2: npx vite build (직접)
if [ "$BUILD1_SUCCESS" = false ]; then
    echo ""
    echo "🚀 빌드 시도 2: npx vite build"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if npx vite build 2>&1; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "   ✅ npx vite build 성공"
        
        echo ""
        echo "📊 빌드 결과 확인 (시도 2):"
        if [ -d "dist" ]; then
            echo "   ✅ dist 디렉토리 생성됨"
            echo "   파일 수: $(find dist -type f | wc -l)"
            ls -la dist/
        elif [ -d "build" ]; then
            echo "   ✅ build 디렉토리 생성됨"
            echo "   파일 수: $(find build -type f | wc -l)"
            ls -la build/
        else
            echo "   ❌ 여전히 빌드 결과물 없음"
        fi
        
    else
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "   ❌ npx vite build도 실패"
    fi
fi

# 빌드 시도 3: 노드 모듈 직접 실행
if [ ! -d "dist" ] && [ ! -d "build" ]; then
    echo ""
    echo "🚀 빌드 시도 3: node_modules/.bin/vite build"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if [ -f "node_modules/.bin/vite" ]; then
        if ./node_modules/.bin/vite build 2>&1; then
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "   ✅ 직접 vite 실행 성공"
        else
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "   ❌ 직접 vite 실행도 실패"
        fi
    else
        echo "   ❌ node_modules/.bin/vite 파일 없음"
    fi
fi

# TypeScript 컴파일 확인
echo ""
echo "📝 TypeScript 확인:"
if command -v tsc &>/dev/null; then
    echo "   TypeScript 버전: $(tsc --version)"
    echo "   TypeScript 컴파일 테스트:"
    npx tsc --noEmit 2>&1 | head -10
else
    echo "   ❌ TypeScript 컴파일러 없음"
fi

# 최종 상태 보고
echo ""
echo "📋 최종 진단 보고"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "dist" ]; then
    echo "✅ SUCCESS: dist 디렉토리 생성됨"
    echo "   파일 수: $(find dist -type f | wc -l)"
    echo "   총 크기: $(du -sh dist | cut -f1)"
    echo "   index.html: $([ -f "dist/index.html" ] && echo "존재" || echo "없음")"
    echo ""
    echo "🐳 Docker 빌드 테스트 권장:"
    echo "   docker build -f Dockerfile.offline -t test-build ."
elif [ -d "build" ]; then
    echo "⚠️  WARNING: build 디렉토리 생성됨 (dist 아님)"
    echo "   build를 dist로 이동 필요: mv build dist"
    echo "   파일 수: $(find build -type f | wc -l)"
    echo "   총 크기: $(du -sh build | cut -f1)"
else
    echo "❌ FAILURE: 빌드 결과물 생성 실패"
    echo ""
    echo "🔍 추가 확인 사항:"
    echo "   1. 소스 파일 존재 확인: ls -la src/"
    echo "   2. index.html 템플릿: ls -la index.html"
    echo "   3. TypeScript 오류: npx tsc --noEmit"
    echo "   4. Vite 설정 문제: Vite 설정에서 build.outDir 확인"
    echo ""
    echo "🛠️  권장 해결 방법:"
    echo "   1. vite.config.ts에서 build.outDir 명시적 설정"
    echo "   2. src/main.tsx 파일 존재 확인"
    echo "   3. index.html의 script src 경로 확인"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
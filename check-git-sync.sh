#!/bin/bash

echo "🔍 GitHub 동기화 상태 종합 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 현재 브랜치와 원격 정보
echo "📍 Git 정보:"
echo "  현재 브랜치: $(git branch --show-current)"
echo "  원격 저장소: $(git remote -v | head -1)"

# 커밋 동기화 상태 확인
echo ""
echo "📊 커밋 동기화 상태:"
AHEAD=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo "0")
BEHIND=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")

if [ "$AHEAD" -eq 0 ] && [ "$BEHIND" -eq 0 ]; then
    echo "  ✅ 로컬과 원격이 완전히 동기화됨"
elif [ "$AHEAD" -gt 0 ]; then
    echo "  ⚠️  원격에 $AHEAD 개의 새로운 커밋이 있음 (pull 필요)"
elif [ "$BEHIND" -gt 0 ]; then
    echo "  ⚠️  로컬에 $BEHIND 개의 커밋이 있음 (push 필요)"
fi

# 작업 디렉토리 상태
echo ""
echo "💼 작업 디렉토리 상태:"
if [ -z "$(git status --porcelain)" ]; then
    echo "  ✅ 모든 변경사항이 커밋됨"
else
    echo "  ⚠️  커밋되지 않은 변경사항 있음:"
    git status --porcelain | while read line; do
        echo "    $line"
    done
fi

# 추적되지 않는 파일들 확인
echo ""
echo "📁 추적되지 않는 파일들:"
UNTRACKED=$(git ls-files --others --exclude-standard)
if [ -z "$UNTRACKED" ]; then
    echo "  ✅ 모든 파일이 추적 중이거나 무시됨"
else
    echo "  ⚠️  추적되지 않는 파일들:"
    echo "$UNTRACKED" | while read file; do
        echo "    📄 $file"
    done
fi

# 최근 커밋 히스토리
echo ""
echo "📝 최근 커밋 (5개):"
git log --oneline -5 | while read line; do
    echo "  $line"
done

# 원격 비교
echo ""
echo "🔄 원격과의 차이점:"
if git diff --quiet HEAD origin/$(git branch --show-current) 2>/dev/null; then
    echo "  ✅ 원격과 차이점 없음"
else
    echo "  ⚠️  원격과 다른 내용 있음"
    echo "  변경된 파일:"
    git diff --name-only HEAD origin/$(git branch --show-current) 2>/dev/null | while read file; do
        echo "    📝 $file"
    done || echo "    (원격 브랜치를 찾을 수 없음)"
fi

# 중요 파일들 존재 확인
echo ""
echo "📋 중요 파일들 존재 확인:"
IMPORTANT_FILES=(
    "src/pages/ProfileSetup.tsx"
    "src/pages/Rebalancing.tsx" 
    "src/pages/Results.tsx"
    "src/pages/Strategies.tsx"
    "backend/app.py"
    "start.sh"
    "stop.sh"
    "CLAUDE.md"
    "RUN.md"
)

for file in "${IMPORTANT_FILES[@]}"; do
    if [ -f "$file" ]; then
        if git ls-files --error-unmatch "$file" > /dev/null 2>&1; then
            echo "  ✅ $file (Git 추적 중)"
        else
            echo "  ⚠️  $file (Git 추적 안됨)"
        fi
    else
        echo "  ❌ $file (파일 없음)"
    fi
done

# 결론
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 종합 결과:"

if [ -z "$(git status --porcelain)" ] && [ "$AHEAD" -eq 0 ] && [ "$BEHIND" -eq 0 ]; then
    echo "  🎉 모든 소스가 GitHub에 완전히 업로드됨"
elif [ "$BEHIND" -gt 0 ]; then
    echo "  📤 로컬 변경사항을 GitHub에 push 필요"
    echo "      명령어: git push origin $(git branch --show-current)"
elif [ "$AHEAD" -gt 0 ]; then
    echo "  📥 GitHub의 새로운 변경사항을 pull 필요"
    echo "      명령어: git pull origin $(git branch --show-current)"
elif [ ! -z "$(git status --porcelain)" ]; then
    echo "  💾 변경사항을 먼저 커밋 필요"
    echo "      명령어: git add . && git commit -m '업데이트' && git push"
else
    echo "  ✅ 동기화 상태 양호"
fi
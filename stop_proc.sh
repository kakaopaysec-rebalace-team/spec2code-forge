# 프로세스 이름 기반 종료
     echo "🔄 프로세스 이름 기반 종료 중..."
     pkill -f "npm run dev" 2>/dev/null || echo "npm run dev 프로세스가 없습니다."
     pkill -f "vite" 2>/dev/null || echo "vite 프로세스가 없습니다."
     pkill -f "uvicorn" 2>/dev/null || echo "uvicorn 프로세스가 없습니다."
     pkill -f "python.*app.py" 2>/dev/null || echo "Python app.py 프로세스가 없습니다."
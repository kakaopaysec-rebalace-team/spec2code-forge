# Multi-stage build for React + FastAPI application
FROM node:18-alpine as frontend-builder

# 프론트엔드 빌드
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Python 백엔드와 정적 파일 서빙
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 코드 복사
COPY backend/ ./backend/

# 프론트엔드 빌드 결과물 복사
COPY --from=frontend-builder /app/dist ./frontend/dist/

# 환경변수 설정
ENV PYTHONPATH=/app/backend
ENV PORT=8000
ENV HOST=0.0.0.0

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# 포트 노출
EXPOSE $PORT

# 백엔드 서버 실행 (정적 파일도 서빙)
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
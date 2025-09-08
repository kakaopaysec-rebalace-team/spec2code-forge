# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered asset rebalancing system built with React, TypeScript, and shadcn/ui frontend connected to a FastAPI backend. The application helps users analyze their investment strategies and provides AI-driven portfolio rebalancing recommendations using Claude AI integration. It features Korean language content and focuses on investment portfolio optimization.

## Development Commands

### Frontend (React + Vite)
```bash
# Start development server (runs on port 8080)
npm run dev

# Build for production
npm run build

# Build for development mode
npm run build:dev

# Run ESLint
npm run lint

# Preview production build
npm run preview
```

### Backend (FastAPI + Python)
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (required for Python 3.13)
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies from requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

# Start backend server (runs on port 8000)
source venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Or use the startup script
python start_backend.py
```

## 🚀 Quick Start (추천)

### 자동 스크립트 사용

```bash
# 시스템 시작 (백엔드 + 프론트엔드 자동 시작)
./start.sh

# 시스템 종료
./stop.sh

# 시스템 재시작
./restart.sh

# 시스템 상태 확인
./status.sh
```

## Full System Startup (수동)

1. **Backend Setup**:
   ```bash
   cd backend
   cp .env.example .env  # Edit with your API keys
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python start_backend.py
   ```

2. **Frontend Setup** (separate terminal):
   ```bash
   npm run dev
   ```

3. **Access Points**:
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000 (note: start.sh uses port 8003)
   - API Docs: http://localhost:8000/docs

## Tech Stack & Architecture

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite with SWC plugin
- **UI Framework**: shadcn/ui components built on Radix UI
- **Styling**: Tailwind CSS with custom design tokens
- **Routing**: React Router DOM
- **State Management**: TanStack Query for server state
- **Forms**: React Hook Form with Zod validation
- **Icons**: Lucide React
- **Charts**: Recharts for data visualization
- **HTTP Client**: Axios for API communication

### Backend
- **Framework**: FastAPI with Python 3.8+
- **Data Processing**: Pandas, NumPy, yfinance for market data
- **AI Integration**: Anthropic Claude API for strategy generation
- **Web Scraping**: BeautifulSoup4, requests for content analysis
- **Document Processing**: PyPDF2 for file analysis
- **Research Integration**: arXiv API for academic papers
- **Database**: SQLite with aiosqlite for async operations
- **Machine Learning**: scikit-learn, scipy for portfolio optimization
- **Technical Analysis**: TA library for financial indicators

## Project Structure

```
/
├── src/                    # Frontend source
│   ├── pages/
│   │   ├── Index.tsx       # Landing page
│   │   ├── ProfileSetup.tsx # User input & portfolio setup
│   │   ├── Results.tsx     # AI analysis results
│   │   ├── Rebalancing.tsx # Portfolio rebalancing interface
│   │   ├── Strategies.tsx  # Investment strategies page
│   │   └── NotFound.tsx    # 404 page
│   ├── components/ui/      # shadcn/ui components
│   ├── hooks/              # Custom React hooks
│   └── lib/
│       ├── api.ts          # Backend API integration
│       └── utils.ts        # Utility functions
└── backend/                # Backend API
    ├── app.py              # FastAPI main application
    ├── data_processor.py   # Market data collection & processing
    ├── ai_model_trainer.py # Claude AI integration & strategy generation
    ├── simulation_analyzer.py # Portfolio simulation & analysis
    ├── user_data_processor.py # User document/URL processing
    ├── database_manager.py # Database operations & management
    ├── strategy_learner.py # ML strategy learning algorithms
    ├── init_strategies.py  # Strategy initialization
    ├── start_backend.py    # Backend startup script
    ├── requirements.txt    # Python dependencies
    ├── .env.example        # Environment configuration template
    ├── *.db                # SQLite database files
    ├── logs/               # Application logs
    └── uploads/            # User uploaded files
```

## API Integration

The frontend connects to the backend through `src/lib/api.ts` which provides:
- `analyzePortfolio()` - Main portfolio analysis endpoint
- `getMarketData()` - Real-time market data
- `analyzeUserData()` - Process user documents/URLs
- `healthCheck()` - Backend status verification
- `getUserHoldings()` - Get user's portfolio holdings
- `getAllStrategies()` - Retrieve available investment strategies
- `getStrategyTemplates()` - Get predefined strategy templates
- `createHolding()`, `updateHolding()`, `deleteHolding()` - Holdings management

## Key Features Implementation

1. **Portfolio Analysis Flow**:
   - User fills ProfileSetup form → API call to `/analyze`
   - Backend processes with Claude AI → Returns strategy + simulation
   - Results displayed with charts and recommendations

2. **AI Strategy Generation**:
   - Uses Claude API for investment strategy recommendations
   - Processes user-provided documents, URLs, and text
   - Generates personalized portfolio allocations

3. **Market Data Integration**:
   - Real-time data from yfinance (Yahoo Finance)
   - Korean stock market support (KRX symbols)
   - Historical performance simulation

4. **User Data Processing**:
   - PDF document analysis
   - Web scraping for investment content
   - Text-based investment philosophy parsing

## Environment Configuration

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
VITE_ENV=development
```

### Backend (.env)
```bash
# Core Application
APP_NAME="AI Asset Rebalancing System"
DEBUG=True
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# AI/ML Services
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Financial Data APIs
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
FINNHUB_API_KEY=your_finnhub_api_key_here
MARKETSTACK_API_KEY=your_marketstack_api_key_here

# Web Search & Content
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# Database
DATABASE_URL=asset_rebalancing.db

# CORS Configuration
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000
```

## Deployment & Docker

The project includes comprehensive deployment configurations:

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Manual Docker build
docker build -t ai-rebalancing .

# Run the container
docker run -p 8080:8080 -p 8000:8000 ai-rebalancing
```

### Deployment Scripts
- `./deploy.sh` - Main deployment script
- `./deploy-offline.sh` - Offline deployment for network-restricted environments
- `./deploy-ultimate.sh` - Ultimate deployment solution
- `./setup-rocky-linux.sh` - Rocky Linux server setup
- Various debugging and troubleshooting scripts

## Development Notes

- **CORS**: Backend configured to allow localhost:8080 for frontend development
- **Error Handling**: Both frontend and backend have comprehensive error handling
- **Data Flow**: Analysis results stored in sessionStorage for Results page
- **API Timeout**: 30-second timeout for analysis requests
- **Mock Data**: Backend provides fallback mock data when external APIs fail
- **Korean Support**: Full Korean language UI with Korean stock symbol mapping
- **Security**: API keys stored in environment variables, never in code
- **Port Configuration**: Frontend runs on 8080, backend on 8000 (or 8003 with start.sh)
- **Database**: SQLite databases for user data, strategies, and simulation results
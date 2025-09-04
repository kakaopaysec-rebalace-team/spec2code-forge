import axios from 'axios';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout for analysis requests
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    if (error.response?.status === 500) {
      console.error('Server Error:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// Types
export interface UserProfile {
  investment_style: 'conservative' | 'moderate' | 'aggressive';
  investment_goal: 'retirement' | 'wealth' | 'income' | 'growth';
  investment_period: 'short' | 'medium' | 'long';
}

export interface PortfolioItem {
  stock: string;
  weight: number;
}

export interface UserData {
  text?: string;
  url?: string;
  file_content?: string;
}

export interface AnalysisRequest {
  user_id: string;
  user_profile: UserProfile;
  current_portfolio: PortfolioItem[];
  user_data?: UserData;
}

export interface RebalancingResponse {
  status: string;
  strategy: {
    portfolio_allocation: Record<string, number>;
    actions: Array<{
      action: string;
      stock: string;
      target_weight?: number;
      current_weight?: number;
      difference?: number;
      reason?: string;
    }>;
    rationale: string;
    expected_return: string;
    risk_level: string;
    generated_at: string;
  };
  simulation: {
    simulation_period_days: number;
    current_portfolio: {
      metrics: {
        total_return: number;
        annual_return: number;
        volatility: number;
        sharpe_ratio: number;
        max_drawdown: number;
        win_rate: number;
      };
      portfolio: Record<string, number>;
    };
    recommended_strategy: {
      metrics: {
        total_return: number;
        annual_return: number;
        volatility: number;
        sharpe_ratio: number;
        max_drawdown: number;
        win_rate: number;
      };
      portfolio: Record<string, number>;
    };
    comparison: {
      annual_return_improvement: number;
      volatility_improvement: number;
      sharpe_ratio_improvement: number;
      max_drawdown_improvement: number;
      overall_score: number;
    };
    performance_chart_data: Array<{
      date: string;
      user_portfolio: number;
      ai_strategy: number;
      benchmark: number;
    }>;
    generated_at: string;
  };
  rationale: string;
}

export interface MarketDataResponse {
  symbol: string;
  data: {
    symbol: string;
    name: string;
    current_price: number;
    change: number;
    change_percent: number;
    volume: number;
    market_cap: number;
    sector: string;
    pe_ratio?: number;
    dividend_yield?: number;
  };
}

// API functions
export const healthCheck = async (): Promise<{ status: string; timestamp: string }> => {
  const response = await api.get('/health');
  return response.data;
};

export const analyzePortfolio = async (request: AnalysisRequest): Promise<RebalancingResponse> => {
  const response = await api.post('/analyze', request);
  return response.data;
};

export const getMarketData = async (symbol: string): Promise<MarketDataResponse> => {
  const response = await api.get(`/market-data/${encodeURIComponent(symbol)}`);
  return response.data;
};

export const analyzeUserData = async (userData: UserData) => {
  const response = await api.post('/user-data/analyze', userData);
  return response.data;
};

export const getStrategyTemplates = async () => {
  const response = await api.get('/strategies/templates');
  return response.data;
};

// Utility functions
export const generateUserId = (): string => {
  return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const formatPortfolioForAPI = (portfolio: Array<{ stock: string; weight: string }>): PortfolioItem[] => {
  return portfolio
    .filter(item => item.stock && item.weight && parseFloat(item.weight) > 0)
    .map(item => ({
      stock: item.stock,
      weight: parseFloat(item.weight)
    }));
};

export const normalizePortfolioWeights = (portfolio: PortfolioItem[]): PortfolioItem[] => {
  const totalWeight = portfolio.reduce((sum, item) => sum + item.weight, 0);
  if (totalWeight === 0) return portfolio;
  
  return portfolio.map(item => ({
    ...item,
    weight: item.weight / totalWeight
  }));
};

export default api;
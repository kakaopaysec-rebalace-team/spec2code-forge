import axios from 'axios';

// API configuration with dynamic host detection
const getApiBaseUrl = () => {
  // 환경변수가 있으면 사용
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // 브라우저에서 현재 호스트 감지
  if (typeof window !== 'undefined') {
    const currentHost = window.location.hostname;
    // localhost나 127.0.0.1인 경우 8003 포트 사용
    if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
      return `http://localhost:8003`;
    }
    // 다른 호스트인 경우 해당 호스트의 8003 포트 사용
    return `http://${currentHost}:8003`;
  }
  
  // 기본값
  return 'http://localhost:8003';
};

const API_BASE_URL = getApiBaseUrl();

// Only log in development
if (import.meta.env.DEV) {
  console.log('API: Base URL configured as:', API_BASE_URL);
  console.log('API: Environment VITE_API_URL:', import.meta.env.VITE_API_URL);
}

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
    if (import.meta.env.DEV) {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    }
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
    if (import.meta.env.DEV) {
      console.log(`API Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
      if (response.data && response.config.url?.includes('strategies')) {
        console.log('API Strategies count:', response.data.strategies?.length || 0);
      }
      if (response.data && response.config.url?.includes('holdings')) {
        console.log('API Holdings count:', response.data.holdings?.length || 0, 'Total value:', response.data.total_value);
      }
    }
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    if (import.meta.env.DEV) {
      console.error('API Error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url
      });
    }
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

export interface Holding {
  holding_id: string;
  user_id: string;
  symbol: string;
  name: string;
  quantity: number;
  purchase_price: number;
  current_price: number;
  market_value: number;
  weight: number;
  sector?: string;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface HoldingsResponse {
  status: string;
  user_id: string;
  holdings: Holding[];
  total_value: number;
  count: number;
}

export interface RebalancingStrategy {
  strategy_id: string;
  strategy_name: string;
  strategy_type: string;
  description: string;
  target_allocation: Record<string, number>;
  expected_return: number;
  volatility: number;
  max_drawdown: number;
  sharpe_ratio: number;
  risk_level: string;
  tags: string[];
  user_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StrategiesResponse {
  status: string;
  strategies: RebalancingStrategy[];
  count: number;
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

// User data upload functions
export const uploadUserText = async (userId: string, content: string, dataType: 'text' | 'url') => {
  const response = await api.post(`/user-data/upload?user_id=${userId}`, {
    data_type: dataType,
    content: content
  });
  return response.data;
};

export const uploadUserFile = async (userId: string, file: File) => {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('file', file);
  
  const response = await api.post('/user-data/upload-file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getUserData = async (userId: string) => {
  const response = await api.get(`/users/${userId}/data`);
  return response.data;
};

export const getStrategyTemplates = async () => {
  const response = await api.get('/strategies/templates');
  return response.data;
};

export const getUserHoldings = async (userId: string): Promise<HoldingsResponse> => {
  const response = await api.get(`/users/${userId}/holdings`);
  return response.data;
};

export const getAllStrategies = async (userId?: string): Promise<StrategiesResponse> => {
  const params = userId ? { user_id: userId } : {};
  const response = await api.get('/strategies', { params });
  return response.data;
};

export const getStrategyDetails = async (strategyId: string): Promise<{ status: string; strategy: RebalancingStrategy }> => {
  const response = await api.get(`/strategies/${strategyId}`);
  return response.data;
};

export const createHolding = async (userId: string, holdingData: Partial<Holding>) => {
  const response = await api.post(`/users/${userId}/holdings`, holdingData);
  return response.data;
};

export const updateHoldingPrices = async (userId: string, priceUpdates: Record<string, number>) => {
  const response = await api.put(`/users/${userId}/holdings/prices`, priceUpdates);
  return response.data;
};

export const deleteHolding = async (holdingId: string) => {
  const response = await api.delete(`/holdings/${holdingId}`);
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
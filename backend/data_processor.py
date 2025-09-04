import pandas as pd
import numpy as np
import yfinance as yf
import requests
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import json
from urllib.parse import quote_plus
import time

load_dotenv()
logger = logging.getLogger(__name__)

class DataProcessor:
    """
    데이터 수집 및 전처리 모듈
    KRX, investing.com 등에서 API를 통해 데이터를 정기적으로 수집하고 정제합니다.
    AI 모델 학습을 위한 추가 소스(웹, 문서, 논문)의 데이터를 처리할 수 있는 기능 포함
    """
    
    def __init__(self):
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY")
        self.marketstack_api_key = os.getenv("MARKETSTACK_API_KEY")
        self.google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.investing_base_url = "https://investing.com"
        
        # Major US stock symbols (S&P 500 focus)
        self.major_us_stocks = {
            "Apple": "AAPL",
            "Microsoft": "MSFT",
            "Alphabet": "GOOGL", 
            "Amazon": "AMZN",
            "Tesla": "TSLA",
            "NVIDIA": "NVDA",
            "Meta": "META",
            "Berkshire Hathaway": "BRK-B",
            "Visa": "V",
            "Johnson & Johnson": "JNJ",
            "Walmart": "WMT",
            "UnitedHealth": "UNH",
            "Exxon Mobil": "XOM",
            "Home Depot": "HD",
            "Procter & Gamble": "PG",
            "JPMorgan Chase": "JPM",
            "Chevron": "CVX",
            "Mastercard": "MA",
            "AbbVie": "ABBV",
            "Pfizer": "PFE",
            "Coca-Cola": "KO",
            "Merck": "MRK",
            "Intel": "INTC",
            "Cisco": "CSCO",
            "Netflix": "NFLX",
            "Salesforce": "CRM",
            "Broadcom": "AVGO",
            "Oracle": "ORCL",
            "Comcast": "CMCSA",
            "AMD": "AMD"
        }
        
        # Stock sectors for diversified portfolios
        self.stock_sectors = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "INTC", "CSCO", "ORCL", "CRM", "AMD"],
            "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "CVS", "LLY", "TMO", "DHR", "BMY"],
            "Financial": ["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "AXP", "SCHW", "C"],
            "Consumer": ["AMZN", "WMT", "HD", "PG", "KO", "PEP", "COST", "MCD", "NKE", "SBUX"],
            "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "MPC", "OXY", "KMI"],
            "Industrial": ["GE", "CAT", "BA", "UPS", "HON", "RTX", "LMT", "MMM", "FDX", "UNP"]
        }
        
        # Sector mapping
        self.sector_mapping = {
            "기술": "Technology",
            "금융": "Financial Services",
            "제조": "Manufacturing",
            "화학": "Chemical",
            "자동차": "Automotive",
            "엔터테인먼트": "Entertainment",
            "바이오": "Biotechnology"
        }

    async def collect_and_process_data(self, stock_ticker_list: List[str]) -> pd.DataFrame:
        """
        메인 데이터 수집 및 전처리 함수
        
        Args:
            stock_ticker_list: 분석할 종목 코드 리스트
            
        Returns:
            dataframe: AI 학습에 적합한 형태로 가공된 데이터프레임
        """
        try:
            logger.info(f"Starting data collection for {len(stock_ticker_list)} stocks")
            
            # 1. 기본 시장 데이터 수집
            market_data = await self.get_market_data(stock_ticker_list)
            
            # 2. KRX API 데이터 수집 (if available)
            if self.krx_api_key:
                krx_data = await self.get_krx_data(stock_ticker_list)
                market_data = self._merge_krx_data(market_data, krx_data)
            
            # 3. investing.com 데이터 수집
            investing_data = await self.get_investing_data(stock_ticker_list)
            market_data = self._merge_investing_data(market_data, investing_data)
            
            # 4. 데이터 정제 및 전처리
            processed_data = self._preprocess_for_ai(market_data)
            
            logger.info(f"Data collection completed. Shape: {processed_data.shape}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error in collect_and_process_data: {str(e)}")
            raise

    async def get_market_data(self, stock_list: List[str]) -> pd.DataFrame:
        """
        주식 리스트에 대한 시장 데이터 수집 (Yahoo Finance 기반)
        """
        try:
            logger.info(f"Fetching market data for {len(stock_list)} stocks")
            
            # Convert Korean names to symbols
            symbols = []
            for stock in stock_list:
                if stock in self.korean_stocks:
                    symbols.append(self.korean_stocks[stock])
                else:
                    # Assume it's already a symbol
                    symbols.append(stock if '.' in stock else f"{stock}.KS")
            
            # Fetch data using yfinance
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)  # 2 years of data
            
            all_data = []
            
            for symbol in symbols:
                try:
                    stock = yf.Ticker(symbol)
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if not hist.empty:
                        # Calculate technical indicators
                        hist = self._calculate_technical_indicators(hist)
                        
                        # Add stock metadata
                        info = stock.info
                        hist['Symbol'] = symbol
                        hist['Company_Name'] = info.get('longName', symbol)
                        hist['Sector'] = info.get('sector', 'Unknown')
                        hist['Industry'] = info.get('industry', 'Unknown')
                        hist['Market_Cap'] = info.get('marketCap', 0)
                        hist['PE_Ratio'] = info.get('trailingPE', None)
                        hist['PB_Ratio'] = info.get('priceToBook', None)
                        hist['Dividend_Yield'] = info.get('dividendYield', None)
                        hist['Beta'] = info.get('beta', None)
                        hist['52Week_High'] = info.get('fiftyTwoWeekHigh', None)
                        hist['52Week_Low'] = info.get('fiftyTwoWeekLow', None)
                        
                        all_data.append(hist)
                        
                    await asyncio.sleep(0.1)  # Rate limiting
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {symbol}: {str(e)}")
                    continue
            
            if all_data:
                combined_df = pd.concat(all_data)
                combined_df = self._clean_data(combined_df)
                logger.info(f"Successfully processed market data for {len(all_data)} stocks")
                return combined_df
            else:
                logger.warning("No market data could be fetched")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error in get_market_data: {str(e)}")
            raise

    async def get_alpha_vantage_data(self, stock_list: List[str]) -> Dict[str, Any]:
        """
        Alpha Vantage API를 통한 미국 주식 데이터 수집 (무료 티어: 5 calls/minute, 500 calls/day)
        """
        try:
            if not self.alpha_vantage_api_key or self.alpha_vantage_api_key == "your_alpha_vantage_api_key_here":
                logger.warning("Alpha Vantage API key not available, using mock data")
                return self._generate_mock_alpha_vantage_data(stock_list)
            
            alpha_data = {}
            base_url = "https://www.alphavantage.co/query"
            
            for symbol in stock_list:
                try:
                    # Get daily stock data
                    params = {
                        'function': 'TIME_SERIES_DAILY',
                        'symbol': symbol,
                        'apikey': self.alpha_vantage_api_key,
                        'outputsize': 'compact'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(base_url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if 'Time Series (Daily)' in data:
                                    alpha_data[symbol] = {
                                        'daily_data': data['Time Series (Daily)'],
                                        'metadata': data.get('Meta Data', {})
                                    }
                                else:
                                    logger.warning(f"No data returned for {symbol} from Alpha Vantage")
                    
                    await asyncio.sleep(12)  # Rate limiting: 5 calls per minute
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch Alpha Vantage data for {symbol}: {str(e)}")
                    continue
            
            logger.info(f"Fetched Alpha Vantage data for {len(alpha_data)} stocks")
            return alpha_data
            
        except Exception as e:
            logger.error(f"Error in get_alpha_vantage_data: {str(e)}")
            return {}

    async def get_finnhub_data(self, stock_list: List[str]) -> Dict[str, Any]:
        """
        Finnhub API를 통한 실시간 주식 데이터 수집 (무료 티어: 60 calls/minute)
        """
        try:
            if not self.finnhub_api_key or self.finnhub_api_key == "your_finnhub_api_key_here":
                logger.warning("Finnhub API key not available, using mock data")
                return self._generate_mock_finnhub_data(stock_list)
            
            finnhub_data = {}
            base_url = "https://finnhub.io/api/v1"
            
            for symbol in stock_list:
                try:
                    symbol_data = {}
                    
                    # Get real-time quote
                    quote_url = f"{base_url}/quote"
                    params = {'symbol': symbol, 'token': self.finnhub_api_key}
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(quote_url, params=params) as response:
                            if response.status == 200:
                                quote_data = await response.json()
                                symbol_data['quote'] = quote_data
                    
                    # Get company profile
                    profile_url = f"{base_url}/stock/profile2"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(profile_url, params=params) as response:
                            if response.status == 200:
                                profile_data = await response.json()
                                symbol_data['profile'] = profile_data
                    
                    finnhub_data[symbol] = symbol_data
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch Finnhub data for {symbol}: {str(e)}")
                    continue
            
            logger.info(f"Fetched Finnhub data for {len(finnhub_data)} stocks")
            return finnhub_data
            
        except Exception as e:
            logger.error(f"Error in get_finnhub_data: {str(e)}")
            return {}

    async def get_investing_data(self, stock_list: List[str]) -> Dict[str, Any]:
        """
        investing.com에서 추가 시장 데이터 수집
        """
        try:
            investing_data = {}
            
            for stock in stock_list:
                try:
                    # Construct investing.com URL for the stock
                    search_term = stock.replace('.KS', '')
                    url = f"https://www.investing.com/search/?q={search_term}"
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Extract relevant financial data
                                # This is a simplified implementation
                                data = {
                                    'analyst_rating': self._extract_analyst_rating(soup),
                                    'price_target': self._extract_price_target(soup),
                                    'news_sentiment': self._extract_news_sentiment(soup)
                                }
                                investing_data[stock] = data
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch investing.com data for {stock}: {str(e)}")
                    continue
            
            logger.info(f"Fetched investing.com data for {len(investing_data)} stocks")
            return investing_data
            
        except Exception as e:
            logger.error(f"Error in get_investing_data: {str(e)}")
            return {}

    def _calculate_technical_indicators(self, hist: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표 계산
        """
        try:
            # Returns and volatility
            hist['Daily_Return'] = hist['Close'].pct_change()
            hist['Log_Return'] = np.log(hist['Close'] / hist['Close'].shift(1))
            hist['Volatility_30D'] = hist['Daily_Return'].rolling(window=30).std()
            hist['Volatility_60D'] = hist['Daily_Return'].rolling(window=60).std()
            
            # Moving averages
            hist['MA_5'] = hist['Close'].rolling(window=5).mean()
            hist['MA_10'] = hist['Close'].rolling(window=10).mean()
            hist['MA_20'] = hist['Close'].rolling(window=20).mean()
            hist['MA_50'] = hist['Close'].rolling(window=50).mean()
            hist['MA_200'] = hist['Close'].rolling(window=200).mean()
            
            # Exponential moving averages
            hist['EMA_12'] = hist['Close'].ewm(span=12).mean()
            hist['EMA_26'] = hist['Close'].ewm(span=26).mean()
            
            # MACD
            hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
            hist['MACD_Signal'] = hist['MACD'].ewm(span=9).mean()
            hist['MACD_Histogram'] = hist['MACD'] - hist['MACD_Signal']
            
            # RSI
            hist['RSI'] = self._calculate_rsi(hist['Close'])
            
            # Bollinger Bands
            rolling_mean = hist['Close'].rolling(window=20).mean()
            rolling_std = hist['Close'].rolling(window=20).std()
            hist['BB_Upper'] = rolling_mean + (rolling_std * 2)
            hist['BB_Lower'] = rolling_mean - (rolling_std * 2)
            hist['BB_Width'] = hist['BB_Upper'] - hist['BB_Lower']
            hist['BB_Position'] = (hist['Close'] - hist['BB_Lower']) / hist['BB_Width']
            
            # Volume indicators
            hist['Volume_MA_20'] = hist['Volume'].rolling(window=20).mean()
            hist['Volume_Ratio'] = hist['Volume'] / hist['Volume_MA_20']
            
            # Price patterns
            hist['Price_Change_5D'] = (hist['Close'] - hist['Close'].shift(5)) / hist['Close'].shift(5)
            hist['Price_Change_20D'] = (hist['Close'] - hist['Close'].shift(20)) / hist['Close'].shift(20)
            hist['Price_Range'] = (hist['High'] - hist['Low']) / hist['Close']
            
            return hist
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return hist

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index) 계산
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _preprocess_for_ai(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        AI 학습에 적합한 형태로 데이터 전처리
        """
        try:
            if df.empty:
                return df
            
            # 1. 시간 동기화 (KST 기준)
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # KST timezone 적용
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Seoul')
            
            # 2. 결측치 처리
            # Forward fill, then backward fill
            df = df.fillna(method='forward').fillna(method='backward')
            
            # Interpolate remaining NaN values
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].interpolate(method='linear')
            
            # 3. 데이터 형식 일치화
            # Ensure consistent data types
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 4. 이상치 제거 (IQR method)
            for col in numeric_columns:
                if col in df.columns and df[col].dtype in ['int64', 'float64']:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
            
            # 5. Feature engineering for AI
            # Add date-based features
            df['Year'] = df.index.year
            df['Month'] = df.index.month
            df['DayOfWeek'] = df.index.dayofweek
            df['Quarter'] = df.index.quarter
            
            # Add lag features
            for col in ['Close', 'Volume', 'Daily_Return']:
                if col in df.columns:
                    df[f'{col}_Lag1'] = df[col].shift(1)
                    df[f'{col}_Lag5'] = df[col].shift(5)
                    df[f'{col}_Lag20'] = df[col].shift(20)
            
            # Add rolling statistics
            for col in ['Close', 'Volume']:
                if col in df.columns:
                    df[f'{col}_Rolling_Mean_5'] = df[col].rolling(window=5).mean()
                    df[f'{col}_Rolling_Std_5'] = df[col].rolling(window=5).std()
                    df[f'{col}_Rolling_Mean_20'] = df[col].rolling(window=20).mean()
                    df[f'{col}_Rolling_Std_20'] = df[col].rolling(window=20).std()
            
            # 6. Normalization for selected features
            features_to_normalize = ['Close', 'Volume', 'Market_Cap', 'Daily_Return', 'Volatility_30D']
            for feature in features_to_normalize:
                if feature in df.columns:
                    df[f'{feature}_Normalized'] = (df[feature] - df[feature].mean()) / df[feature].std()
            
            # 7. Final cleanup
            df = df.sort_index()
            df = df.dropna(subset=['Close', 'Volume'])  # Keep only rows with essential data
            
            logger.info(f"AI preprocessing completed. Final shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error in AI preprocessing: {str(e)}")
            return df

    def _merge_krx_data(self, market_data: pd.DataFrame, krx_data: Dict[str, Any]) -> pd.DataFrame:
        """
        KRX 데이터를 시장 데이터와 병합
        """
        try:
            if not krx_data or market_data.empty:
                return market_data
            
            for symbol, data in krx_data.items():
                if isinstance(data, dict) and 'OutBlock_1' in data:
                    krx_records = data['OutBlock_1']
                    
                    # Convert to DataFrame and merge
                    krx_df = pd.DataFrame(krx_records)
                    if not krx_df.empty and 'trdDd' in krx_df.columns:
                        krx_df['Date'] = pd.to_datetime(krx_df['trdDd'], format='%Y%m%d')
                        krx_df = krx_df.set_index('Date')
                        
                        # Add KRX-specific data to main dataframe
                        symbol_with_ks = f"{symbol}.KS"
                        mask = market_data['Symbol'] == symbol_with_ks
                        
                        if mask.any():
                            # Merge additional KRX metrics
                            for col in ['foreignBuyQty', 'foreignSellQty', 'institutionBuyQty', 'institutionSellQty']:
                                if col in krx_df.columns:
                                    market_data.loc[mask, f'KRX_{col}'] = krx_df[col].reindex(market_data.index[mask]).values
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error merging KRX data: {str(e)}")
            return market_data

    def _merge_investing_data(self, market_data: pd.DataFrame, investing_data: Dict[str, Any]) -> pd.DataFrame:
        """
        investing.com 데이터를 시장 데이터와 병합
        """
        try:
            if not investing_data or market_data.empty:
                return market_data
            
            for symbol, data in investing_data.items():
                mask = market_data['Symbol'] == symbol
                if mask.any():
                    market_data.loc[mask, 'Analyst_Rating'] = data.get('analyst_rating', None)
                    market_data.loc[mask, 'Price_Target'] = data.get('price_target', None)
                    market_data.loc[mask, 'News_Sentiment'] = data.get('news_sentiment', None)
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error merging investing data: {str(e)}")
            return market_data

    def _extract_analyst_rating(self, soup) -> Optional[str]:
        """investing.com에서 애널리스트 등급 추출"""
        try:
            # This is a placeholder implementation
            rating_element = soup.find('div', {'class': 'analyst-rating'})
            return rating_element.text.strip() if rating_element else None
        except:
            return None

    def _extract_price_target(self, soup) -> Optional[float]:
        """investing.com에서 목표 주가 추출"""
        try:
            # This is a placeholder implementation
            target_element = soup.find('span', {'class': 'price-target'})
            if target_element:
                price_text = target_element.text.strip().replace(',', '')
                return float(price_text) if price_text.replace('.', '').isdigit() else None
            return None
        except:
            return None

    def _extract_news_sentiment(self, soup) -> Optional[str]:
        """investing.com에서 뉴스 심리 추출"""
        try:
            # This is a placeholder implementation
            sentiment_element = soup.find('div', {'class': 'sentiment'})
            return sentiment_element.text.strip() if sentiment_element else None
        except:
            return None

    def _get_korean_name(self, symbol: str) -> str:
        """심볼을 한국어 이름으로 변환"""
        for korean, sym in self.korean_stocks.items():
            if sym == symbol:
                return korean
        return symbol.replace('.KS', '')

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 정제 및 기본 전처리"""
        try:
            if df.empty:
                return df
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Sort by date
            df = df.sort_index()
            
            # Remove duplicate index values
            df = df[~df.index.duplicated(keep='last')]
            
            logger.info(f"Data cleaned: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error in data cleaning: {str(e)}")
            return df

    async def get_single_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        단일 주식에 대한 상세 데이터 조회
        """
        try:
            # Convert Korean name if necessary
            if symbol in self.korean_stocks:
                ticker_symbol = self.korean_stocks[symbol]
            else:
                ticker_symbol = symbol if '.' in symbol else f"{symbol}.KS"
            
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            hist = stock.history(period="1mo")
            
            if hist.empty:
                return {"error": "No data available"}
            
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change = current_price - prev_price
            change_pct = (change / prev_price) * 100
            
            return {
                "symbol": ticker_symbol,
                "name": symbol,
                "current_price": float(current_price),
                "change": float(change),
                "change_percent": float(change_pct),
                "volume": int(hist['Volume'].iloc[-1]),
                "market_cap": info.get('marketCap', 0),
                "sector": info.get('sector', 'Unknown'),
                "pe_ratio": info.get('trailingPE', None),
                "pb_ratio": info.get('priceToBook', None),
                "dividend_yield": info.get('dividendYield', None),
                "52_week_high": info.get('fiftyTwoWeekHigh', None),
                "52_week_low": info.get('fiftyTwoWeekLow', None)
            }
            
        except Exception as e:
            logger.error(f"Error fetching single stock data for {symbol}: {str(e)}")
            return {"error": str(e)}

    async def get_web_data(self, url: str) -> Dict[str, Any]:
        """
        웹 URL에서 투자 관련 콘텐츠 추출
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title and text content
                        title = soup.find('title')
                        title_text = title.get_text() if title else ""
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.extract()
                        
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return {
                            "url": url,
                            "title": title_text,
                            "content": text[:10000],  # Increased content length
                            "extracted_at": datetime.now().isoformat(),
                            "word_count": len(text.split()),
                            "language": "ko" if any(ord(char) > 0x1100 and ord(char) < 0x11FF or 
                                                  ord(char) > 0x3130 and ord(char) < 0x318F or 
                                                  ord(char) > 0xAC00 and ord(char) < 0xD7AF for char in text) else "en"
                        }
                    else:
                        return {"error": f"HTTP {response.status}"}
                        
        except Exception as e:
            logger.error(f"Error extracting web data from {url}: {str(e)}")
            return {"error": str(e)}

    async def search_investment_content(self, keywords: List[str], source: str = "google") -> List[Dict[str, Any]]:
        """
        투자 관련 콘텐츠 검색 (Google Search API, 뉴스, 논문 등)
        
        Args:
            keywords: 검색 키워드 리스트
            source: 검색 소스 ("google", "news", "arxiv")
        """
        try:
            if source == "google" and self.google_search_api_key:
                return await self._search_google(keywords)
            elif source == "arxiv":
                return await self._search_arxiv(keywords)
            else:
                # Fallback to mock data
                return await self._mock_search_results(keywords)
                
        except Exception as e:
            logger.error(f"Error searching investment content: {str(e)}")
            return []

    async def _search_google(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Google Search API를 사용한 콘텐츠 검색"""
        try:
            results = []
            base_url = "https://www.googleapis.com/customsearch/v1"
            
            for keyword in keywords:
                params = {
                    'key': self.google_search_api_key,
                    'cx': os.getenv('GOOGLE_SEARCH_ENGINE_ID', 'your-search-engine-id'),
                    'q': f"{keyword} 투자 전략 분석",
                    'num': 5,
                    'lr': 'lang_ko'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for item in data.get('items', []):
                                results.append({
                                    'keyword': keyword,
                                    'title': item.get('title', ''),
                                    'snippet': item.get('snippet', ''),
                                    'url': item.get('link', ''),
                                    'source': 'google',
                                    'date': datetime.now().isoformat()
                                })
                
                await asyncio.sleep(0.1)  # Rate limiting
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Google search: {str(e)}")
            return []

    async def _search_arxiv(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """arXiv API를 사용한 논문 검색"""
        try:
            results = []
            base_url = "http://export.arxiv.org/api/query"
            
            for keyword in keywords:
                search_query = f"all:{keyword} AND cat:q-fin*"
                params = {
                    'search_query': search_query,
                    'start': 0,
                    'max_results': 5
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_url, params=params) as response:
                        if response.status == 200:
                            xml_content = await response.text()
                            # Simple XML parsing (you might want to use xml.etree.ElementTree for production)
                            
                            # This is a simplified implementation
                            results.append({
                                'keyword': keyword,
                                'title': f"Quantitative Finance Research on {keyword}",
                                'summary': f"Academic research on {keyword} in quantitative finance",
                                'url': f"https://arxiv.org/search/?query={quote_plus(keyword)}&searchtype=all",
                                'source': 'arxiv',
                                'date': datetime.now().isoformat()
                            })
                
                await asyncio.sleep(1)  # Rate limiting for arXiv
            
            return results
            
        except Exception as e:
            logger.error(f"Error in arXiv search: {str(e)}")
            return []

    async def _mock_search_results(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Mock 검색 결과 생성 (API 키가 없을 때 사용)"""
        results = []
        
        investment_topics = [
            "Portfolio Optimization", "Risk Management", "Asset Allocation", "Market Analysis",
            "Technical Analysis", "Value Investing", "Growth Investing", "Dividend Strategy"
        ]
        
        for keyword in keywords:
            for i, topic in enumerate(investment_topics[:3]):
                results.append({
                    'keyword': keyword,
                    'title': f"{keyword} and {topic} Strategy Analysis",
                    'summary': f"Expert analysis and investment outlook on {keyword} from a {topic} perspective",
                    'url': f"https://example-investment-site.com/{keyword}-{topic.replace(' ', '-').lower()}",
                    'source': 'mock',
                    'date': datetime.now().isoformat(),
                    'relevance_score': 0.9 - (i * 0.1)
                })
        
        return results

    def _generate_mock_alpha_vantage_data(self, stock_list: List[str]) -> Dict[str, Any]:
        """Alpha Vantage Mock 데이터 생성"""
        mock_data = {}
        base_date = datetime.now() - timedelta(days=30)
        
        for symbol in stock_list:
            # Generate mock daily data for the last 30 days
            daily_data = {}
            base_price = np.random.uniform(50, 500)  # Random base price
            
            for i in range(30):
                date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
                # Simulate price movement
                change = np.random.normal(0, 0.02)  # 2% daily volatility
                price = base_price * (1 + change)
                volume = np.random.randint(1000000, 10000000)
                
                daily_data[date] = {
                    "1. open": f"{price:.2f}",
                    "2. high": f"{price * 1.02:.2f}",
                    "3. low": f"{price * 0.98:.2f}",
                    "4. close": f"{price:.2f}",
                    "5. volume": str(volume)
                }
                base_price = price
            
            mock_data[symbol] = {
                'daily_data': daily_data,
                'metadata': {
                    'symbol': symbol,
                    'last_refreshed': datetime.now().strftime("%Y-%m-%d"),
                    'time_zone': 'US/Eastern'
                }
            }
        
        return mock_data

    def _generate_mock_finnhub_data(self, stock_list: List[str]) -> Dict[str, Any]:
        """Finnhub Mock 데이터 생성"""
        mock_data = {}
        
        company_profiles = {
            "AAPL": {"name": "Apple Inc.", "industry": "Technology Hardware", "sector": "Technology"},
            "MSFT": {"name": "Microsoft Corp", "industry": "Software", "sector": "Technology"},
            "GOOGL": {"name": "Alphabet Inc", "industry": "Internet & Direct Marketing", "sector": "Communication"},
            "AMZN": {"name": "Amazon.com Inc", "industry": "Internet Retail", "sector": "Consumer Discretionary"},
            "TSLA": {"name": "Tesla Inc", "industry": "Auto Manufacturers", "sector": "Consumer Discretionary"},
        }
        
        for symbol in stock_list:
            base_price = np.random.uniform(50, 500)
            mock_data[symbol] = {
                'quote': {
                    'c': round(base_price, 2),  # current price
                    'h': round(base_price * 1.05, 2),  # high price of the day
                    'l': round(base_price * 0.95, 2),  # low price of the day
                    'o': round(base_price * 0.98, 2),  # open price of the day
                    'pc': round(base_price * 0.97, 2),  # previous close price
                    't': int(datetime.now().timestamp())  # timestamp
                },
                'profile': company_profiles.get(symbol, {
                    "name": f"{symbol} Corporation",
                    "industry": "Various Industries",
                    "sector": "Diversified"
                })
            }
        
        return mock_data

    def get_sample_us_portfolio(self) -> List[str]:
        """샘플 미국 주식 포트폴리오 반환"""
        return [
            "AAPL",  # Technology - 20%
            "MSFT",  # Technology - 15%
            "GOOGL", # Technology - 15%
            "AMZN",  # Consumer Discretionary - 10%
            "JNJ",   # Healthcare - 10%
            "JPM",   # Financial - 10%
            "V",     # Financial - 5%
            "WMT",   # Consumer Staples - 5%
            "PG",    # Consumer Staples - 5%
            "XOM"    # Energy - 5%
        ]

    def get_diversified_us_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """섹터별 분산된 미국 주식 포트폴리오 반환"""
        return {
            "Technology": {
                "weight": 0.35,
                "stocks": {
                    "AAPL": 0.12,
                    "MSFT": 0.10,
                    "GOOGL": 0.08,
                    "NVDA": 0.05
                }
            },
            "Healthcare": {
                "weight": 0.20,
                "stocks": {
                    "JNJ": 0.08,
                    "UNH": 0.07,
                    "PFE": 0.05
                }
            },
            "Financial": {
                "weight": 0.15,
                "stocks": {
                    "JPM": 0.08,
                    "V": 0.04,
                    "MA": 0.03
                }
            },
            "Consumer": {
                "weight": 0.15,
                "stocks": {
                    "AMZN": 0.08,
                    "WMT": 0.04,
                    "PG": 0.03
                }
            },
            "Energy": {
                "weight": 0.10,
                "stocks": {
                    "XOM": 0.06,
                    "CVX": 0.04
                }
            },
            "Industrial": {
                "weight": 0.05,
                "stocks": {
                    "GE": 0.03,
                    "CAT": 0.02
                }
            }
        }
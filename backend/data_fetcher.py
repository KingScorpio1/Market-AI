# backend/data_fetcher.py

import ccxt
import yfinance as yf
import pandas as pd

# Initialize Binance (Public data doesn't need API keys)
exchange = ccxt.binance()

def get_current_price(symbol):
    """
    Ultra-fast price check. 
    Uses CCXT for Crypto, YFinance for Stocks.
    """
    try:
        if "-USD" in symbol: # Crypto
            # Convert BTC-USD -> BTC/USDT for Binance
            pair = symbol.replace("-USD", "/USDT")
            ticker = exchange.fetch_ticker(pair)
            return ticker['last']
        else: # Stocks (NVDA, TSLA)
            ticker = yf.Ticker(symbol)
            return ticker.fast_info['last_price']
    except:
        return None

def get_price_data(symbol="BTC-USD", period="60d", interval="1h"):
    """
    Fetches historical candles for analysis/training.
    """
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty: return df
        
        # Flatten MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.copy()
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()

def get_news_headlines(symbol="BTC-USD"):
    """Fetches latest news titles from Yahoo Finance with error handling"""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        headlines = []
        if news:
            for n in news:
                # Try different keys that Yahoo might use
                title = n.get('title') or n.get('headline')
                if title:
                    headlines.append(title)
        
        return headlines
    except Exception as e:
        # Don't print error to keep console clean, just return empty
        return []
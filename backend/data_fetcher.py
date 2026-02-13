#data_fetcher.py

import yfinance as yf
import pandas as pd

def get_price_data(symbol="BTC-USD", period="60d", interval="1h"):
    """
    Fetches market data. 
    For Scalping (1m), use period="5d", interval="1m".
    """
    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True
        )
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.copy()
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame() # Return empty if fails

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
        print(f"News fetch error for {symbol}: {e}")
        return []
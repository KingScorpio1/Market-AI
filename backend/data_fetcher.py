# backend/data_fetcher.py

import ccxt
import yfinance as yf
import pandas as pd
import feedparser
import time

# Initialize Binance (Public data doesn't need API keys)
exchange = ccxt.binance()

def get_current_price(symbol, retries=3):
    """
    Ultra-fast price check with built-in retry logic for socket errors.
    """
    for attempt in range(retries):
        try:
            if "-USD" in symbol: # Crypto
                pair = symbol.replace("-USD", "/USDT")
                ticker = exchange.fetch_ticker(pair)
                return ticker['last']
            else: # Stocks
                ticker = yf.Ticker(symbol) # Let yfinance handle the session natively
                return ticker.fast_info['last_price']
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep(1) # Wait 1 second and try again

def get_price_data(symbol="BTC-USD", period="60d", interval="1h", retries=3):
    """
    Fetches historical candles. Uses a manual retry loop to bypass Windows socket errors
    while complying with Yahoo's new curl_cffi security requirement.
    """
    for attempt in range(retries):
        try:
            # Anti-spam delay (prevents rate limiting)
            time.sleep(0.5) 
            
            df = yf.download(
                symbol, 
                period=period, 
                interval=interval, 
                progress=False
                # Notice: We removed the session= parameter entirely.
            )
            
            if df.empty: return df
            
            # Flatten MultiIndex if present (yfinance format quirk)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df.copy()
            df.dropna(inplace=True)
            return df
            
        except Exception as e:
            print(f"⚠️ Network hiccup for {symbol}, retrying ({attempt+1}/{retries})...")
            time.sleep(2) # Wait 2 seconds before retrying the download
            
    print(f"❌ Failed to fetch {symbol} after {retries} attempts.")
    return pd.DataFrame()

def get_news_headlines(symbol="BTC-USD"):
    """
    Fetches news via RSS Feeds (Unblockable).
    """
    try:
        if "-USD" in symbol:
            rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        else:
            ticker = symbol.replace("-USD", "")
            rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"

        feed = feedparser.parse(rss_url)
        headlines = []
        for entry in feed.entries[:5]:
            headlines.append(entry.title)
            
        return headlines
    except Exception as e:
        return []
#ai_engine.py

from sklearn.ensemble import IsolationForest
import numpy as np
import ta

def anomaly_detector(df):
    # Detect Volume Spikes (Whale Activity Proxy)
    df['vol_avg'] = df['Volume'].rolling(window=20).mean()
    df['whale_alert'] = np.where(df['Volume'] > 3 * df['vol_avg'], 1, 0)
    
    # Calculate ADX for Strategy Selection
    df['adx'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx()

    # AI Anomaly Detection
    features = df[["Volume", "atr"]].dropna()
    if len(features) > 0:
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(features)
        df.loc[features.index, "anomaly"] = model.predict(features)
    else:
        df["anomaly"] = 1 # Normal
        
    return df

def calculate_crash_risk(row):
    risk_score = 0
    
    # 1. RSI Overbought
    rsi = row['rsi']
    if rsi > 70: risk_score += 40
    elif rsi > 60: risk_score += 20
    
    # 2. Volatility Spike
    if row['atr'] > row['atr_avg']: 
        risk_score += 20

    # 3. AI Anomaly
    if row.get('anomaly', 1) == -1:
        risk_score += 30

    # 4. Whale Dump Risk
    if row['whale_alert'] == 1:
        risk_score += 10

    return min(risk_score, 100)

def trading_signal(df, sentiment_score=0.0):
    if len(df) < 50: return "HOLD"
    
    last = df.iloc[-1]
    df['atr_avg'] = df['atr'].rolling(window=20).mean()
    crash_risk = calculate_crash_risk(df.iloc[-1])

    rsi = float(last["rsi"])
    ema50 = float(last["ema50"])
    ema200 = float(last["ema200"])
    macd = float(last["macd"])
    
    # Trend Filter
    is_bullish = last["Close"] > ema200
    
    # SELL LOGIC
    if crash_risk > 80:
        return f"CRITICAL SELL (Risk: {crash_risk}%)"
    
    if sentiment_score < -0.6:
        return "PANIC SELL (News Event)"

    if (rsi > 75 or ema50 < ema200) and crash_risk > 50:
        return f"SELL (Trend Reversal)"

    # BUY LOGIC
    buy_signal = (
        is_bullish and       
        rsi < 40 and         
        macd > 0 and         
        crash_risk < 30 and   
        sentiment_score > 0  
    )

    if buy_signal:
        return "BUY"
    
    return "HOLD"

def get_strategy(row):
    if row['adx'] > 25:
        return "TREND_FOLLOWING" # Trust EMA crosses, ignore overbought RSI
    else:
        return "MEAN_REVERSION" # Buy support, Sell resistance, Trust RSI
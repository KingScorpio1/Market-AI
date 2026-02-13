#ai_engine.py

from sklearn.ensemble import IsolationForest
import numpy as np

def anomaly_detector(df):
    # Detect Volume Spikes (Whale Activity Proxy)
    # If Volume > 3x the 20-period average, it's a whale
    df['vol_avg'] = df['Volume'].rolling(window=20).mean()
    df['whale_alert'] = np.where(df['Volume'] > 3 * df['vol_avg'], 1, 0)

    # AI Anomaly Detection
    features = df[["Volume", "atr"]].dropna()
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(features)
    df.loc[features.index, "anomaly"] = model.predict(features)
    return df

def calculate_crash_risk(row):
    """
    Outputs a 0-100% score indicating probability of a price drop.
    """
    risk_score = 0
    
    # 1. RSI Overbought (Price is too high)
    rsi = row['rsi']
    if rsi > 70: risk_score += 40
    elif rsi > 60: risk_score += 20
    
    # 2. Volatility Spike (Panic/Uncertainty)
    # If current ATR is higher than average, market is unstable
    if row['atr'] > row['atr_avg']: 
        risk_score += 20

    # 3. AI Anomaly (Unusual behavior)
    if row['anomaly'] == -1:
        risk_score += 30

    # 4. Whale Dump Risk (High Volume + Drop)
    # (Simplified logic: if whale alert is ON, add risk)
    if row['whale_alert'] == 1:
        risk_score += 10

    return min(risk_score, 100) # Cap at 100%

def trading_signal(df, sentiment_score=0.0):
    last = df.iloc[-1]
    
    # Calculate Risk
    # We need a rolling average for ATR to compare against
    df['atr_avg'] = df['atr'].rolling(window=20).mean()
    crash_risk = calculate_crash_risk(df.iloc[-1])

    rsi = float(last["rsi"])
    ema50 = float(last["ema50"])
    ema200 = float(last["ema200"])
    macd = float(last["macd"])
    anomaly = int(last["anomaly"])

    # --- ADVANCED LOGIC ---
    
    # SELL LOGIC
    if crash_risk > 80:
        return f"CRITICAL SELL (Risk: {crash_risk}%)"
    
    if sentiment_score < -0.5:
        return "PANIC SELL (Bad News)"

    if (rsi > 70 or ema50 < ema200) and crash_risk > 50:
        return f"SELL (Risk: {crash_risk}%)"

    # BUY LOGIC
    # Only buy if risk is low (< 40%) and Technicals are good
    buy_signal = (
        rsi < 45 and
        ema50 > ema200 and
        macd > 0 and
        crash_risk < 40 and
        sentiment_score > -0.1
    )

    if buy_signal:
        return "BUY"
    
    return "HOLD"
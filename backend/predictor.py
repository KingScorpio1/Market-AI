# backend/predictor.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from backend.indicators import add_indicators

def predict_next_price(df):
    """
    Trains a model on the fly using the last 60 days of data 
    to predict the NEXT closing price.
    """
    # 1. Prepare Data
    df = add_indicators(df)
    df = df.dropna()
    
    # Feature Engineering (The inputs for the AI)
    # We use technical indicators as features
    feature_cols = ['rsi', 'ema50', 'ema200', 'macd', 'atr', 'Volume']
    
    data = df[feature_cols].copy()
    
    # TARGET: We want to predict the 'Close' price of the NEXT candle
    # We shift the Close column UP by 1 to create labels
    data['target'] = df['Close'].shift(-1)
    data = data.dropna()
    
    if len(data) < 50:
        return None # Not enough data to train
    
    # 2. Train/Test Split
    X = data[feature_cols]
    y = data['target']
    
    # Use last 20% for validation, first 80% for training
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    # 3. Train Model (Random Forest is robust and less prone to overfitting than LinearReg)
    model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train, y_train)
    
    # 4. Predict Future
    # Get the very latest data row to predict the unknown next candle
    latest_features = df[feature_cols].iloc[[-1]] 
    prediction = model.predict(latest_features)[0]
    
    return prediction
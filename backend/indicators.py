#indicators.py

import ta
import pandas as pd
import numpy as np

def to_1d(series):
    """Force any pandas object into a clean 1D Series"""
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return pd.Series(np.asarray(series).flatten(), index=series.index)

def add_indicators(df: pd.DataFrame):
    close = to_1d(df["Close"])
    high  = to_1d(df["High"])
    low   = to_1d(df["Low"])

    df["rsi"] = ta.momentum.RSIIndicator(close=close).rsi()
    df["ema50"] = ta.trend.EMAIndicator(close=close, window=50).ema_indicator()
    df["ema200"] = ta.trend.EMAIndicator(close=close, window=200).ema_indicator()
    df["macd"] = ta.trend.MACD(close=close).macd_diff()
    df["atr"] = ta.volatility.AverageTrueRange(
        high=high, low=low, close=close
    ).average_true_range()

    return df

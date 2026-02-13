#main.py

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from data_fetcher import get_price_data
from indicators import add_indicators
from ai_engine import anomaly_detector, trading_signal
from alerts import generate_alert

df = get_price_data("BTC-USD")
df = add_indicators(df)
df = anomaly_detector(df)

signal = trading_signal(df)
alert = generate_alert(signal, df["Close"].iloc[-1])

print("Signal:", signal)
if alert:
    print(alert)

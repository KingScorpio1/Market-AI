#bot_runner.py

import time
import sys
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from backend.data_fetcher import get_price_data, get_current_price, get_news_headlines
from backend.indicators import add_indicators
from backend.ai_engine import trading_signal, anomaly_detector
from backend.sentiment import analyze_sentiment
from backend.portfolio_manager import execute_trade, get_portfolio_status, update_high_water_mark
from backend.predictor import predict_next_price # <--- NEW
from bot.telegram_bot import send_telegram_message

# --- CONFIGURATION ---
WATCHLIST = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD", "NVDA", "TSLA", "AAPL", "AMZN"]
EMAIL_SENDER = "sulesmith38@gmail.com"
EMAIL_PASSWORD = "xkns egss ipjs snhb" # Google App Password
EMAIL_RECEIVER = "smithsule63@gmail.com"
# ---------------------

def send_email_alert(subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("📧 Email Sent!")
    except Exception as e:
        print(f"Email failed: {e}")

def run_scanner():
    print("🤖 Institutional AI System Online (Level 4)...")
    send_telegram_message("🤖 System Online: ML Predictor + Trailing Stops Active.")

    while True:
        for symbol in WATCHLIST:
            try:
                print(f"🔍 {symbol}...", end=" ")
                
                # 1. FAST PRICE CHECK (Real-Time)
                current_price = get_current_price(symbol)
                if current_price is None:
                    print("Skipping (Price Error)")
                    continue

                # 2. TRAILING STOP LOSS LOGIC
                update_high_water_mark(symbol, current_price, trader="bot")
                
                portfolio = get_portfolio_status("bot")
                if symbol in portfolio["positions"]:
                    pos = portfolio["positions"][symbol]
                    highest = pos.get('highest_price') or pos['entry_price']
                    
                    stop_price = highest * 0.97 # 3% Trailing Stop
                    
                    if current_price < stop_price:
                        print(f"📉 Trailing Stop Hit!")
                        trade_msg = execute_trade(symbol, "SELL", current_price, trader="bot")
                        send_telegram_message(f"📉 **TRAILING STOP HIT: {symbol}**\nDropped from peak ${highest:.2f}\n{trade_msg}")
                        continue 

                # 3. AI ANALYSIS & PREDICTION
                df = get_price_data(symbol)
                if df.empty: continue
                
                df = add_indicators(df)
                df = anomaly_detector(df)
                
                # ML PREDICTION
                predicted_price = predict_next_price(df)
                predicted_move = 0.0
                if predicted_price:
                    predicted_move = ((predicted_price - current_price) / current_price) * 100
                
                # News Sentiment
                headlines = get_news_headlines(symbol)
                sentiment = analyze_sentiment(headlines)

                # Standard Signals
                signal = trading_signal(df, sentiment)
                
                # 4. DECISION ENGINE (Combining Rules + ML)
                ml_confirmation = predicted_move > 0.5 
                
                if "BUY" in signal and ml_confirmation:
                    print(f"🚀 STRONG BUY (ML Predicts +{predicted_move:.2f}%)")
                    trade_msg = execute_trade(symbol, "BUY", current_price, trader="bot")
                    
                    msg = (f"🚀 **AI SNIPER ENTRY: {symbol}**\n"
                           f"Price: ${current_price:.2f}\n"
                           f"ML Forecast: ${predicted_price:.2f} (+{predicted_move:.2f}%)\n"
                           f"News Score: {sentiment:.2f}\n"
                           f"{trade_msg}")
                    
                    send_telegram_message(msg)
                    send_email_alert(f"URGENT BUY: {symbol}", msg) # <--- RESTORED EMAIL
                
                elif "SELL" in signal:
                     print(f"SELL SIGNAL")
                     trade_msg = execute_trade(symbol, "SELL", current_price, trader="bot")
                     if "✅" in trade_msg:
                         msg = f"⚠️ **EXIT SIGNAL: {symbol}**\n{trade_msg}"
                         send_telegram_message(msg)
                         if "CRITICAL" in signal:
                             send_email_alert(f"URGENT SELL: {symbol}", msg) # <--- RESTORED EMAIL
                else:
                    print(f"HOLD (ML Forecast: {predicted_move:+.2f}%)")

            except Exception as e:
                print(f"Error {symbol}: {e}")
        
        print("\n⏳ Cooling down for 5 minutes...")
        time.sleep(300)

if __name__ == "__main__":
    run_scanner()
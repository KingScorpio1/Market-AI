#bot_runner.py

import time
import sys
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from backend.data_fetcher import get_price_data, get_news_headlines
from backend.indicators import add_indicators
from backend.ai_engine import trading_signal, anomaly_detector
from backend.sentiment import analyze_sentiment
from backend.portfolio_manager import execute_trade
from bot.telegram_bot import send_telegram_message

# --- CONFIGURATION ---
WATCHLIST = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD", "NVDA", "TSLA", "AAPL", "AMZN"]
EMAIL_SENDER = "sulesmith38@gmail.com"
EMAIL_PASSWORD = "moneymakesmoney369!" # Google App Password
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
    print("🤖 Institutional AI Scanner Started...")
    send_telegram_message("🤖 System Online: Tracking Whales & Crash Risk.")

    while True:
        for symbol in WATCHLIST:
            try:
                print(f"🔍 Scanning {symbol}...", end=" ")
                
                df = get_price_data(symbol)
                if df.empty:
                    print("❌ No Data")
                    continue

                df = add_indicators(df)
                df = anomaly_detector(df) # Calculates Whale/Anomaly
                
                headlines = get_news_headlines(symbol)
                sentiment = analyze_sentiment(headlines)
                
                # Get Signal (Now includes Crash Risk text)
                signal = trading_signal(df, sentiment)
                current_price = df['Close'].iloc[-1]
                crash_risk = 0 # Default
                
                # Extract risk % from signal string if present
                if "Risk:" in signal:
                    import re
                    match = re.search(r"Risk: (\d+)%", signal)
                    if match: crash_risk = int(match.group(1))

                # --- ALERT LOGIC ---
                is_whale = df['whale_alert'].iloc[-1] == 1
                
                trade_msg = ""
                if "BUY" in signal:
                    trade_msg = execute_trade(symbol, "BUY", current_price)
                elif "SELL" in signal or "PANIC" in signal:
                    trade_msg = execute_trade(symbol, "SELL", current_price)
                # -------------------------

                if "BUY" in signal or "SELL" in signal or is_whale:
                    print(f"\n🚨 ALERT: {signal} @ ${current_price:.2f}")
                    
                    emoji = "🟢" if "BUY" in signal else "🔴"
                    if "CRITICAL" in signal: emoji = "💀"
                    
                    msg = (
                        f"{emoji} **{symbol} UPDATE**\n"
                        f"Signal: {signal}\n"
                        f"Price: ${current_price:.2f}\n"
                        f"News Score: {sentiment:.2f}\n"
                        f"🤖 Auto-Trade: {trade_msg}" 
                    )
                    
                    send_telegram_message(msg)
                    
                    # 2. Email (Only for CRITICAL or BUY)
                    if "CRITICAL" in signal or "BUY" in signal:
                        send_email_alert(f"URGENT: {symbol} Signal", msg)
                
                else:
                    print(f"✅ HOLD (Risk: {crash_risk}%)")
                
            except Exception as e:
                print(f"\n❌ Error {symbol}: {e}")
        
        print("Waiting 60 minutes...")
        time.sleep(3600)

if __name__ == "__main__":
    run_scanner()
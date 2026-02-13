# stock_scalper.py
import time
import sys
import pytz
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from backend.data_fetcher import get_price_data
from backend.indicators import add_indicators
from backend.ai_engine import trading_signal, anomaly_detector, calculate_crash_risk
from backend.portfolio_manager import execute_trade
from bot.telegram_bot import send_telegram_message

# --- CONFIGURATION ---
# High Volatility Stocks work best for minute trading
SCALP_WATCHLIST = ["NVDA", "TSLA", "AMD", "AAPL", "COIN", "MARA"] 

def is_market_open():
    """Checks if US Market is open (Mon-Fri, 9:30-16:00 EST)"""
    nyc = pytz.timezone('America/New_York')
    now = datetime.now(nyc)
    
    # 1. Check Weekend (5=Sat, 6=Sun)
    if now.weekday() >= 5:
        return False
    
    # 2. Check Hours (09:30 to 16:00)
    market_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_end = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_start <= now <= market_end

def run_scalper():
    print("🚀 FLASH TRADER (Minute Bot) Started...")
    send_telegram_message("🚀 Scalping Bot Online: Hunting for Minute-moves.")

    while True:
        if not is_market_open():
            print("💤 Market Closed. Sleeping for 5 minutes...", end="\r")
            time.sleep(300) # Check every 5 mins if market opened
            continue

        print(f"\n⚡ SCANNING ({datetime.now().strftime('%H:%M:%S')})...")
        
        for symbol in SCALP_WATCHLIST:
            try:
                # 1. Fetch 1-MINUTE Data (Fast!)
                # We only need last 5 days for 1m interval
                df = get_price_data(symbol, period="5d", interval="1m")
                
                if df.empty or len(df) < 50: 
                    continue

                # 2. Add Indicators
                df = add_indicators(df)
                df = anomaly_detector(df)
                
                # 3. Aggressive Logic (Modify thresholds dynamically for speed)
                # We pass a dummy '0' sentiment because News doesn't update every minute
                signal = trading_signal(df, sentiment_score=0.0)
                current_price = df['Close'].iloc[-1]
                
                # 4. Filter: Only take "BUY" signals if momentum is REALLY strong
                # (You can tweak this logic)
                
                if "BUY" in signal or "SELL" in signal:
                    # Execute Trade Immediately
                    trade_status = execute_trade(symbol, "BUY" if "BUY" in signal else "SELL", current_price)
                    
                    if "✅" in trade_status: # Only alert if trade actually happened
                        print(f"⚡ EXECUTION: {symbol} -> {trade_status}")
                        send_telegram_message(f"⚡ **SCALP ALERT: {symbol}**\n{trade_status}", "scalper")
            
            except Exception as e:
                print(f"Error {symbol}: {e}")
        
        # Wait 60 seconds exactly
        time.sleep(60)

if __name__ == "__main__":
    run_scalper()
# backend/portfolio_manager.py

import os
import time
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)

def safe_execute(query, retries=3):
    """
    Wrapper to retry database operations if Windows socket errors 
    or Cloudflare 502 Bad Gateway errors occur.
    """
    for attempt in range(retries):
        try:
            return query.execute()
        except Exception as e:
            if attempt == retries - 1:
                print(f"Database error after {retries} attempts: {e}")
                raise e
            time.sleep(1) # Wait 1 second and try again

def get_portfolio_status(trader="bot"):
    """
    Trader can be 'bot' (id=1) or 'human' (id=2)
    """
    trader_id = 1 if trader == "bot" else 2
    
    try:
        # Fetch Balance with Retry Logic
        balance_data = safe_execute(supabase.table("portfolio").select("balance").eq("id", trader_id))
        balance = balance_data.data[0]["balance"] if balance_data.data else 0
        
        # Fetch Open Positions with Retry Logic
        pos_data = safe_execute(supabase.table("positions").select("*").eq("trader", trader))
        positions = {p["symbol"]: p for p in pos_data.data}
        
        # Fetch History with Retry Logic
        hist_data = safe_execute(supabase.table("trade_history").select("*").eq("trader", trader).order("time", desc=True).limit(20))
        
        return {
            "balance": balance,
            "positions": positions,
            "history": hist_data.data
        }
    except Exception:
        # If the internet completely drops, return empty instead of crashing the dashboard
        return {"balance": 0, "positions": {}, "history":[]}

def execute_trade(symbol, action, price, trader="bot", amount=None):
    trader_id = 1 if trader == "bot" else 2
    
    status = get_portfolio_status(trader)
    balance = status["balance"]
    positions = status["positions"]
    
    try:
        if action == "BUY":
            if symbol in positions:
                return f"❌ {trader.capitalize()} already holds {symbol}"
            
            # DETERMINE TRADE SIZE
            if amount:
                trade_amount = float(amount)
            else:
                trade_amount = balance * 0.20
                
            if trade_amount > balance:
                return f"❌ Insufficient funds (Cash: ${balance:.2f})"
            if trade_amount < 10: 
                return "❌ Trade size too small (Min $10)"
            
            shares = trade_amount / price
            new_balance = balance - trade_amount
            
            # Update DB safely
            safe_execute(supabase.table("portfolio").update({"balance": new_balance}).eq("id", trader_id))
            safe_execute(supabase.table("positions").insert({
                "symbol": symbol, "entry_price": price, "shares": shares, "trader": trader, "highest_price": price
            }))
            safe_execute(supabase.table("trade_history").insert({
                "symbol": symbol, "action": "BUY", "price": price, 
                "shares": shares, "value": trade_amount, "trader": trader
            }))
            
            return f"✅ {trader.upper()} BOUGHT {shares:.4f} {symbol} @ ${price:.2f}"

        elif action == "SELL":
            if symbol not in positions:
                return f"❌ {trader.capitalize()} doesn't own {symbol}"
            
            pos = positions[symbol]
            shares = pos["shares"]
            sale_value = shares * price
            profit = sale_value - (shares * pos["entry_price"])
            new_balance = balance + sale_value
            
            # Update DB safely
            safe_execute(supabase.table("portfolio").update({"balance": new_balance}).eq("id", trader_id))
            safe_execute(supabase.table("positions").delete().eq("symbol", symbol).eq("trader", trader))
            safe_execute(supabase.table("trade_history").insert({
                "symbol": symbol, "action": "SELL", "price": price, 
                "shares": shares, "value": sale_value, "profit": profit, "trader": trader
            }))
            
            return f"✅ {trader.upper()} SOLD {symbol} (Profit: ${profit:+.2f})"

    except Exception as e:
        return f"❌ DB Transaction Failed: {e}"

    return "❌ Invalid Action"

def update_high_water_mark(symbol, current_price, trader="bot"):
    """
    Updates the highest price seen for a position.
    Used for Trailing Stop Loss.
    """
    try:
        trader_id = 1 if trader == "bot" else 2
        
        # Safely get current highest_price from DB
        res = safe_execute(supabase.table("positions").select("highest_price").eq("symbol", symbol).eq("trader", trader))
        if not res or not res.data: return
        
        stored_high = res.data[0]['highest_price']
        
        # If it's None (old position) or current is higher, update it safely
        if stored_high is None or current_price > stored_high:
            safe_execute(supabase.table("positions").update({"highest_price": current_price}).eq("symbol", symbol).eq("trader", trader))
            print(f"📈 New High for {symbol}: ${current_price:.2f} (Trailing Stop adjusting...)")
            
    except Exception as e:
        pass # Silently pass to keep the bot moving forward
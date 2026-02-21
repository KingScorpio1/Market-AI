import os
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)

def get_portfolio_status(trader="bot"):
    """
    Trader can be 'bot' (id=1) or 'human' (id=2)
    """
    trader_id = 1 if trader == "bot" else 2
    
    # Fetch Balance
    balance_data = supabase.table("portfolio").select("balance").eq("id", trader_id).execute()
    balance = balance_data.data[0]["balance"] if balance_data.data else 0
    
    # Fetch Open Positions for this specific trader
    pos_data = supabase.table("positions").select("*").eq("trader", trader).execute()
    positions = {p["symbol"]: p for p in pos_data.data}
    
    # Fetch History for this specific trader
    hist_data = supabase.table("trade_history").select("*").eq("trader", trader).order("time", desc=True).limit(20).execute()
    
    return {
        "balance": balance,
        "positions": positions,
        "history": hist_data.data
    }

def execute_trade(symbol, action, price, trader="bot", amount=None):
    """
    amount: (Optional) Specific dollar amount to trade. 
            If None, defaults to 20% of balance.
    """
    trader_id = 1 if trader == "bot" else 2
    
    status = get_portfolio_status(trader)
    balance = status["balance"]
    positions = status["positions"]
    
    if action == "BUY":
        if symbol in positions:
            # If we already own it, maybe we want to add more? 
            # For simplicity, let's block duplicate entries for now.
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
        
        # Update DB
        supabase.table("portfolio").update({"balance": new_balance}).eq("id", trader_id).execute()
        supabase.table("positions").insert({
            "symbol": symbol, "entry_price": price, "shares": shares, "trader": trader, "highest_price": price
        }).execute()
        
        supabase.table("trade_history").insert({
            "symbol": symbol, "action": "BUY", "price": price, 
            "shares": shares, "value": trade_amount, "trader": trader
        }).execute()
        
        return f"✅ {trader.upper()} BOUGHT {shares:.4f} {symbol} @ ${price:.2f}"

    # ... (Keep SELL logic exactly the same) ...
    elif action == "SELL":
        # ... (Your existing SELL code) ...
        # (Paste the previous SELL block here)
        if symbol not in positions:
            return f"❌ {trader.capitalize()} doesn't own {symbol}"
        
        pos = positions[symbol]
        shares = pos["shares"]
        sale_value = shares * price
        profit = sale_value - (shares * pos["entry_price"])
        new_balance = balance + sale_value
        
        supabase.table("portfolio").update({"balance": new_balance}).eq("id", trader_id).execute()
        supabase.table("positions").delete().eq("symbol", symbol).eq("trader", trader).execute()
        
        supabase.table("trade_history").insert({
            "symbol": symbol, "action": "SELL", "price": price, 
            "shares": shares, "value": sale_value, "profit": profit, "trader": trader
        }).execute()
        
        return f"✅ {trader.upper()} SOLD {symbol} (Profit: ${profit:+.2f})"

    return "❌ Invalid Action"

def update_high_water_mark(symbol, current_price, trader="bot"):
    """
    Updates the highest price seen for a position.
    Used for Trailing Stop Loss.
    """
    try:
        trader_id = 1 if trader == "bot" else 2
        
        # 1. Get current highest_price from DB
        res = supabase.table("positions").select("highest_price").eq("symbol", symbol).eq("trader", trader).execute()
        if not res.data: return
        
        stored_high = res.data[0]['highest_price']
        
        # If it's None (old position) or current is higher, update it
        if stored_high is None or current_price > stored_high:
            supabase.table("positions").update({
                "highest_price": current_price
            }).eq("symbol", symbol).eq("trader", trader).execute()
            print(f"📈 New High for {symbol}: ${current_price:.2f} (Trailing Stop adjusting...)")
            
    except Exception as e:
        print(f"Error updating high water mark: {e}")
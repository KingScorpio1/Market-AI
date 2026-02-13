import os
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Render/Local Env Variables
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)

def get_portfolio_status():
    # Fetch Balance
    balance_data = supabase.table("portfolio").select("balance").eq("id", 1).execute()
    balance = balance_data.data[0]["balance"]
    
    # Fetch Open Positions
    pos_data = supabase.table("positions").select("*").execute()
    positions = {p["symbol"]: p for p in pos_data.data}
    
    # Fetch History
    hist_data = supabase.table("trade_history").select("*").order("time", desc=True).limit(20).execute()
    
    return {
        "balance": balance,
        "positions": positions,
        "history": hist_data.data
    }

def execute_trade(symbol, action, price):
    status = get_portfolio_status()
    balance = status["balance"]
    positions = status["positions"]
    
    if action == "BUY":
        if symbol in positions:
            return f"❌ Already hold {symbol}"
        
        trade_amount = balance * 0.20
        if trade_amount < 10: return "❌ Insufficient funds"
        
        shares = trade_amount / price
        new_balance = balance - trade_amount
        
        # Update Database
        supabase.table("portfolio").update({"balance": new_balance}).eq("id", 1).execute()
        supabase.table("positions").insert({
            "symbol": symbol, "entry_price": price, "shares": shares
        }).execute()
        
        supabase.table("trade_history").insert({
            "symbol": symbol, "action": "BUY", "price": price, "shares": shares, "value": trade_amount
        }).execute()
        
        return f"✅ BOUGHT {shares:.4f} {symbol} @ ${price:.2f}"

    elif action == "SELL":
        if symbol not in positions:
            return f"❌ Don't own {symbol}"
        
        pos = positions[symbol]
        shares = pos["shares"]
        sale_value = shares * price
        profit = sale_value - (shares * pos["entry_price"])
        new_balance = balance + sale_value
        
        # Update Database
        supabase.table("portfolio").update({"balance": new_balance}).eq("id", 1).execute()
        supabase.table("positions").delete().eq("symbol", symbol).execute()
        
        supabase.table("trade_history").insert({
            "symbol": symbol, "action": "SELL", "price": price, 
            "shares": shares, "value": sale_value, "profit": profit
        }).execute()
        
        return f"✅ SOLD {symbol} for ${profit:+.2f} Profit"

    return "❌ Invalid Action"
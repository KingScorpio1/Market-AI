import pandas as pd
import json
import os
from datetime import datetime

PORTFOLIO_FILE = "/opt/render/project/src/portfolio_data.json" if os.environ.get('RENDER') else "portfolio_data.json"

def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        # Initial State: $10,000 Cash, No Assets, No History
        return {"balance": 10000.0, "positions": {}, "history": []}
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except:
        return {"balance": 10000.0, "positions": {}, "history": []}

def save_portfolio(data):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=4)

def execute_trade(symbol, action, price):
    """
    Simulates a trade.
    Action: 'BUY' or 'SELL'
    """
    data = load_portfolio()
    balance = data["balance"]
    positions = data["positions"]
    
    # TIMESTAMP
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action == "BUY":
        # ADDING RISK PARAMS
        stop_loss = price * 0.95  # 5% SL
        take_profit = price * 1.10 # 10% TP

        # Check if we already own it (Simple mode: 1 position per asset)
        if symbol in positions:
            return f"❌ Already hold {symbol}"
        
        # Position Sizing: Use 20% of available cash per trade
        trade_amount = balance * 0.20
        if trade_amount < 10: return "❌ Insufficient funds"
        
        shares = trade_amount / price
        data["balance"] -= trade_amount
        data["positions"][symbol] = {
            "entry_price": price, 
            "shares": shares, 
            "sl": stop_loss, 
            "tp": take_profit,
            "time": timestamp
        }
        
        # Record Log
        data["history"].append({
            "time": timestamp, "symbol": symbol, "action": "BUY", 
            "price": price, "shares": shares, "value": trade_amount
        })
        save_portfolio(data)
        return f"✅ BOUGHT {shares:.4f} {symbol} @ ${price:.2f}"

    elif action == "SELL":
        if symbol not in positions:
            return f"❌ Don't own {symbol}"
        
        pos = positions[symbol]
        shares = pos["shares"]
        sale_value = shares * price
        profit = sale_value - (shares * pos["entry_price"])
        
        data["balance"] += sale_value
        del data["positions"][symbol] # Remove position
        
        data["history"].append({
            "time": timestamp, "symbol": symbol, "action": "SELL", 
            "price": price, "shares": shares, "value": sale_value, "profit": profit
        })
        save_portfolio(data)
        return f"✅ SOLD {symbol} for ${profit:+.2f} Profit"
    
    return "❌ Invalid Action"

def get_portfolio_status():
    """Returns formatted data for Dashboard"""
    data = load_portfolio()
    return data

# Check for SL/TP on every tick (to be called by bot_runner)
    def check_exit_conditions(symbol, current_price):
        data = load_portfolio()
        if symbol in data["positions"]:
            pos = data["positions"][symbol]
            if current_price <= pos["sl"]: return "SELL (Stop Loss)"
            if current_price >= pos["tp"]: return "SELL (Take Profit)"
        return None
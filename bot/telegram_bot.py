#telegram_bot.py

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import requests

# ---------------- CONFIGURATION ----------------
# Bot 1: The Hourly Scanner (Crypto/Stocks)
MAIN_BOT_TOKEN = "8465822700:AAGNua-bEY-1_9b_ZBa2NMv-pmFugri7C2Y"

# Bot 2: The Minute Scalper (Stocks Only)
SCALPER_BOT_TOKEN = "8322178938:AAFD1dgTJ6jDVublhaS-Cu_KX65ejKbUJcs"

CHAT_ID = "5368652220"
# -----------------------------------------------

def send_telegram_message(message, bot_type="main"):
    """
    Sends a message using the specified bot.
    bot_type: 'main' (default) or 'scalper'
    """
    # Select the correct token
    if bot_type == "scalper":
        token = SCALPER_BOT_TOKEN
    else:
        token = MAIN_BOT_TOKEN
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown" # Allows bold/emoji formatting
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Failed to send {bot_type} alert: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

if __name__ == "__main__":
    # Test both bots
    send_telegram_message("✅ Main Bot Connected!", "main")
    send_telegram_message("🚀 Scalper Bot Connected!", "scalper")
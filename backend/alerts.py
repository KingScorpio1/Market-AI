#alerts

def generate_alert(signal, price):
    if signal == "BUY":
        return f"📈 BUY SIGNAL\nPrice: ${price:.2f}"
    elif signal == "SELL":
        return f"⚠️ SELL WARNING\nPrice: ${price:.2f}"
    return None

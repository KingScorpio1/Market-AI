#app.py

import sys
import time
from pathlib import Path

# Add project root to system path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
from bot.bot_runner import run_scanner

# Import backend modules
from backend.data_fetcher import get_price_data, get_news_headlines
from backend.indicators import add_indicators
from backend.ai_engine import trading_signal, anomaly_detector, calculate_crash_risk
from backend.sentiment import analyze_sentiment
from backend.portfolio_manager import get_portfolio_status

if 'bot_thread' not in st.session_state:
    thread = threading.Thread(target=run_scanner, daemon=True)
    thread.start()
    st.session_state.bot_thread = True

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="AI Institutional Scanner", page_icon="🤖")

# --- AUTO REFRESH LOGIC (5 Minutes) ---
if 'last_run' not in st.session_state:
    st.session_state.last_run = time.time()
if time.time() - st.session_state.last_run > 300:
    st.session_state.last_run = time.time()
    st.rerun()

st.title("🤖 AI Institutional Crypto & Stock Scanner")
st.markdown("---")

# --- WATCHLIST ---
watchlist = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD", "NVDA", "TSLA", "AAPL", "AMZN", "COIN"]
symbol = st.sidebar.selectbox("Select Asset", watchlist)
st.sidebar.markdown("---")
st.sidebar.caption("Auto-refreshes every 5 minutes")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Live Analysis", "🧪 Strategy Backtest", "💼 Live Portfolio"])

# ==========================================
# TAB 1: LIVE ANALYSIS
# ==========================================
with tab1:
    with st.spinner(f"Analyzing {symbol}..."):
        try:
            # 1. Fetch & Process Data
            df = get_price_data(symbol)
            if df.empty:
                st.error("API Error: No data found.")
                st.stop()
            
            df = add_indicators(df)
            df = anomaly_detector(df)
            headlines = get_news_headlines(symbol)
            sentiment_score = analyze_sentiment(headlines)
            signal = trading_signal(df, sentiment_score)
            
            # Metrics Calculation
            last_row = df.iloc[-1]
            crash_risk = calculate_crash_risk(last_row)
            is_whale = last_row['whale_alert'] == 1
            
            # --- METRICS ROW ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Price", f"${last_row['Close']:.2f}")
            
            sig_color = "normal"
            if "BUY" in signal: sig_color = "normal"
            if "SELL" in signal: sig_color = "inverse"
            c2.metric("🚦 Signal", signal, delta_color=sig_color)
            
            risk_color = "off"
            if crash_risk > 50: risk_color = "inverse"
            c3.metric("📉 Crash Risk", f"{crash_risk}%", delta_color=risk_color)
            
            c4.metric("Market Sentiment", f"{sentiment_score:.2f}")

            # --- INTERACTIVE CHART (Plotly) ---
            st.subheader("📈 Institutional Chart")
            
            # Create subplots: Row 1 = Price, Row 2 = RSI
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name='Price'
            ), row=1, col=1)

            # EMAs
            fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], line=dict(color='orange', width=1), name='EMA 50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['ema200'], line=dict(color='blue', width=1), name='EMA 200'), row=1, col=1)

            # Whale Volume Spikes (Markers)
            whale_data = df[df['whale_alert'] == 1]
            if not whale_data.empty:
                fig.add_trace(go.Scatter(
                    x=whale_data.index, y=whale_data['High']*1.02, 
                    mode='markers', marker=dict(symbol='triangle-down', size=10, color='purple'),
                    name='Whale Activity'
                ), row=1, col=1)

            # RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='purple', width=2), name='RSI'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            fig.update_layout(height=600, xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # --- NEWS SECTION ---
            st.markdown("### 📰 News Feed")
            if headlines:
                for i, h in enumerate(headlines[:5]):
                    st.write(f"{i+1}. {h}")
            else:
                st.info("No recent news found.")

        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# TAB 2: BACKTESTING ENGINE
# ==========================================
with tab2:
    st.header(f"🧪 Strategy Backtest: {symbol}")
    st.caption("Simulating your strategy over the last 365 days...")
    
    if st.button("▶ Run Backtest"):
        with st.spinner("Simulating trades..."):
            # 1. Get Long History
            history = get_price_data(symbol, period="1y", interval="1h") # 1 Year of Data
            history = add_indicators(history)
            history = anomaly_detector(history)
            
            # 2. Run Simulation
            balance = 10000 # Start with $10,000
            shares = 0
            trades = []
            
            for i in range(50, len(history)):
                row = history.iloc[i]
                # Pass a dummy sentiment of 0.0 for history (since we don't have historical news)
                # Or you could randomly generate it for stress testing
                sig = trading_signal(history.iloc[:i+1], sentiment_score=0.0) 
                
                price = row['Close']
                
                if "BUY" in sig and balance > 0:
                    shares = balance / price
                    balance = 0
                    trades.append({'date': history.index[i], 'type': 'BUY', 'price': price})
                    
                elif "SELL" in sig and shares > 0:
                    balance = shares * price
                    shares = 0
                    trades.append({'date': history.index[i], 'type': 'SELL', 'price': price})
            
            # Final Value
            final_value = balance if balance > 0 else shares * history.iloc[-1]['Close']
            profit = final_value - 10000
            
            # 3. Display Results
            col1, col2, col3 = st.columns(3)
            col1.metric("Starting Balance", "$10,000")
            col2.metric("Final Balance", f"${final_value:,.2f}", delta=f"{profit:,.2f}")
            col3.metric("Total Trades", len(trades))
            
            if trades:
                trade_df = pd.DataFrame(trades)
                st.dataframe(trade_df, use_container_width=True)
            else:
                st.info("No trades triggered by strategy in this period.")
# ==========================================
# TAB 3: LIVE PORTFOLIO (PAPER TRADING)
# ==========================================
with tab3:
    st.header("💼 Paper Trading Portfolio")
    st.caption("Real-time tracking of bot performance (Virtual Money)")
    
    # 1. Load Data
    data = get_portfolio_status()
    balance = data["balance"]
    positions = data["positions"]
    history = data["history"]
    
    # 2. Calculate Total Equity
    equity = balance
    active_positions = []
    
    if positions:
        for sym, pos in positions.items():
            # We need current price to calc unrealized PnL
            # (Fetching live price might be slow, so we just show entry for now 
            # or fetch if you want precision)
            current_val = pos["shares"] * pos["entry_price"] # Placeholder for live value
            equity += current_val
            
            active_positions.append({
                "Asset": sym,
                "Entry Price": f"${pos['entry_price']:.2f}",
                "Shares": f"{pos['shares']:.4f}",
                "Entry Time": pos["time"]
            })
    
    # 3. Scoreboard
    total_profit = equity - 10000
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Cash Balance", f"${balance:,.2f}")
    col2.metric("💰 Total Equity", f"${equity:,.2f}", delta=f"{total_profit:,.2f}")
    col3.metric("🔓 Open Positions", len(positions))
    
    # 4. Tables
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Holdings")
        if active_positions:
            st.dataframe(pd.DataFrame(active_positions), use_container_width=True)
        else:
            st.info("No active positions. Cash is King! 👑")
            
    with c2:
        st.subheader("Trade History")
        if history:
            hist_df = pd.DataFrame(history)
            # Reorder columns for readability
            hist_df = hist_df[["time", "symbol", "action", "price", "profit"]]
            st.dataframe(hist_df.sort_values("time", ascending=False), use_container_width=True)
        else:
            st.info("No trades executed yet.")
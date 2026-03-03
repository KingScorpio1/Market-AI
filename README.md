# 🤖 Institutional AI Market Scanner & Trading Bot

An advanced, autonomous trading system and analytics dashboard built with Python. This project utilizes Machine Learning, Sentiment Analysis, and Real-Time Market Data to detect market anomalies, manage risk with trailing stop-losses, and execute paper trades. 

It also features a **"Man vs. Machine" Trading Arena**, allowing human traders to compete against the AI in real-time while receiving immediate critiques on their trading decisions.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)
![Supabase](https://img.shields.io/badge/Supabase-Database-green.svg)

---

## ✨ Core Features

*   **🧠 Machine Learning Predictor:** Uses `RandomForestRegressor` to forecast the next timeframe's closing price, preventing false breakouts.
*   **🐋 Anomaly & Whale Detection:** Uses `IsolationForest` to detect unnatural volume spikes and hidden institutional buying/selling.
*   **🛡️ Dynamic Risk Management:** Implements automated **Trailing Stop-Losses** to lock in profits as assets appreciate.
*   **📰 NLP Sentiment Analysis:** Scrapes real-time RSS feeds (Yahoo Finance & CoinDesk) to calculate market sentiment using Natural Language Processing.
*   **⚔️ Man vs. Machine Arena:** A Streamlit dashboard where you manage a virtual portfolio alongside the Bot. The AI analyzes your manual trades and critiques your timing based on technical indicators.
*   **⚡ Real-Time Data Fallbacks:** Connects directly to exchange order books via `CCXT` (Binance) for instant crypto pricing, falling back to `yfinance` for stocks and micro-cap tokens.
*   **📱 Multi-Channel Alerts:** Pushes critical signals and trade executions instantly via Telegram and Email.
*   **☁️ Cloud Database:** Uses Supabase (PostgreSQL) with custom-built network retry logic to persistently track portfolios and trade history without data loss.

---

## 🛠️ Tech Stack

*   **Backend:** Python, Pandas, NumPy
*   **Machine Learning:** Scikit-Learn (`RandomForest`, `IsolationForest`)
*   **Technical Analysis:** `ta` library (RSI, MACD, EMAs, ATR, ADX)
*   **Data Providers:** `ccxt` (Crypto), `yfinance` (Stocks), `feedparser` (News RSS)
*   **Database:** Supabase (PostgreSQL)
*   **Frontend/Dashboard:** Streamlit, Plotly
*   **Alerts:** `python-telegram-bot`, `smtplib`

---

## 📁 Project Structure

```text
market_ai/
│
├── backend/
│   ├── ai_engine.py         # Anomaly detection & rule-based strategy
│   ├── data_fetcher.py      # CCXT & yfinance API connections with retry logic
│   ├── indicators.py        # Technical Analysis calculations
│   ├── portfolio_manager.py # Supabase DB logic & Trailing Stops
│   ├── predictor.py         # RandomForest ML Price Prediction
│   └── sentiment.py         # NLP RSS News sentiment analyzer
│
├── bot/
│   ├── bot_runner.py        # The primary autonomous scanner (Hourly)
│   ├── stock_scalper.py     # Aggressive 1-minute stock scalping bot
│   └── telegram_bot.py      # Telegram API integrations
│
├── dashboard/
│   └── app.py               # Streamlit Dashboard (Charts, Backtesting, Arena)
│
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/market_ai.git
cd market_ai
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your API keys:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
TELEGRAM_MAIN_TOKEN=your_telegram_bot_token
TELEGRAM_SCALPER_TOKEN=your_scalper_bot_token
TELEGRAM_CHAT_ID=your_chat_id
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_google_app_password
```

### 4. Initialize the Supabase Database
Run the following SQL in your Supabase SQL Editor to generate the necessary tables:
```sql
CREATE TABLE portfolio (id int PRIMARY KEY, balance float8 DEFAULT 10000.0, trader TEXT DEFAULT 'bot');
CREATE TABLE positions (symbol TEXT, entry_price FLOAT8, shares FLOAT8, entry_time TIMESTAMP DEFAULT NOW(), trader TEXT DEFAULT 'bot', highest_price FLOAT8);
CREATE TABLE trade_history (id SERIAL PRIMARY KEY, time TIMESTAMP DEFAULT NOW(), symbol TEXT, action TEXT, price FLOAT8, shares FLOAT8, value FLOAT8, profit FLOAT8 DEFAULT 0, trader TEXT DEFAULT 'bot');

-- Initialize Bot and Human starting balances
INSERT INTO portfolio (id, balance, trader) VALUES (1, 10000.0, 'bot'), (2, 10000.0, 'human');
```

---

## 💻 Running the System

To launch the full system (Visual Dashboard + Background AI Bot), run:
```bash
python -m streamlit run dashboard/app.py
```
*The Streamlit dashboard will open at `http://localhost:8501`.*

**Optional Standalone Commands:**
If you want to run the bots headlessly (without the dashboard):
*   `python bot/bot_runner.py` (Standard Scanner)
*   `python bot/stock_scalper.py` (Minute Scalper)

---

## ⚠️ Disclaimer
**For Educational Purposes Only.** 
This software is provided "as is" and without warranty of any kind. The AI predictions, technical indicators, and automated trades are entirely simulated (paper trading) by default. Do not use this system to trade real money without extensive modification, backtesting, and understanding of the financial risks involved.
```
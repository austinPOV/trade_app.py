
# FULL SMART TRADER APP CODE (DARK THEME, MODERN FILTERS, FULL FEATURES)

import streamlit as st
import json
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime

# Load JSON utility
def load_json(path, fallback):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return fallback

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

ideas_data = load_json("daily_trade_ideas.json", {"date": str(datetime.today().date()), "ideas": []})
portfolio = load_json("portfolio.json", {"budget": 0.0, "trades": []})

# Configure page layout
st.set_page_config("📈 Smart Trader AI", layout="wide")

# Apply modern dark theme
st.markdown("""
    <style>
    body, .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    .block-container {
        padding-top: 1rem;
    }
    .st-bb, .st-bf {
        background-color: #1e1e1e;
        border: 1px solid #00f0ff;
        border-radius: 10px;
        padding: 10px;
    }
    .stButton>button {
        color: black;
        background-color: #00f0ff;
        border-radius: 10px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Top Controls
cols = st.columns([1, 1, 1, 1, 1])
portfolio["budget"] = cols[0].number_input("💵 Budget", value=float(portfolio.get("budget", 0.0)), step=100.0, format="%.2f")
risk = cols[1].selectbox("🎯 Risk", ["Low", "Moderate", "High"])
sector_filter = cols[2].selectbox("🏭 Sector", ["All", "Communication Services", "Consumer Discretionary", "Consumer Staples", "Energy", "Financials", "Health Care", "Industrials", "Information Technology", "Materials", "Real Estate", "Utilities"])
max_sector = cols[3].slider("📊 % per Sector", 0, 100, 30, step=5)
max_asset_type = cols[4].slider("📦 % per Asset Type", 0, 100, 40, step=5)
save_json("portfolio.json", portfolio)

# Show chart function
def display_chart(ticker, chart_type):
    df = yf.download(ticker, period="3mo", interval="1d")
    df.index.name = 'Date'
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    if df.empty:
        st.warning("Chart data unavailable.")
        return
    if chart_type == "Candlestick":
        fig, ax = plt.subplots()
        mpf.plot(df, type='candle', style='charles', ax=ax, volume=True)
        st.pyplot(fig)
    else:
        fig, ax = plt.subplots()
        df['Close'].plot(ax=ax, color='#00f0ff')
        ax.set_xlabel("Date")
        ax.set_ylabel("Price (USD)")
        ax.set_title(f"{ticker} — Line Chart")
        st.pyplot(fig)

# Sell signal analyzer
def analyze_sell_signals(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        close = df["Close"]
        rsi = 100 - (100 / (1 + close.pct_change().rolling(14).mean() / close.pct_change().rolling(14).std()))
        macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
        signal = macd.ewm(span=9).mean()
        boll = close.rolling(20).mean() + 2 * close.rolling(20).std()
        price = close.iloc[-1]
        signals = []
        if rsi.iloc[-1] > 70: signals.append("RSI > 70")
        if macd.iloc[-1] < signal.iloc[-1]: signals.append("MACD Bearish")
        if price > boll.iloc[-1]: signals.append("Price > Bollinger Upper")
        return {"price": price, "rsi": round(rsi.iloc[-1], 2), "macd": round(macd.iloc[-1], 2), "signal": round(signal.iloc[-1], 2), "boll_upper": round(boll.iloc[-1], 2), "sell_reasons": signals}
    except:
        return None

# Filter logic
def filter_ideas():
    output = []
    for i in ideas_data["ideas"]:
        if risk == "Low" and i["volatility"] != "low": continue
        if risk == "Moderate" and i["volatility"] == "high": continue
        if sector_filter != "All" and i["sector"].lower() != sector_filter.lower(): continue
        output.append(i)
    return sorted(output, key=lambda x: x["score"], reverse=True)

# Show Trade Ideas
st.markdown("## 📈 Trade Opportunities")
for idx, idea in enumerate(filter_ideas()):
    with st.expander(f"{idea['ticker']} — {idea['sector']} | {idea['type']} | Score: {idea['score']}"):
        cols = st.columns([2, 1])
        cols[0].metric("Price", f"${idea['price']:.2f}")
        cols[0].write(f"Volatility: {idea['volatility']}")
        cols[0].write(f"RSI: {idea['RSI']}")
        cols[0].write(f"MACD: {idea['MACD']}")
        cols[1].write(f"Reason: {idea['reason']}")
        cols[1].write(f"Suggested Action: {idea['suggested_action']}")
        chart_type = st.selectbox("Chart Type", ["Line", "Candlestick"], key=f"charttype_{idx}")
        display_chart(idea['ticker'], chart_type)
        if st.button(f"✅ I Bought {idea['ticker']}", key=f"buy_{idx}"):
            portfolio["trades"].append({"ticker": idea['ticker'], "buy_price": idea['price'], "type": idea['type'], "sector": idea['sector'], "date": ideas_data["date"]})
            save_json("portfolio.json", portfolio)
            st.success("Trade logged.")

# Portfolio Tracker
st.markdown("---")
st.markdown("## 📦 My Portfolio")
if not portfolio["trades"]:
    st.info("No trades logged.")
else:
    df = pd.DataFrame(portfolio["trades"])
    live_data = []
    for trade in portfolio["trades"]:
        live = analyze_sell_signals(trade["ticker"])
        if live:
            pnl = round((live["price"] - trade["buy_price"]) / trade["buy_price"] * 100, 2)
            live_data.append({"Ticker": trade["ticker"], "Buy Price": trade["buy_price"], "Current": live["price"], "PnL %": pnl, "Sell Flags": ", ".join(live["sell_reasons"] or ["None"])})
    df_live = pd.DataFrame(live_data)
    st.dataframe(df_live)
    invested = sum(t["buy_price"] for t in portfolio["trades"])
    current = sum(row["Current"] for row in live_data)
    profit = current - invested
    st.markdown(f"**Total Invested:** ${invested:.2f} — **Current Value:** ${current:.2f} — **Net P/L:** ${profit:.2f} ({round(profit/invested*100,2)}%)")
    sector_df = pd.DataFrame(portfolio["trades"])["sector"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(sector_df, labels=sector_df.index, autopct="%1.1f%%")
    ax.axis("equal")
    st.pyplot(fig)

# Save data
save_json("portfolio.json", portfolio)

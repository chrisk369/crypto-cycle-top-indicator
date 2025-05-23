import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pytrends.request import TrendReq
import time
import os

st.set_page_config(page_title="🧠 Crypto Cycle Top Indicator", layout="wide")
st.title("🧠 Crypto Cycle Top Indicator")
st.caption("Combining sentiment, price, and on-chain signals to spot potential cycle tops")

# -------------------------------
# 1. Bitcoin Price (CoinGecko)
# -------------------------------
@st.cache_data
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()["bitcoin"]["usd"]
    else:
        return None

btc_price = get_btc_price()
if btc_price:
    st.metric(label="Bitcoin Price (USD)", value=f"${btc_price:,.2f}")
else:
    st.error("❌ Failed to load Bitcoin price")

# -------------------------------
# 2. Fear & Greed Index
# -------------------------------
@st.cache_data
def get_fear_greed():
    url = "https://api.alternative.me/fng/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        value = int(data["data"][0]["value"])
        sentiment = data["data"][0]["value_classification"]
        return value, sentiment
    return None, None

fear_val, sentiment = get_fear_greed()
if fear_val:
    st.metric("Fear & Greed Index", value=fear_val, delta=sentiment)
else:
    st.error("❌ Fear & Greed Index unavailable")

# -------------------------------
# 3. Google Trends - "Bitcoin"
# -------------------------------
@st.cache_data(ttl=86400)
def get_google_trends_score():
    pytrends = TrendReq()
    try:
        pytrends.build_payload(["Bitcoin"], timeframe='now 7-d')
        data = pytrends.interest_over_time()
        if not data.empty:
            avg_score = data["Bitcoin"].mean()
            return avg_score
        return None
    except Exception:
        return None

gtrend_score = get_google_trends_score()
if gtrend_score:
    st.metric("Google Trends Score", value=f"{gtrend_score:.1f}")
else:
    st.warning("Google Trends data not available.")

# -------------------------------
# 4. Pi Cycle Indicator (last 365 days)
# -------------------------------
@st.cache_data
def get_btc_price_history():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "365"}
    headers = {"accept": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200 and "prices" in response.json():
        prices = response.json()["prices"]
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("date", inplace=True)
        df["price"] = df["price"].astype(float)
        return df[["price"]]
    return None

def compute_pi_cycle(df):
    if df is None or len(df) < 350:
        return None
    df["111ema"] = df["price"].ewm(span=111, adjust=False).mean()
    df["350sma"] = df["price"].rolling(window=350).mean()
    df["2x_350sma"] = df["350sma"] * 2
    df["pi_signal"] = df["111ema"] > df["2x_350sma"]
    df["pi_value"] = ((df["111ema"] - df["2x_350sma"]) / df["2x_350sma"]) * 100
    df["pi_value"] = df["pi_value"].clip(lower=0)
    return df

def get_pi_cycle_signal():
    df = get_btc_price_history()
    if df is not None:
        df = compute_pi_cycle(df)
        if df is not None:
            latest = df.dropna().iloc[-1]
            return latest["pi_signal"], latest["pi_value"], df
    return None, None, None

pi_signal, pi_value, pi_df = get_pi_cycle_signal()
if pi_signal is not None:
    st.markdown("### 🟣 Pi Cycle Indicator")
    st.markdown(f"#### Pi Signal Active: {pi_signal} | Value: {pi_value:.2f}")
    st.line_chart(pi_df[["price", "111ema", "2x_350sma"]].dropna().tail(300))
else:
    st.warning("Pi Cycle not available (only last 365 days supported).")

# -------------------------------
# 5. Cycle Score Calculation
# -------------------------------
def calculate_cycle_score(price, fear, trend, dominance, pi_active, pi_val):
    score = 0
    if price:
        score += min(price / 1000, 40)
    if fear:
        score += fear * 0.3
    if trend:
        score += min(trend / 2, 15)
    if dominance is not None:
        if dominance < 40:
            score += 10
        elif dominance < 45:
            score += 5
    if pi_active:
        score += 15
    if pi_val:
        if pi_val > 10:
            score += pi_val * 0.1
    return int(min(score, 100))

score = calculate_cycle_score(
    btc_price, fear_val, gtrend_score, 60.52,
    pi_signal if pi_signal else False,
    pi_value if pi_value else 0
)

st.subheader("🧮 Cycle Top Score")
st.markdown(f"### **{score}/100**")
if score > 85:
    st.error("⚠️ High risk of cycle top — Consider caution!")
elif score > 70:
    st.warning("😬 Elevated risk — Monitor closely")
else:
    st.success("✅ Risk moderate or low")

# -------------------------------
# 6. Save & Show Score History
# -------------------------------
DATA_FILE = "score_history.csv"

def save_score_history(score):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    new_entry = pd.DataFrame([[now, score]], columns=["timestamp", "score"])
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_entry], ignore_index=True)
    else:
        df = new_entry
    df.to_csv(DATA_FILE, index=False)

save_score_history(score)

st.markdown("### 📈 Score History")
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    st.line_chart(df.set_index("timestamp")["score"])
else:
    st.info("No historical data yet.")

st.caption("Data: CoinGecko, Alternative.me, Google Trends | Built with Streamlit")


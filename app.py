import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pytrends.request import TrendReq
import talib  # For RSI, MACD
import time
import numpy as np
import os

st.set_page_config(page_title="Crypto Cycle Top Indicator", layout="wide")
st.title("🧠 Crypto Cycle Top Indicator")
st.caption("Combining sentiment, price, and on-chain signals to spot potential cycle tops")

# -------------------------------
# 1. Bitcoin Price (CoinGecko)
# -------------------------------
@st.cache_data
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    headers = {"User-Agent": "Mozilla/5.0"}  # Basic header to avoid some rejections
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()["bitcoin"]["usd"]
    else:
        st.error(f"🔒 Unauthorized ({response.status_code}). CoinGecko may be rejecting the request.")
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
        st.warning("⏳ Too many requests to Google Trends. Retrying...")
        time.sleep(60)
        return get_google_trends_score()

gtrend_score = get_google_trends_score()
if gtrend_score:
    st.metric("Google Trends Score", value=f"{gtrend_score:.1f}")
else:
    st.warning("Google Trends data not available.")

# -------------------------------
# 4. RSI and Daily RSI Calculation
# -------------------------------
@st.cache_data
def get_btc_price_history():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "365"}
    headers = {
        "accept": "application/json"
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        prices = response.json()["prices"]
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit='ms')
        df.set_index("date", inplace=True)
        return df
    return None

def calculate_rsi(df):
    df['RSI'] = talib.RSI(df['price'], timeperiod=14)
    return df

# -------------------------------
# 5. MACD Calculation
# -------------------------------
def calculate_macd(df):
    df['MACD'], df['MACD_Signal'], _ = talib.MACD(df['price'], fastperiod=12, slowperiod=26, signalperiod=9)
    return df

# -------------------------------
# 6. Power Law Oscillator Calculation
# -------------------------------
def power_law_oscillator(df):
    price_changes = df['price'].pct_change().dropna()
    exponent = 2  # Typical exponent used in Power Law analysis
    pl_oscillator = (price_changes ** exponent).mean()
    return pl_oscillator

# -------------------------------
# 7. Thermocap Calculation (Stock-to-Flow)
# -------------------------------
def get_thermocap():
    # Get Bitcoin's supply and market cap from CoinGecko
    supply = get_btc_supply()  # Supply data from CoinGecko
    market_cap = get_btc_market_cap()  # Market cap data from CoinGecko
    thermocap = market_cap / supply  # Stock-to-Flow ratio
    return thermocap

# -------------------------------
# 8. Calculate Cycle Score
# -------------------------------
def calculate_cycle_score(price, fear, trend, dominance, pi_active, pi_val, rsi, macd, thermocap, plo):
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
    if rsi:
        score += (rsi / 100) * 10  # Scale RSI between 0 and 100
    if macd:
        score += macd.mean()  # Use average MACD value
    score += thermocap * 5  # Adjust weight
    score += plo * 10  # Adjust weight
    return int(min(score, 100))

# -------------------------------
# 9. Save & Show Score History
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


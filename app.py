import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
import time
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
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()["bitcoin"]["usd"]
    else:
        st.error(f"Error fetching data: {response.status_code}")
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
@st.cache_data(ttl=86400)  # Cache data for 24 hours
def get_google_trends_score():
    pytrends = TrendReq()
    pytrends.build_payload(["Bitcoin"], timeframe='now 7-d')
    
    try:
        data = pytrends.interest_over_time()
        if not data.empty:
            avg_score = data["Bitcoin"].mean()
            return avg_score
        return None
    except TooManyRequestsError:
        st.error("Too many requests to Google Trends. Please wait a few minutes and try again.")
        return None

gtrend_score = get_google_trends_score()
if gtrend_score:
    st.metric("Google Trends Score", value=f"{gtrend_score:.1f}")
else:
    st.warning("Google Trends data not available.")

# -------------------------------
# 5. Pi Cycle Indicator with Value
# -------------------------------
@st.cache_data
def get_btc_price_history():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "max"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        prices = response.json()["prices"]
        if len(prices) > 0:
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["date"] = pd.to_datetime(df["timestamp"], unit='ms')
            df.set_index("date", inplace=True)
            df["price"] = df["price"].astype(float)
            return df[["price"]]
        else:
            st.warning("No price data returned from CoinGecko.")
            return None
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

def compute_pi_cycle(df):
    # Check if the dataframe has enough data
    if df is None or len(df) < 350:
        st.warning("Not enough data for Pi Cycle calculation.")
        return df

    df["111ema"] = df["price"].ewm(span=111, adjust=False).mean()
    df["350sma"] = df["price"].rolling(window=350).mean()
    df["2x_350sma"] = df["350sma"] * 2
    df["pi_signal"] = df["111ema"] > df["2x_350sma"]
    
    # Adding Pi Cycle Value (quantified signal strength)
    df["pi_value"] = (df["111ema"] - df["2x_350sma"]) / df["2x_350sma"] * 100  # Percentage difference
    df["pi_value"] = df["pi_value"].clip(lower=0)  # Ensure value can't be negative
    return df

def get_pi_cycle_signal():
    df = get_btc_price_history()
    if df is not None:
        df = compute_pi_cycle(df)
        latest = df.iloc[-1]
        signal = latest["pi_signal"]
        value = latest["pi_value"]
        return signal, value, df
    else:
        st.warning("Pi Cycle data is unavailable. Check Bitcoin price history data.")
        return None, None, None

def categorize_pi_cycle_value(value):
    if value > 20:
        return "🟢 Very Far"
    elif value > 10:
        return "🟡 Far"
    elif value > 0:
        return "🟠 Neutral"
    elif value > -5:
        return "🟣 Close"
    else:
        return "🔴 Very Close Warning"

# Pi Cycle Signal & Value Display
pi_signal, pi_value, pi_df = get_pi_cycle_signal()
if pi_signal is not None:
    pi_category = categorize_pi_cycle_value(pi_value)
    st.markdown("### 🟣 Pi Cycle Indicator")
    st.markdown(f"#### Pi Cycle Signal: {pi_category} (Pi Value: {pi_value:.2f})")

    # Pi Cycle Chart with Pi Value
    st.markdown("### 📊 Pi Cycle Chart (Last 500 Days)")
    if pi_df is not None:
        chart_df = pi_df[["price", "111ema", "2x_350sma", "pi_value"]].tail(500).dropna()  # Include pi_value in chart
        st.line_chart(chart_df)
else:
    st.warning("Pi Cycle data not available. Try again later.")

# -------------------------------
# 6. Refined Cycle Score Calculation
# -------------------------------
def calculate_cycle_score(price, fear, trend, dominance, pi_active, pi_value):
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
    if pi_active is not None:  # Make sure pi_signal is not None
        score += 15
    if pi_value is not None:  # Check that pi_value is valid
        if pi_value > 10:  # If the Pi Value is significant
            score += pi_value * 0.1
    return int(min(score, 100))

# Make sure we handle None values for Pi Cycle
pi_signal = pi_signal if pi_signal is not None else False
pi_value = pi_value if pi_value is not None else 0

score = calculate_cycle_score(btc_price, fear_val, gtrend_score, 60.52, pi_signal, pi_value)

st.subheader("🧮 Cycle Top Score")
st.markdown(f"### **{score}/100**")
if score > 85:
    st.error("⚠️ High risk of cycle top — Consider caution!")
elif score > 70:
    st.warning("😬 Elevated risk — Monitor closely")
else:
    st.success("✅ Risk moderate or low")

# -------------------------------
# 7. Save and Display Score History
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
    st.info("No historical data yet. Come back after the app has run a few times.")

st.caption("Data: CoinGecko, Alternative.me, Google Trends | Built by You + ChatGPT")

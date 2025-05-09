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
        time.sleep(60)  # Adding delay before retrying
        return get_google_trends_score()  # Retry fetching the data

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
    retries = 3  # Retry 3 times if there is an error
    for _ in range(retries):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            prices = response.json()["prices"]
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["date"] = pd.to_datetime(df["timestamp"], unit='ms')
            df.set_index("date", inplace=True)
            df["price"] = df["price"].astype(float)
            return df[["price"]]
        else:
            st.error(f"Error fetching data: {response.status_code}")
            time.sleep(5)  # Wait for 5 seconds before retrying
    return None

def compute_pi_cycle(df):
    if df is None or len(df) < 350:
        st.warning("Not enough data for Pi Cycle calculation.")
        return df

    df["111ema"] = df["price"].ewm(span=111, adjust=False).mean()
    df["350sma"] = df["price"].rolling(window=350).mean()
    df["2x_350sma"] = df["350]()_]()

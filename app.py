import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
from pytrends.request import TrendReq

st.set_page_config(page_title="Crypto Cycle Top Indicator", layout="wide")
st.title("🧠 Crypto Cycle Top Indicator")
st.caption("Combining sentiment, price, and on-chain signals to spot potential cycle tops")

# -------------------------------
# 1. Bitcoin Price (CoinGecko)
# -------------------------------
@st.cache(ttl=300)
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()["bitcoin"]["usd"]
    return None

btc_price = get_btc_price()
if btc_price:
    st.metric(label="Bitcoin Price (USD)", value=f"${btc_price:,.2f}")
else:
    st.error("❌ Failed to load Bitcoin price")

# -------------------------------
# 2. Fear & Greed Index
# -------------------------------
def get_fear_greed():
    url = "https://api.alternative.me/fng/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        value = int





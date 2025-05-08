import streamlit as st
import requests

st.set_page_config(page_title="Crypto Cycle Top Indicator", layout="wide")
st.title("Crypto Cycle Top Indicator")
st.caption("Aggregated Metrics to Identify Market Cycle Extremes")

# ----------------------
# 1. Get Bitcoin Price
# ----------------------
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data["bitcoin"]["usd"]
    return None

btc_price = get_btc_price()
if btc_price:
    st.metric(label="Bitcoin Price (USD)", value=f"${btc_price:,.2f}")
else:
    st.error("Failed to fetch Bitcoin price.")

# -------------------------------
# 2. Get Fear & Greed Index
# -------------------------------
def get_fear_greed():
    url = "https://api.alternative.me/fng/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        value = data["data"][0]["value"]
        value_classification = data["data"][0]["value_classification"]
        return int(value), value_classification
    return None, None

fear_greed_value, sentiment = get_fear_greed()
if fear_greed_value is not None:
    st.metric(label="Fear & Greed Index", value=fear_greed_value, delta=sentiment)
else:
    st.error

import streamlit as st
import requests

st.set_page_config(page_title="Crypto Cycle Top Indicator", layout="wide")

st.title("Crypto Cycle Top Indicator")
st.caption("Aggregated Metrics to Identify Market Cycle Extremes")

# Fetch Bitcoin price data from CoinGecko
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data["bitcoin"]["usd"]
    else:
        return None

btc_price = get_btc_price()

if btc_price:
    st.metric(label="Bitcoin Price (USD)", value=f"${btc_price:,.2f}")
else:
    st.error("Failed to fetch Bitcoin price data.")

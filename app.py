import streamlit as st
import requests
from pytrends.request import TrendReq
import datetime

# Streamlit page setup
st.set_page_config(page_title="Crypto Cycle Top Indicator", layout="wide")
st.title("🧠 Crypto Cycle Top Indicator")
st.caption("Combining sentiment, trend, and price signals to help spot cycle tops")

# -------------------------------
# 1. Bitcoin Price (CoinGecko)
# -------------------------------
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["bitcoin"]["usd"]
    return None

btc_price = get_btc_price()
if btc_price:
    st.metric(label="Bitcoin Price (USD)", value=f"${btc_price:,.2f}")
else:
    st.error("Failed to load BTC price.")

# -------------------------------
# 2. Fear & Greed Index
# -------------------------------
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
    st.error("Fear & Greed Index unavailable.")

# -------------------------------
# 3. Google Trends for "Bitcoin"
# -------------------------------
def get_google_trend_score(keyword="bitcoin"):
    pytrends = TrendReq()
    today = datetime.date.today()
    last_month = today - datetime.timedelta(days=30)
    pytrends.build_payload([keyword], cat=0, timeframe='now 30-d', geo='', gprop='')
    data = pytrends.interest_over_time()
    if not data.empty:
        score = int(data[keyword].mean())
        return score
    return None

trend_score = get_google_trend_score()
if trend_score:
    st.metric("Google Trends: Bitcoin", value=trend_score)
else:
    st.warning("Google Trends data unavailable.")

# -------------------------------
# 4. Combined Cycle Score
# -------------------------------
def calculate_cycle_score(price, fear_greed, trend):
    score = 0
    if price:
        score += min(price / 1000, 40)  # normalize BTC price
    if fear_greed:
        score += fear_greed * 0.3      # weight for sentiment
    if trend:
        score += trend * 0.2           # weight for search interest
    return int(min(score, 100))

score = calculate_cycle_score(btc_price, fear_val, trend_score)

st.subheader("🧮 Cycle Top Score")
st.markdown(f"### **{score}/100**")

# Color warning
if score > 85:
    st.error("⚠️ High risk of cycle top — Consider caution!")
elif score > 70:
    st.warning("😬 Elevated risk — Monitor closely")
else:
    st.success("✅ Risk moderate or low")

# Footer
st.markdown("---")
st.caption("Data: CoinGecko, Alternative.me, Google Trends | Built by Chris + ChatGPT")


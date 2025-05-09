import streamlit as st
import requests

st.set_page_config(page_title="Crypto Cycle Top Indicator", layout="wide")
st.title("🧠 Crypto Cycle Top Indicator")
st.caption("Combining sentiment and price signals to help spot cycle tops")

# -------------------------------
# 1. Bitcoin Price (CoinGecko)
# -------------------------------
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
# 3. Combined Cycle Score (price + sentiment only)
# -------------------------------
def calculate_cycle_score(price, fear_greed):
    score = 0
    if price:
        score += min(price / 1000, 40)  # normalize BTC price
    if fear_greed:
        score += fear_greed * 0.4       # weight for sentiment
    return int(min(score, 100))

score = calculate_cycle_score(btc_price, fear_val)

st.subheader("🧮 Cycle Top Score")
st.markdown(f"### **{score}/100**")

# Color-coded alert
if score > 85:
    st.error("⚠️ High risk of cycle top — Consider caution!")
elif score > 70:
    st.warning("😬 Elevated risk — Monitor closely")
else:
    st.success("✅ Risk moderate or low")

st.markdown("---")
st.caption("Data: CoinGecko, Alternative.me | Built by Chris + ChatGPT")



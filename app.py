import streamlit as st
import requests
from pytrends.request import TrendReq

st.set_page_config(page_title="Crypto Cycle Top Indicator", layout="wide")
st.title("🧠 Crypto Cycle Top Indicator")
st.caption("Combining sentiment and price signals to help spot crypto cycle tops")

# -------------------------------
# 1. Bitcoin Price (CoinGecko)
# -------------------------------
@st.cache_data(ttl=300)
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
@st.cache_data(ttl=300)
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
# 3. Google Trends (PyTrends)
# -------------------------------
@st.cache_data(ttl=3600)
def get_google_trends_score():
    pytrends = TrendReq(hl='en-US', tz=360)
    kw_list = ["Bitcoin"]
    pytrends.build_payload(kw_list, cat=0, timeframe='now 7-d', geo='', gprop='')
    data = pytrends.interest_over_time()
    if not data.empty:
        trend_score = int(data["Bitcoin"].mean())
        return trend_score
    return None

trend_score = get_google_trends_score()
if trend_score is not None:
    st.metric("Google Trends (Bitcoin)", value=trend_score)
else:
    st.error("❌ Google Trends data unavailable")

# -------------------------------
# 4. Volume Spike Detection
# -------------------------------
@st.cache_data(ttl=300)
def get_btc_volume():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": 7}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        volumes = [v[1] for v in data["total_volumes"]]
        avg_volume = sum(volumes) / len(volumes)
        latest_volume = volumes[-1]
        return latest_volume, avg_volume
    return None, None

volume_now, avg_volume = get_btc_volume()
if volume_now:
    delta = volume_now - avg_volume
    st.metric("24h Volume (vs 7d Avg)", value=f"${volume_now/1e9:.2f}B", delta=f"{delta/1e9:.2f}B")
else:
    st.error("❌ BTC volume data unavailable")

# -------------------------------
# 5. Combined Cycle Top Score
# -------------------------------
def calculate_cycle_score(price, fear_greed, trend_score, volume_now, avg_volume):
    score = 0
    if price:
        score += min(price / 1000, 40)  # Max 40
    if fear_greed:
        score += fear_greed * 0.3       # Max ~30
    if trend_score is not None:
        score += min(trend_score / 2, 15)  # Max 15
    if volume_now and avg_volume:
        volume_ratio = volume_now / avg_volume
        if volume_ratio > 2:
            score += 15
        elif volume_ratio > 1.5:
            score += 10
        else:
            score += 5
    return int(min(score, 100))

score = calculate_cycle_score(btc_price, fear_val, trend_score, volume_now, avg_volume)

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
st.caption("Data: CoinGecko, Alternative.me, Google Trends | Built by Chris + ChatGPT")



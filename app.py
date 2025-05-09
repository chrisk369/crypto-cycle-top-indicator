# -------------------------------
# 5. Pi Cycle Indicator with Value
# -------------------------------
@st.cache_data(ttl=86400)
def get_btc_price_history():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "max"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        prices = response.json()["prices"]
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit='ms')
        df.set_index("date", inplace=True)
        df["price"] = df["price"].astype(float)
        return df[["price"]]
    return None

def compute_pi_cycle(df):
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





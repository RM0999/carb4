
import streamlit as st
import requests
from datetime import datetime

# ----🔐 API Keys Section (configure via secrets.toml) ----
api_keys = st.secrets["api_keys"]

# ---- 💱 Live USD to AUD conversion rate (static fallback) ----
USD_TO_AUD = 1.52

# ---- 🪙 Symbol mappings per exchange ----
SYMBOLS = {
    "BTC": {"Coinbase": "BTC-USD", "Crypto.com": "BTC_USDT", "CoinSpot": "BTC"},
    "ETH": {"Coinbase": "ETH-USD", "Crypto.com": "ETH_USDT", "CoinSpot": "ETH"},
    "ADA": {"Coinbase": "ADA-USD", "Crypto.com": "ADA_USDT", "CoinSpot": "ADA"},
    "DOGE": {"Coinbase": "DOGE-USD", "Crypto.com": "DOGE_USDT", "CoinSpot": "DOGE"},
    "SHIB": {"Coinbase": "SHIB-USD", "Crypto.com": "SHIB_USDT", "CoinSpot": "SHIB"},
    "MATIC": {"Coinbase": "MATIC-USD", "Crypto.com": "MATIC_USDT", "CoinSpot": "MATIC"}
}

# ---- Streamlit UI setup ----
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.title("🔍 Crypto Arbitrage Scanner")

with st.sidebar:
    st.header("⚙️ Settings")
    coin = st.selectbox("Select Coin", list(SYMBOLS.keys()))
    min_profit = st.slider("Minimum Profit %", 0.1, 5.0, 0.5)
    investment = st.number_input("Investment (AUD)", 10, 10000, 1000)
    exchanges = st.multiselect("Exchanges", ["Coinbase", "Crypto.com", "CoinSpot"], default=["Coinbase", "Crypto.com", "CoinSpot"])

# ---- Fetcher functions ----
def fetch_coinbase(symbol):
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{symbol}/spot").json()
        price_usd = float(r["data"]["amount"])
        return {"buy": price_usd * USD_TO_AUD, "sell": price_usd * USD_TO_AUD, "fee": 0.006}
    except:
        return None

def fetch_crypto(symbol):
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}").json()
        data = r["result"]["data"]
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.004}
    except:
        return None

def fetch_coinspot(symbol):
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        ask = float(r["prices"][symbol]["ask"])
        bid = float(r["prices"][symbol]["bid"])
        return {"buy": ask, "sell": bid, "fee": 0.01}
    except:
        return None

# ---- Dispatchers ----
fetchers = {
    "Coinbase": lambda: fetch_coinbase(SYMBOLS[coin]["Coinbase"]),
    "Crypto.com": lambda: fetch_crypto(SYMBOLS[coin]["Crypto.com"]),
    "CoinSpot": lambda: fetch_coinspot(SYMBOLS[coin]["CoinSpot"])
}

# ---- Run Scan ----
data = {ex: fetchers[ex]() for ex in exchanges if fetchers[ex]()}
valid_data = {ex: val for ex, val in data.items() if val}

if valid_data:
    best_buy = min(valid_data.items(), key=lambda x: x[1]["buy"])
    best_sell = max(valid_data.items(), key=lambda x: x[1]["sell"])
    spread = best_sell[1]["sell"] - best_buy[1]["buy"]
    gross_profit_pct = round((spread / best_buy[1]["buy"]) * 100, 2)
    net_profit_pct = round(gross_profit_pct - (best_buy[1]["fee"] + best_sell[1]["fee"]) * 100, 2)
    net_profit_aud = round(investment * net_profit_pct / 100, 2)

    if net_profit_pct >= min_profit:
        st.success(f"🚀 Arbitrage Found at {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"🛒 Buy from **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
        st.write(f"💰 Sell on **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
        st.write(f"🔄 Spread: **AUD ${spread:.2f}** ({gross_profit_pct}%)")
        st.write(f"💸 Net Profit: **{net_profit_pct}%** | **AUD ${net_profit_aud}**")
        st.caption(f"Fees: Buy Fee = {best_buy[1]['fee']*100:.2f}%, Sell Fee = {best_sell[1]['fee']*100:.2f}%")
    else:
        st.warning("No profitable arbitrage opportunity found above your threshold.")
else:
    st.error("Failed to fetch data from all selected exchanges.")

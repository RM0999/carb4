
import streamlit as st
import requests
import hmac
import hashlib
import time
import json
from datetime import datetime

# --- Constants ---
USD_TO_AUD = 1.52  # Static FX rate (can be replaced with real-time later)

# --- Streamlit Config ---
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔍 Real-Time Arbitrage Scanner</h1>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Select Coin", ["BTC", "ETH", "LTC", "XRP", "ADA", "DOGE", "SHIB", "MATIC"])
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    exchanges = st.multiselect("Exchanges", [
        "Coinbase", "Crypto.com", "CoinSpot", "Kraken", "IndependentReserve"
    ], default=["Coinbase", "Crypto.com", "CoinSpot", "Kraken", "IndependentReserve"])

# --- Exchange Fetch Functions ---
def fetch_coinbase(symbol):
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot").json()
        price = float(r["data"]["amount"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except:
        return None

def fetch_kraken(symbol):
    try:
        pair_map = {"BTC": "XBT", "ETH": "ETH", "LTC": "LTC", "XRP": "XRP", "ADA": "ADA", "DOGE": "DOGE", "SHIB": "SHIB", "MATIC": "MATIC"}
        pair = f"{pair_map[symbol]}USD"
        url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
        r = requests.get(url).json()
        kr_pair = list(r["result"].keys())[0]
        data = r["result"][kr_pair]
        return {"buy": float(data["a"][0]) * USD_TO_AUD, "sell": float(data["b"][0]) * USD_TO_AUD, "fee": 0.0026}
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

def fetch_independent_reserve(symbol):
    try:
        url = f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={symbol}&secondaryCurrencyCode=AUD"
        r = requests.get(url).json()
        return {"buy": float(r["CurrentLowestOfferPrice"]), "sell": float(r["CurrentHighestBidPrice"]), "fee": 0.005}
    except:
        return None

def fetch_crypto_com(symbol):
    try:
        pair_map = {"BTC": "BTC_USDT", "ETH": "ETH_USDT", "LTC": "LTC_USDT", "XRP": "XRP_USDT", "ADA": "ADA_USDT", "DOGE": "DOGE_USDT", "SHIB": "SHIB_USDT", "MATIC": "MATIC_USDT"}
        pair = pair_map[symbol]
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={pair}").json()
        data = r["result"]["data"]
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

# --- Mapping ---
fetchers = {
    "Coinbase": fetch_coinbase,
    "Crypto.com": fetch_crypto_com,
    "CoinSpot": fetch_coinspot,
    "Kraken": fetch_kraken,
    "IndependentReserve": fetch_independent_reserve
}

# --- Arbitrage Calculation ---
st.subheader("📊 Arbitrage Result")
results = {ex: fetchers[ex](coin) for ex in exchanges}
valid_data = {k: v for k, v in results.items() if v}

st.json(valid_data)  # Optional raw data preview

if len(valid_data) >= 2:
    best_buy = min(valid_data.items(), key=lambda x: x[1]["buy"])
    best_sell = max(valid_data.items(), key=lambda x: x[1]["sell"])
    spread = best_sell[1]["sell"] - best_buy[1]["buy"]
    buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit = spread - buy_fee - sell_fee
    profit_pct = round((net_profit / best_buy[1]["buy"]) * 100, 2)
    profit_aud = round(investment * profit_pct / 100, 2)

    if profit_pct >= min_profit:
        st.success(f"🟢 Buy from {best_buy[0]} at AUD ${best_buy[1]['buy']:.2f}, sell on {best_sell[0]} at AUD ${best_sell[1]['sell']:.2f}")
        st.markdown(f'''
**Spread**: AUD ${spread:.2f}  
**Buy Fee**: AUD ${buy_fee:.2f}  
**Sell Fee**: AUD ${sell_fee:.2f}  
**Net Profit**: {profit_pct}% | **AUD ${profit_aud:.2f}**
''')
    else:
        st.warning("No profitable arbitrage opportunity found above your threshold.")
else:
    st.error("Not enough valid exchange data to compare.")

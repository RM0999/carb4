
import streamlit as st
import requests
import hmac
import hashlib
import time
import json
from datetime import datetime

# --- Constants ---
USD_TO_AUD = 1.54  # Static FX for simplicity

COINS = {
    "BTC": {"symbol": "BTC"},
    "ETH": {"symbol": "ETH"},
    "LTC": {"symbol": "LTC"},
    "XRP": {"symbol": "XRP"},
    "ADA": {"symbol": "ADA"},
    "DOGE": {"symbol": "DOGE"},
    "SHIB": {"symbol": "SHIB"},
    "MATIC": {"symbol": "MATIC"},
}

# --- Streamlit Config ---
st.set_page_config(page_title="Live Arbitrage Scanner", layout="wide")
st.title("🔎 Secure Crypto Arbitrage Scanner")

# --- Sidebar ---
with st.sidebar:
    coin = st.selectbox("Select Coin", list(COINS.keys()))
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    exchanges = st.multiselect("Exchanges", [
        "Coinbase", "Crypto.com", "CoinSpot", "Kraken", "IndependentReserve"
    ], default=["Coinbase", "Crypto.com", "Kraken"])

# --- Exchange Fetchers ---
def fetch_coinspot(coin):
    try:
        key = st.secrets["coinspot"]["api_key"]
        secret = st.secrets["coinspot"]["api_secret"]
        req = {"nonce": str(int(time.time() * 1000))}
        msg = json.dumps(req).encode()
        sig = hmac.new(secret.encode(), msg, hashlib.sha512).hexdigest()
        headers = {"Content-type": "application/json", "key": key, "sign": sig}
        r = requests.post("https://www.coinspot.com.au/api/quotes", headers=headers, data=msg).json()
        ask = float(r[coin.lower()]["buy"])
        bid = float(r[coin.lower()]["sell"])
        return {"buy": ask, "sell": bid, "fee": 0.01}
    except:
        return None

def fetch_kraken(coin):
    try:
        map = {"BTC": "XBT", "ETH": "ETH", "LTC": "LTC", "XRP": "XRP", "ADA": "ADA", "DOGE": "DOGE", "SHIB": "SHIB", "MATIC": "MATIC"}
        kr_symbol = map[coin] + "USD"
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={kr_symbol}").json()
        key = list(r["result"].keys())[0]
        data = r["result"][key]
        return {"buy": float(data["a"][0]) * USD_TO_AUD, "sell": float(data["b"][0]) * USD_TO_AUD, "fee": 0.0026}
    except:
        return None

def fetch_independent_reserve(coin):
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD").json()
        return {
            "buy": float(r["CurrentLowestOfferPrice"]),
            "sell": float(r["CurrentHighestBidPrice"]),
            "fee": 0.005
        }
    except:
        return None

def fetch_coinbase(coin):
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{coin}-USD/spot").json()
        price = float(r["data"]["amount"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except:
        return None

def fetch_crypto_com(coin):
    try:
        symbol = f"{coin}_USDT"
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}").json()
        data = r["result"]["data"]
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

fetchers = {
    "CoinSpot": lambda: fetch_coinspot(coin),
    "Kraken": lambda: fetch_kraken(coin),
    "IndependentReserve": lambda: fetch_independent_reserve(coin),
    "Coinbase": lambda: fetch_coinbase(coin),
    "Crypto.com": lambda: fetch_crypto_com(coin),
}

# --- Run Scan ---
raw_data = {ex: fetchers[ex]() for ex in exchanges if fetchers[ex]()}
valid = {ex: data for ex, data in raw_data.items() if data}

st.subheader("📊 Arbitrage Result")
st.json(valid)

if valid:
    best_buy = min(valid.items(), key=lambda x: x[1]["buy"])
    best_sell = max(valid.items(), key=lambda x: x[1]["sell"])
    spread = best_sell[1]["sell"] - best_buy[1]["buy"]

    buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit = spread - buy_fee - sell_fee
    profit_pct = round((net_profit / best_buy[1]["buy"]) * 100, 2)
    profit_aud = round((net_profit / best_buy[1]["buy"]) * investment, 2)

    if profit_pct >= min_profit:
        st.success(f"✅ Opportunity found at {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"Buy from **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
        st.write(f"Sell on **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
        st.write(f"Spread: **AUD ${spread:.2f}**")
        st.write(f"Buy Fee: **AUD ${buy_fee:.2f}**, Sell Fee: **AUD ${sell_fee:.2f}**")
        st.write(f"Net Profit: **{profit_pct}%** | **AUD ${profit_aud:.2f}**")
    else:
        st.warning("No profitable arbitrage opportunity found above your threshold.")
else:
    st.error("❌ No valid data received from any selected exchanges.")

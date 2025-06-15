
import streamlit as st
import requests
import hmac
import hashlib
import time
import base64
import json
from datetime import datetime

# --- Constants ---
USD_TO_AUD = 1.52  # Placeholder; ideally replaced with live FX data
HEADERS = {"Content-Type": "application/json"}

# --- Streamlit Config ---
st.set_page_config(page_title="Secure Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔒 Secure Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Select Coin", ["BTC", "ETH", "LTC", "XRP", "ADA", "DOGE", "SHIB", "MATIC"])
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    exchanges = st.multiselect("Exchanges", [
        "Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase", "Crypto.com"
    ], default=["Binbase", "CoinSpot", "Kraken"])

# --- Helper Functions ---
def timestamp():
    return str(int(time.time() * 1000))

def fetch_coinspot():
    try:
        key = st.secrets["coinspot_api_key"]
        secret = st.secrets["coinspot_secret_key"]
        req = {"nonce": timestamp()}
        msg = json.dumps(req).encode()
        sig = hmac.new(secret.encode(), msg, hashlib.sha512).hexdigest()
        headers = {"Content-type": "application/json", "key": key, "sign": sig}
        r = requests.post("https://www.coinspot.com.au/api/quotes", headers=headers, data=msg).json()
        ask = float(r[coin.lower()]["buy"])
        bid = float(r[coin.lower()]["sell"])
        return {"buy": ask, "sell": bid, "fee": 0.01}
    except:
        return None

def fetch_kraken():
    try:
        pair_map = {"BTC": "XBT", "ETH": "ETH", "LTC": "LTC", "XRP": "XRP", "ADA": "ADA", "DOGE": "DOGE", "SHIB": "SHIB", "MATIC": "MATIC"}
        pair = f"{pair_map[coin]}USD"
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={pair}").json()
        kr_pair = list(r["result"].keys())[0]
        data = r["result"][kr_pair]
        return {
            "buy": float(data["a"][0]) * USD_TO_AUD,
            "sell": float(data["b"][0]) * USD_TO_AUD,
            "fee": 0.0026
        }
    except:
        return None

def fetch_independent_reserve():
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD").json()
        return {
            "buy": float(r["CurrentLowestOfferPrice"]),
            "sell": float(r["CurrentHighestBidPrice"]),
            "fee": 0.005
        }
    except:
        return None

def fetch_coinbase():
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{coin}-USD/spot").json()
        price = float(r["data"]["amount"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except:
        return None

def fetch_crypto_com():
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={coin}_USDT").json()
        data = r["result"]["data"]
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

def fetch_binance():
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={coin}USDT").json()
        return {
            "buy": float(r["askPrice"]) * USD_TO_AUD,
            "sell": float(r["bidPrice"]) * USD_TO_AUD,
            "fee": 0.001
        }
    except:
        return None

# --- API Mapping ---
fetchers = {
    "Binance": fetch_binance,
    "Kraken": fetch_kraken,
    "CoinSpot": fetch_coinspot,
    "IndependentReserve": fetch_independent_reserve,
    "Coinbase": fetch_coinbase,
    "Crypto.com": fetch_crypto_com
}

# --- Live Scan ---
data = {ex: fetchers[ex]() for ex in exchanges if fetchers[ex]() is not None}
valid = {ex: v for ex, v in data.items() if v}

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
        st.success(f"🟢 Arbitrage Opportunity Found at {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"🛒 Buy from: **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
        st.write(f"💰 Sell on: **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
        st.write(f"🔄 Spread: **AUD ${spread:.2f}**")
        st.write(f"💸 Net Profit: **{profit_pct}%** | **AUD ${profit_aud}**")
        st.caption(f"Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
    else:
        st.warning("No profitable arbitrage opportunity found above your threshold.")
else:
    st.error("⚠️ Could not retrieve valid data from any selected exchange.")

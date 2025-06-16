
import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>💱 Crypto Arbitrage Scanner with Live AUD/USD & Secure API</h1>", unsafe_allow_html=True)

# --- Constants and live FX ---
def get_fx_rate():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD").json()
        return r['rates']['AUD']
    except:
        return 1.52  # fallback

USD_TO_AUD = get_fx_rate()

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Select Coin", ["BTC", "ETH", "LTC", "XRP", "ADA", "DOGE", "SHIB", "MATIC"])
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    exchanges = st.multiselect("Exchanges", ["Coinbase", "Crypto.com", "CoinSpot", "Kraken", "IndependentReserve"], default=["Coinbase", "Kraken", "CoinSpot"])

# --- API Fetchers ---
def fetch_coinbase():
    try:
        url = f"https://api.coinbase.com/v2/prices/{coin}-USD/spot"
        r = requests.get(url).json()
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

def fetch_coinspot():
    try:
        key = st.secrets["api_keys"]["coinspot_key"]
        secret = st.secrets["api_keys"]["coinspot_secret"]
        return {"buy": 1000, "sell": 1010, "fee": 0.01}  # Placeholder
    except:
        return None

def fetch_kraken():
    try:
        pair = f"X{coin}ZUSD" if coin == "BTC" else f"{coin}USD"
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={pair}").json()
        key = list(r["result"].keys())[0]
        data = r["result"][key]
        return {"buy": float(data["a"][0]) * USD_TO_AUD, "sell": float(data["b"][0]) * USD_TO_AUD, "fee": 0.0026}
    except:
        return None

def fetch_independent_reserve():
    try:
        url = f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD"
        r = requests.get(url).json()
        return {"buy": float(r["CurrentLowestOfferPrice"]), "sell": float(r["CurrentHighestBidPrice"]), "fee": 0.005}
    except:
        return None

fetchers = {
    "Coinbase": fetch_coinbase,
    "Crypto.com": fetch_crypto_com,
    "CoinSpot": fetch_coinspot,
    "Kraken": fetch_kraken,
    "IndependentReserve": fetch_independent_reserve
}

# --- Scan ---
data = {ex: fetchers[ex]() for ex in exchanges if fetchers[ex]() is not None}
valid = {ex: val for ex, val in data.items() if val}

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
    st.error("⚠️ Could not retrieve valid data from selected exchanges.")

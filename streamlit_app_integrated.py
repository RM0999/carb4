import streamlit as st
import requests
import time
import hmac
import hashlib
import json
from datetime import datetime


USD_TO_AUD = 1.52  # fallback in case FX API is not called

def fetch_coinspot(coin):
    try:
        key = st.secrets["api_keys"]["coinspot_api_key"]
        secret = st.secrets["api_keys"]["coinspot_api_secret"]
        nonce = str(int(time.time() * 1000))
        request_body = {"nonce": nonce}
        message = json.dumps(request_body).encode()
        signature = hmac.new(secret.encode(), message, hashlib.sha512).hexdigest()
        headers = {
            "Content-type": "application/json",
            "key": key,
            "sign": signature
        }
        r = requests.post("https://www.coinspot.com.au/api/quotes", headers=headers, data=message).json()
        ask = float(r[coin.lower()]["buy"])
        bid = float(r[coin.lower()]["sell"])
        return {"buy": ask, "sell": bid, "fee": 0.01}
    except:
        return None

def fetch_kraken(coin):
    try:
        pair = f"X{coin}ZUSD" if coin == "BTC" else f"{coin}USD"
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={pair}").json()
        key = list(r["result"].keys())[0]
        data = r["result"][key]
        ask = float(data["a"][0]) * USD_TO_AUD
        bid = float(data["b"][0]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.0026}
    except:
        return None

def fetch_coinbase(coin):
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{coin}-USD/spot").json()
        price = float(r["data"]["amount"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except:
        return None

def fetch_independent_reserve(coin):
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD").json()
        ask = float(r["CurrentLowestOfferPrice"])
        bid = float(r["CurrentHighestBidPrice"])
        return {"buy": ask, "sell": bid, "fee": 0.005}
    except:
        return None

def fetch_crypto_com(coin):
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={coin}_USDT").json()
        data = r["result"]["data"]
        ask = float(data["a"]) * USD_TO_AUD
        bid = float(data["b"]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.001}
    except:
        return None

st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔒 Secure Arbitrage Scanner</h1>", unsafe_allow_html=True)

# Live FX rate
def get_fx_rate():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD").json()
        return r["rates"]["AUD"]
    except:
        return 1.52

USD_TO_AUD = get_fx_rate()

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Select Coin", ["BTC", "ETH", "LTC", "XRP", "ADA", "DOGE", "SHIB", "MATIC"])
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    exchanges = st.multiselect("Exchanges", ["Coinbase", "Crypto.com", "CoinSpot", "Kraken", "IndependentReserve"],
                               default=["Coinbase", "Kraken", "CoinSpot", "Crypto.com", "IndependentReserve"])

fetchers = {
    "Coinbase": lambda: fetch_coinbase(coin),
    "Crypto.com": lambda: fetch_crypto_com(coin),
    "CoinSpot": lambda: fetch_coinspot(coin),
    "Kraken": lambda: fetch_kraken(coin),
    "IndependentReserve": lambda: fetch_independent_reserve(coin)
}

# --- Arbitrage Logic ---
data = {}
for ex in exchanges:
    result = fetchers[ex]()
    if result:
        data[ex] = result

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

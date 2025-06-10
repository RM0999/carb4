
import streamlit as st
import requests
from datetime import datetime

# Config
st.set_page_config(page_title="Accurate Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>📊 Accurate Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

# Sidebar UI
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Choose Crypto", ["BTC", "ETH", "LTC", "XRP", "ADA", "DOGE", "SHIB", "MATIC"])
    min_profit = st.slider("Minimum Profit (%)", 0.1, 10.0, 0.5)
    investment = st.number_input("Investment (AUD)", min_value=10.0, value=1000.0)

# Real-time FX rate
def fetch_fx_rate():
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=AUD").json()
        return r["rates"]["AUD"]
    except:
        return 1.52

USD_TO_AUD = fetch_fx_rate()

# Exchange symbol mapping
SYMBOLS = {
    "BTC": {"Binance": "BTCUSDT", "Kraken": "XBTUSDT", "Coinbase": "BTC-USD"},
    "ETH": {"Binance": "ETHUSDT", "Kraken": "ETHUSDT", "Coinbase": "ETH-USD"},
    "LTC": {"Binance": "LTCUSDT", "Kraken": "LTCUSDT", "Coinbase": "LTC-USD"},
    "XRP": {"Binance": "XRPUSDT", "Kraken": "XRPUSDT", "Coinbase": "XRP-USD"},
    "ADA": {"Binance": "ADAUSDT", "Kraken": "ADAUSDT", "Coinbase": "ADA-USD"},
    "DOGE": {"Binance": "DOGEUSDT", "Kraken": "DOGEUSDT", "Coinbase": "DOGE-USD"},
    "SHIB": {"Binance": "SHIBUSDT", "Kraken": "SHIBUSDT", "Coinbase": "SHIB-USD"},
    "MATIC": {"Binance": "MATICUSDT", "Kraken": "MATICUSDT", "Coinbase": "MATIC-USD"}
}

def fetch_binance(symbol):
    url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
    r = requests.get(url).json()
    return {"buy": float(r["askPrice"]) * USD_TO_AUD, "sell": float(r["bidPrice"]) * USD_TO_AUD, "fee": 0.001}

def fetch_kraken(symbol):
    symbol_map = {"XBT": "XXBTZUSD", "ETH": "XETHZUSD", "LTC": "XLTCZUSD", "XRP": "XXRPZUSD",
                  "ADA": "ADAUSD", "DOGE": "DOGEUSD", "SHIB": "SHIBUSD", "MATIC": "MATICUSD"}
    url = f"https://api.kraken.com/0/public/Ticker?pair={symbol}"
    r = requests.get(url).json()
    data = r["result"][symbol_map[symbol.replace('USDT', '').replace('XBT', 'XBT')]]
    return {"buy": float(data["a"][0]) * USD_TO_AUD, "sell": float(data["b"][0]) * USD_TO_AUD, "fee": 0.0026}

def fetch_coinbase(symbol):
    url = f"https://api.coinbase.com/v2/prices/{symbol}/buy"
    r_buy = requests.get(url).json()
    buy = float(r_buy["data"]["amount"])

    url = f"https://api.coinbase.com/v2/prices/{symbol}/sell"
    r_sell = requests.get(url).json()
    sell = float(r_sell["data"]["amount"])
    return {"buy": buy * USD_TO_AUD, "sell": sell * USD_TO_AUD, "fee": 0.005}

# Mapping fetchers
fetchers = {
    "Binance": lambda: fetch_binance(SYMBOLS[coin]["Binance"]),
    "Kraken": lambda: fetch_kraken(SYMBOLS[coin]["Kraken"]),
    "Coinbase": lambda: fetch_coinbase(SYMBOLS[coin]["Coinbase"]),
}

# Fetch all valid data
data = {ex: fetchers[ex]() for ex in fetchers if fetchers[ex]() is not None}

# Calculate arbitrage
if data:
    best_buy = min(data.items(), key=lambda x: x[1]["buy"])
    best_sell = max(data.items(), key=lambda x: x[1]["sell"])
    spread = best_sell[1]["sell"] - best_buy[1]["buy"]
    buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit_amt = spread - buy_fee - sell_fee
    net_profit_pct = round((net_profit_amt / best_buy[1]["buy"]) * 100, 2)
    est_profit = round(investment * net_profit_pct / 100, 2)
    timestamp = datetime.now().strftime("%H:%M:%S")

    if net_profit_pct >= min_profit:
        st.success(f"🚀 Arbitrage Opportunity Found at {timestamp}")
        st.write(f"🛒 Buy from: **{best_buy[0]}** at AUD ${best_buy[1]['buy']:.2f}")
        st.write(f"💰 Sell on: **{best_sell[0]}** at AUD ${best_sell[1]['sell']:.2f}")
        st.write(f"🔄 Spread: AUD ${spread:.2f}")
        st.write(f"💸 Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
        st.write(f"✅ Net Profit: **{net_profit_pct}%** | AUD ${est_profit:.2f}")
    else:
        st.warning("No profitable arbitrage opportunity found above your threshold.")
else:
    st.error("❌ No valid data retrieved.")


import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")

st.title("🔍 Live Crypto Arbitrage Scanner")

# Constants
USD_TO_AUD = 1.52
DEFAULT_INVESTMENT = 1000

# Supported coins and their symbols per exchange
SYMBOLS = {
    "BTC": {"Binance": "BTCUSDT", "Kraken": "XXBTZUSD", "Coinbase": "BTC-USD"},
    "ETH": {"Binance": "ETHUSDT", "Kraken": "XETHZUSD", "Coinbase": "ETH-USD"},
    "LTC": {"Binance": "LTCUSDT", "Kraken": "XLTCZUSD", "Coinbase": "LTC-USD"},
    "XRP": {"Binance": "XRPUSDT", "Kraken": "XXRPZUSD", "Coinbase": "XRP-USD"},
    "ADA": {"Binance": "ADAUSDT", "Kraken": "ADAUSD", "Coinbase": "ADA-USD"},
    "DOGE": {"Binance": "DOGEUSDT", "Kraken": "DOGEUSD", "Coinbase": "DOGE-USD"},
    "SHIB": {"Binance": "SHIBUSDT", "Kraken": "SHIBUSD", "Coinbase": "SHIB-USD"},
    "MATIC": {"Binance": "MATICUSDT", "Kraken": "MATICUSD", "Coinbase": "MATIC-USD"}
}

EXCHANGES = ["Binance", "Kraken", "Coinbase"]

# Sidebar controls
with st.sidebar:
    coin = st.selectbox("Select Crypto", list(SYMBOLS.keys()))
    min_profit = st.slider("Minimum Profit (%)", 0.1, 10.0, 0.5)
    investment = st.number_input("Investment (AUD)", min_value=10, value=DEFAULT_INVESTMENT)
    selected_exchanges = st.multiselect("Select Exchanges", EXCHANGES, default=EXCHANGES)

# API fetch functions
def fetch_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
        r = requests.get(url).json()
        return {
            "buy": float(r["askPrice"]) * USD_TO_AUD,
            "sell": float(r["bidPrice"]) * USD_TO_AUD,
            "fee": 0.001
        }
    except:
        return None

def fetch_kraken(symbol):
    try:
        url = f"https://api.kraken.com/0/public/Ticker?pair={symbol}"
        r = requests.get(url).json()
        result = list(r["result"].values())[0]
        return {
            "buy": float(result["a"][0]) * USD_TO_AUD,
            "sell": float(result["b"][0]) * USD_TO_AUD,
            "fee": 0.0026
        }
    except:
        return None

def fetch_coinbase(symbol):
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}/spot"
        r = requests.get(url).json()
        price = float(r["data"]["amount"])
        return {
            "buy": price * (1 + 0.005),
            "sell": price * (1 - 0.005),
            "fee": 0.005
        }
    except:
        return None

# Run scanner
if coin not in SYMBOLS:
    st.error("Selected coin is not supported.")
else:
    fetchers = {
        "Binance": lambda: fetch_binance(SYMBOLS[coin]["Binance"]),
        "Kraken": lambda: fetch_kraken(SYMBOLS[coin]["Kraken"]),
        "Coinbase": lambda: fetch_coinbase(SYMBOLS[coin]["Coinbase"]),
    }

    data = {ex: fetchers[ex]() for ex in selected_exchanges if fetchers[ex]() is not None}

    if len(data) < 2:
        st.warning("Not enough valid data for comparison.")
    else:
        best_buy = min(data.items(), key=lambda x: x[1]["buy"])
        best_sell = max(data.items(), key=lambda x: x[1]["sell"])

        spread = best_sell[1]["sell"] - best_buy[1]["buy"]
        spread_pct = (spread / best_buy[1]["buy"]) * 100

        buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
        sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]

        net_profit = spread - buy_fee - sell_fee
        net_profit_pct = (net_profit / best_buy[1]["buy"]) * 100
        net_profit_aud = investment * (net_profit_pct / 100)

        if net_profit_pct >= min_profit:
            st.success(f"🟢 Arbitrage Opportunity Found for {coin}")
            st.write(f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}")
            st.write(f"🛒 Buy from: **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
            st.write(f"💰 Sell on: **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
            st.write(f"🔄 Spread: AUD ${spread:.2f} ({spread_pct:.2f}%)")
            st.write(f"💸 Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
            st.write(f"📈 Net Profit: **{net_profit_pct:.2f}%** | **AUD ${net_profit_aud:.2f}**")
        else:
            st.warning("No profitable arbitrage opportunity found above your threshold.")

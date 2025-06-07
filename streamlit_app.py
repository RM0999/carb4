
import streamlit as st
import requests
from datetime import datetime

# Settings
USD_TO_AUD = 1.52  # Static fallback, consider live conversion later
COINS = {
    "BTC": {"symbol_binance": "BTCUSDT", "symbol_coinbase": "BTC-USD", "symbol_crypto": "BTC_USDT"},
    "ETH": {"symbol_binance": "ETHUSDT", "symbol_coinbase": "ETH-USD", "symbol_crypto": "ETH_USDT"},
    "LTC": {"symbol_binance": "LTCUSDT", "symbol_coinbase": "LTC-USD", "symbol_crypto": "LTC_USDT"},
    "XRP": {"symbol_binance": "XRPUSDT", "symbol_coinbase": "XRP-USD", "symbol_crypto": "XRP_USDT"},
    "ADA": {"symbol_binance": "ADAUSDT", "symbol_coinbase": "ADA-USD", "symbol_crypto": "ADA_USDT"},
    "DOGE": {"symbol_binance": "DOGEUSDT", "symbol_coinbase": "DOGE-USD", "symbol_crypto": "DOGE_USDT"},
    "SHIB": {"symbol_binance": "SHIBUSDT", "symbol_coinbase": "SHIB-USD", "symbol_crypto": "SHIB_USDT"},
    "MATIC": {"symbol_binance": "MATICUSDT", "symbol_coinbase": "MATIC-USD", "symbol_crypto": "MATIC_USDT"}
}

# Streamlit UI
st.set_page_config(page_title="Multi-Crypto Arbitrage Scanner", layout="wide")
st.title("💹 Multi-Crypto Arbitrage Scanner")

with st.sidebar:
    coin = st.selectbox("Select Cryptocurrency", list(COINS.keys()))
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    min_profit = st.slider("Minimum Profit %", 0.1, 5.0, 1.0)
    exchanges = st.multiselect("Select Exchanges", [
        "Binance", "Kraken", "CoinSpot", "IndependentReserve",
        "Coinbase", "CoinJar", "Crypto.com"
    ], default=["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase", "CoinJar", "Crypto.com"])

# API fetchers
def fetch_binance(symbol):  # USD
    url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
    try:
        r = requests.get(url).json()
        return {"buy": float(r["askPrice"]) * USD_TO_AUD, "sell": float(r["bidPrice"]) * USD_TO_AUD, "fee": 0.001}
    except: return None

def fetch_kraken(symbol):  # BTC, ETH, LTC only via USD
    map_symbol = symbol.replace("USDT", "USD").replace("BTC", "XBT")
    url = f"https://api.kraken.com/0/public/Ticker?pair={map_symbol}"
    try:
        r = requests.get(url).json()
        k = list(r["result"].keys())[0]
        return {"buy": float(r["result"][k]["a"][0]) * USD_TO_AUD, "sell": float(r["result"][k]["b"][0]) * USD_TO_AUD, "fee": 0.0026}
    except: return None

def fetch_coinspot(symbol):  # AUD
    url = "https://www.coinspot.com.au/pubapi/v2/latest"
    try:
        r = requests.get(url).json()
        sym = symbol.replace("USDT", "")
        return {"buy": float(r["prices"][sym]["ask"]), "sell": float(r["prices"][sym]["bid"]), "fee": 0.01}
    except: return None

def fetch_independent_reserve(symbol):  # BTC, ETH, LTC, XRP, ADA in AUD
    code = symbol.replace("USDT", "").capitalize()
    url = f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={code}&secondaryCurrencyCode=AUD"
    try:
        r = requests.get(url).json()
        return {"buy": float(r["CurrentLowestOfferPrice"]), "sell": float(r["CurrentHighestBidPrice"]), "fee": 0.005}
    except: return None

def fetch_coinbase(symbol):  # USD
    url = f"https://api.exchange.coinbase.com/products/{symbol}/ticker"
    try:
        r = requests.get(url).json()
        return {"buy": float(r["ask"]) * USD_TO_AUD, "sell": float(r["bid"]) * USD_TO_AUD, "fee": 0.006}
    except: return None

def fetch_coinjar(symbol):  # AUD
    url = "https://data.exchange.coinjar.com/products"
    try:
        r = requests.get(url).json()
        product = next(p for p in r if p["display_name"].startswith(symbol.replace("USDT", "") + "/AUD"))
        return {"buy": float(product["ask"]), "sell": float(product["bid"]), "fee": 0.01}
    except: return None

def fetch_cryptocom(symbol):  # USD
    url = f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}"
    try:
        r = requests.get(url).json()
        return {"buy": float(r["result"]["data"]["a"]) * USD_TO_AUD, "sell": float(r["result"]["data"]["b"]) * USD_TO_AUD, "fee": 0.003}
    except: return None

fetchers = {
    "Binance": lambda: fetch_binance(COINS[coin]["symbol_binance"]),
    "Kraken": lambda: fetch_kraken(COINS[coin]["symbol_binance"]),
    "CoinSpot": lambda: fetch_coinspot(COINS[coin]["symbol_binance"]),
    "IndependentReserve": lambda: fetch_independent_reserve(COINS[coin]["symbol_binance"]),
    "Coinbase": lambda: fetch_coinbase(COINS[coin]["symbol_coinbase"]),
    "CoinJar": lambda: fetch_coinjar(COINS[coin]["symbol_binance"]),
    "Crypto.com": lambda: fetch_cryptocom(COINS[coin]["symbol_crypto"]),
}

results = {ex: fetchers[ex]() for ex in exchanges if fetchers[ex]()}
valid = {k: v for k, v in results.items() if v}

if valid:
    best_buy = min(valid.items(), key=lambda x: x[1]['buy'])
    best_sell = max(valid.items(), key=lambda x: x[1]['sell'])
    spread = round(best_sell[1]["sell"] - best_buy[1]["buy"], 2)
    profit_pct = round((spread) / best_buy[1]["buy"] * 100, 2)
    net_profit = round(investment * (profit_pct / 100), 2)

    if profit_pct >= min_profit:
        st.success(f"🟢 Opportunity Found for {coin}!")
        st.write(f"🛒 Buy from: **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
        st.write(f"💰 Sell on: **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
        st.write(f"🔄 Spread: AUD ${spread:.2f} ({profit_pct}%)")
        st.write(f"💸 Net Profit: **AUD ${net_profit:.2f}**")
        st.caption(f"Fees: Buy Fee = AUD ${round(best_buy[1]['buy'] * best_buy[1]['fee'], 2)}, "
                   f"Sell Fee = AUD ${round(best_sell[1]['sell'] * best_sell[1]['fee'], 2)}")
    else:
        st.warning(f"No arbitrage opportunity above {min_profit}% for {coin}.")
else:
    st.error("❌ No valid data retrieved from selected exchanges.")

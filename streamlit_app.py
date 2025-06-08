
import streamlit as st
import requests
from datetime import datetime

# Fixed AUD conversion rate (for simplicity)
USD_TO_AUD = 1.52

# Supported coins and their exchange symbols
COINS = {
    "BTC": {
        "symbol_binance": "BTCUSDT",
        "symbol_kraken": "XBTUSDT",
        "symbol_coinspot": "BTC",
        "symbol_independent": "Xbt",
        "symbol_coinbase": "BTC-USD",
        "symbol_coinjar": "BTC",
        "symbol_crypto": "BTC_USDT",
    },
    "ETH": {
        "symbol_binance": "ETHUSDT",
        "symbol_kraken": "ETHUSDT",
        "symbol_coinspot": "ETH",
        "symbol_independent": "Eth",
        "symbol_coinbase": "ETH-USD",
        "symbol_coinjar": "ETH",
        "symbol_crypto": "ETH_USDT",
    },
    "LTC": {
        "symbol_binance": "LTCUSDT",
        "symbol_kraken": "LTCUSDT",
        "symbol_coinspot": "LTC",
        "symbol_independent": "Ltc",
        "symbol_coinbase": "LTC-USD",
        "symbol_coinjar": "LTC",
        "symbol_crypto": "LTC_USDT",
    },
    "ADA": {
        "symbol_binance": "ADAUSDT",
        "symbol_kraken": "ADAUSDT",
        "symbol_coinspot": "ADA",
        "symbol_independent": "Ada",
        "symbol_coinbase": "ADA-USD",
        "symbol_coinjar": "ADA",
        "symbol_crypto": "ADA_USDT",
    },
    "XRP": {
        "symbol_binance": "XRPUSDT",
        "symbol_kraken": "XRPUSDT",
        "symbol_coinspot": "XRP",
        "symbol_independent": "Xrp",
        "symbol_coinbase": "XRP-USD",
        "symbol_coinjar": "XRP",
        "symbol_crypto": "XRP_USDT",
    }
}

st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>💱 Live Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Select Coin", list(COINS.keys()))
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 10.0, 0.5)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    selected_exchanges = st.multiselect("Exchanges", ["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase", "CoinJar", "Crypto.com"],
                                        default=["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase"])

# API Fetchers
def fetch_binance(symbol):  # USDT
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}").json()
        return {"buy": float(r["askPrice"]) * USD_TO_AUD, "sell": float(r["bidPrice"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

def fetch_kraken(symbol):  # USD
    try:
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={symbol}").json()
        key = list(r["result"].keys())[0]
        data = r["result"][key]
        return {"buy": float(data["a"][0]) * USD_TO_AUD, "sell": float(data["b"][0]) * USD_TO_AUD, "fee": 0.0026}
    except:
        return None

def fetch_coinspot(symbol):  # AUD
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        ask = float(r['prices'][symbol]['ask'])
        bid = float(r['prices'][symbol]['bid'])
        return {'buy': ask, 'sell': bid, 'fee': 0.01}
    except:
        return None

def fetch_independent(symbol):  # AUD
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={symbol}&secondaryCurrencyCode=Aud").json()
        return {'buy': float(r['CurrentLowestOfferPrice']), 'sell': float(r['CurrentHighestBidPrice']), 'fee': 0.005}
    except:
        return None

def fetch_coinbase(symbol):  # USD
    try:
        r = requests.get(f"https://api.exchange.coinbase.com/products/{symbol}/book?level=1").json()
        return {'buy': float(r["asks"][0][0]) * USD_TO_AUD, 'sell': float(r["bids"][0][0]) * USD_TO_AUD, 'fee': 0.006}
    except:
        return None

def fetch_coinjar(symbol):  # AUD
    try:
        r = requests.get("https://data.exchange.coinjar.com/products").json()
        for item in r:
            if item['currency_pair'].startswith(symbol.lower()):
                return {'buy': float(item['ask']), 'sell': float(item['bid']), 'fee': 0.005}
        return None
    except:
        return None

def fetch_crypto(symbol):  # USDT
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}").json()
        data = r["result"]["data"]
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

# Map exchange to its fetcher
fetchers = {
    "Binance": lambda: fetch_binance(COINS[coin]["symbol_binance"]),
    "Kraken": lambda: fetch_kraken(COINS[coin]["symbol_kraken"]),
    "CoinSpot": lambda: fetch_coinspot(COINS[coin]["symbol_coinspot"]),
    "IndependentReserve": lambda: fetch_independent(COINS[coin]["symbol_independent"]),
    "Coinbase": lambda: fetch_coinbase(COINS[coin]["symbol_coinbase"]),
    "CoinJar": lambda: fetch_coinjar(COINS[coin]["symbol_coinjar"]),
    "Crypto.com": lambda: fetch_crypto(COINS[coin]["symbol_crypto"]),
}

# Run
results = {ex: fetchers[ex]() for ex in selected_exchanges if fetchers[ex]() is not None}
valid = {ex: val for ex, val in results.items() if val.get("buy") > 0 and val.get("sell") > 0}

if valid:
    best_buy = min(valid.items(), key=lambda x: x[1]["buy"])
    best_sell = max(valid.items(), key=lambda x: x[1]["sell"])
    spread_value = best_sell[1]["sell"] - best_buy[1]["buy"]
    spread_pct = round((spread_value / best_buy[1]["buy"]) * 100, 2)
    buy_fee = investment * best_buy[1]["fee"]
    sell_fee = investment * best_sell[1]["fee"]
    net_profit_value = investment * ((best_sell[1]["sell"] - best_buy[1]["buy"]) / best_buy[1]["buy"]) - (buy_fee + sell_fee)
    net_profit_pct = round((net_profit_value / investment) * 100, 2)

    if net_profit_pct >= min_profit:
        st.success(f"🕒 {datetime.now().strftime('%H:%M:%S')} — {coin}")
        st.write(f"🛒 Buy from: **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
        st.write(f"💰 Sell on: **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
        st.write(f"🔄 Spread: AUD ${spread_value:.2f} ({spread_pct}%)")
        st.write(f"💸 Net Profit: {net_profit_pct}% | **AUD ${net_profit_value:.2f}**")
        st.caption(f"Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
    else:
        st.warning("No arbitrage opportunity above minimum net profit threshold.")
else:
    st.error("⚠️ No valid market data returned from selected exchanges.")


import streamlit as st
import requests
from datetime import datetime

# Supported coins and their symbols per exchange
COINS = {
    "BTC": {
        "symbol_binance": "BTCUSDT",
        "symbol_kraken": "XBTUSDT",
        "symbol_coinspot": "BTC",
        "symbol_independentreserve": "Xbt",
        "symbol_coinbase": "BTC-USD",
        "symbol_coinjar": "btc",
        "symbol_crypto": "BTC_USDT",
        "symbol_okx": "BTC-USDT",
        "symbol_kucoin": "BTC-USDT",
        "symbol_bybit": "BTCUSDT"
    },
    "ETH": {
        "symbol_binance": "ETHUSDT",
        "symbol_kraken": "ETHUSDT",
        "symbol_coinspot": "ETH",
        "symbol_independentreserve": "Eth",
        "symbol_coinbase": "ETH-USD",
        "symbol_coinjar": "eth",
        "symbol_crypto": "ETH_USDT",
        "symbol_okx": "ETH-USDT",
        "symbol_kucoin": "ETH-USDT",
        "symbol_bybit": "ETHUSDT"
    },
    "LTC": {
        "symbol_binance": "LTCUSDT",
        "symbol_kraken": "LTCUSDT",
        "symbol_coinspot": "LTC",
        "symbol_independentreserve": "Ltc",
        "symbol_coinbase": "LTC-USD",
        "symbol_coinjar": "ltc",
        "symbol_crypto": "LTC_USDT",
        "symbol_okx": "LTC-USDT",
        "symbol_kucoin": "LTC-USDT",
        "symbol_bybit": "LTCUSDT"
    },
    "ADA": {
        "symbol_binance": "ADAUSDT",
        "symbol_kraken": "ADAUSDT",
        "symbol_coinspot": "ADA",
        "symbol_independentreserve": "Ada",
        "symbol_coinbase": "ADA-USD",
        "symbol_coinjar": "ada",
        "symbol_crypto": "ADA_USDT",
        "symbol_okx": "ADA-USDT",
        "symbol_kucoin": "ADA-USDT",
        "symbol_bybit": "ADAUSDT"
    },
    "XRP": {
        "symbol_binance": "XRPUSDT",
        "symbol_kraken": "XRPUSDT",
        "symbol_coinspot": "XRP",
        "symbol_independentreserve": "Xrp",
        "symbol_coinbase": "XRP-USD",
        "symbol_coinjar": "xrp",
        "symbol_crypto": "XRP_USDT",
        "symbol_okx": "XRP-USDT",
        "symbol_kucoin": "XRP-USDT",
        "symbol_bybit": "XRPUSDT"
    }
}

USD_TO_AUD = 1.52

# App layout
st.set_page_config(page_title="Arbitrage Scanner", layout="wide")
st.title("💹 Crypto Arbitrage Scanner")
st.sidebar.title("⚙️ Settings")
coin = st.sidebar.selectbox("Select Coin", list(COINS.keys()), index=0)
min_profit = st.sidebar.slider("Minimum Net Profit (%)", 0.1, 10.0, 1.0)
investment = st.sidebar.number_input("Investment Amount (AUD)", min_value=10, value=1000)
exchanges = st.sidebar.multiselect("Exchanges", list(COINS[coin].keys()), default=list(COINS[coin].keys()))

# Fetch functions
def fetch_binance(symbol): return fetch_usdt_price(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}")
def fetch_kraken(symbol): return fetch_kraken_price("https://api.kraken.com/0/public/Ticker?pair=" + symbol)
def fetch_coinspot(symbol): return fetch_au_price("https://www.coinspot.com.au/pubapi/v2/latest", symbol)
def fetch_independentreserve(symbol): return fetch_ir_price(symbol)
def fetch_coinbase(symbol): return fetch_cb_price("https://api.exchange.coinbase.com/products/" + symbol + "/ticker")
def fetch_coinjar(symbol): return fetch_cj_price(symbol)
def fetch_crypto(symbol): return fetch_crypto_price("https://api.crypto.com/v2/public/get-ticker?instrument_name=" + symbol)
def fetch_okx(symbol): return fetch_usdt_price("https://www.okx.com/api/v5/market/ticker?instId=" + symbol)
def fetch_kucoin(symbol): return fetch_usdt_price("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=" + symbol)
def fetch_bybit(symbol): return fetch_bybit_price("https://api.bybit.com/v2/public/tickers?symbol=" + symbol)

# Helpers
def fetch_usdt_price(url):
    try:
        r = requests.get(url).json()
        ask, bid = float(r.get("askPrice", r.get("data", {}).get("askPrice", 0))), float(r.get("bidPrice", r.get("data", {}).get("bidPrice", 0)))
        return {"buy": ask * USD_TO_AUD, "sell": bid * USD_TO_AUD, "fee": 0.001}
    except: return None

def fetch_kraken_price(url):
    try:
        r = requests.get(url).json()
        key = list(r["result"].keys())[0]
        return {"buy": float(r["result"][key]["a"][0]) * USD_TO_AUD, "sell": float(r["result"][key]["b"][0]) * USD_TO_AUD, "fee": 0.0026}
    except: return None

def fetch_au_price(url, symbol):
    try:
        r = requests.get(url).json()
        return {"buy": float(r['prices'][symbol]['ask']), "sell": float(r['prices'][symbol]['bid']), "fee": 0.01}
    except: return None

def fetch_ir_price(symbol):
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={symbol}&secondaryCurrencyCode=Aud").json()
        return {"buy": float(r["CurrentLowestOfferPrice"]), "sell": float(r["CurrentHighestBidPrice"]), "fee": 0.005}
    except: return None

def fetch_cb_price(url):
    try:
        r = requests.get(url).json()
        return {"buy": float(r["ask"]) * USD_TO_AUD, "sell": float(r["bid"]) * USD_TO_AUD, "fee": 0.005}
    except: return None

def fetch_cj_price(symbol):
    try:
        r = requests.get("https://data.exchange.coinjar.com/products/" + symbol + "_aud/ticker").json()
        return {"buy": float(r["ask"]), "sell": float(r["bid"]), "fee": 0.01}
    except: return None

def fetch_crypto_price(url):
    try:
        r = requests.get(url).json()
        data = r.get("result", {}).get("data", {})
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.001}
    except: return None

def fetch_bybit_price(url):
    try:
        r = requests.get(url).json()
        data = r["result"][0]
        return {"buy": float(data["ask_price"]) * USD_TO_AUD, "sell": float(data["bid_price"]) * USD_TO_AUD, "fee": 0.001}
    except: return None

# Mapping fetchers
fetchers = {
    "symbol_binance": fetch_binance,
    "symbol_kraken": fetch_kraken,
    "symbol_coinspot": fetch_coinspot,
    "symbol_independentreserve": fetch_independentreserve,
    "symbol_coinbase": fetch_coinbase,
    "symbol_coinjar": fetch_coinjar,
    "symbol_crypto": fetch_crypto,
    "symbol_okx": fetch_okx,
    "symbol_kucoin": fetch_kucoin,
    "symbol_bybit": fetch_bybit
}

# Run scan
results = {}
for exchange_key in exchanges:
    symbol = COINS[coin].get(exchange_key)
    fetch_func = fetchers.get(exchange_key)
    if symbol and fetch_func:
        result = fetch_func(symbol)
        if result: results[exchange_key] = result

if results:
    best_buy = min(results.items(), key=lambda x: x[1]["buy"])
    best_sell = max(results.items(), key=lambda x: x[1]["sell"])
    spread = best_sell[1]["sell"] - best_buy[1]["buy"]
    buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit_value = spread - buy_fee - sell_fee
    net_profit_pct = round((net_profit_value / best_buy[1]["buy"]) * 100, 2)
    net_profit_aud = round((net_profit_pct / 100) * investment, 2)
    
    if net_profit_pct >= min_profit:
        st.success(f"🚀 Arbitrage Opportunity")
        st.write(f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"🛒 Buy from: {best_buy[0]} at AUD ${best_buy[1]['buy']:.2f}")
        st.write(f"💰 Sell on: {best_sell[0]} at AUD ${best_sell[1]['sell']:.2f}")
        st.write(f"🔄 Spread: AUD ${spread:.2f} ({(spread / best_buy[1]['buy']) * 100:.2f}%)")
        st.write(f"💸 Net Profit: {net_profit_pct}% | AUD ${net_profit_aud}")
        st.caption(f"Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
    else:
        st.warning("No arbitrage opportunity above minimum net profit threshold.")
else:
    st.error("No data available from selected exchanges.")


import streamlit as st
import requests
from datetime import datetime

# Currency conversion (static fallback for USD to AUD)
USD_TO_AUD = 1.52

# Supported coins and their symbols on each exchange
COINS = {
    "BTC": {"binance": "BTCUSDT", "kraken": "XBTUSD", "crypto": "BTC_USDT", "okx": "BTC-USDT", "kucoin": "BTC-USDT", "bybit": "BTCUSDT", "coinbase": "BTC-USD", "coinjar": "btc", "coinspot": "BTC", "indres": "Xbt"},
    "ETH": {"binance": "ETHUSDT", "kraken": "ETHUSD", "crypto": "ETH_USDT", "okx": "ETH-USDT", "kucoin": "ETH-USDT", "bybit": "ETHUSDT", "coinbase": "ETH-USD", "coinjar": "eth", "coinspot": "ETH", "indres": "Eth"},
    "LTC": {"binance": "LTCUSDT", "kraken": "LTCUSD", "crypto": "LTC_USDT", "okx": "LTC-USDT", "kucoin": "LTC-USDT", "bybit": "LTCUSDT", "coinbase": "LTC-USD", "coinjar": "ltc", "coinspot": "LTC", "indres": "Ltc"},
    "ADA": {"binance": "ADAUSDT", "kraken": "ADAUSD", "crypto": "ADA_USDT", "okx": "ADA-USDT", "kucoin": "ADA-USDT", "bybit": "ADAUSDT", "coinbase": "ADA-USD", "coinjar": "ada", "coinspot": "ADA", "indres": "Ada"},
    "XRP": {"binance": "XRPUSDT", "kraken": "XRPUSD", "crypto": "XRP_USDT", "okx": "XRP-USDT", "kucoin": "XRP-USDT", "bybit": "XRPUSDT", "coinbase": "XRP-USD", "coinjar": "xrp", "coinspot": "XRP", "indres": "Xrp"}
}

# Streamlit UI setup
st.set_page_config(page_title="🔍 Full Crypto Arbitrage Scanner", layout="wide")
st.title("🔁 Full Crypto Arbitrage Scanner with 10 Live Exchanges")

with st.sidebar:
    coin = st.selectbox("Select Coin", list(COINS.keys()))
    min_profit = st.slider("Minimum Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment Amount (AUD)", value=1000)
    exchanges = st.multiselect("Select Exchanges", list(COINS[coin].keys()), default=list(COINS[coin].keys()))

# Define API fetch functions
def fetch_binance(symbol):  # USDT
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}").json()
        return {"buy": float(r["askPrice"]) * USD_TO_AUD, "sell": float(r["bidPrice"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

def fetch_kraken(symbol):  # USD
    try:
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={symbol}").json()
        data = next(iter(r["result"].values()))
        return {"buy": float(data["a"][0]) * USD_TO_AUD, "sell": float(data["b"][0]) * USD_TO_AUD, "fee": 0.0026}
    except:
        return None

def fetch_coinspot(symbol):  # AUD
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        data = r["prices"][symbol]
        return {"buy": float(data["ask"]), "sell": float(data["bid"]), "fee": 0.01}
    except:
        return None

def fetch_indres(symbol):  # AUD
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={symbol}&secondaryCurrencyCode=Aud").json()
        return {"buy": float(r["CurrentLowestOfferPrice"]), "sell": float(r["CurrentHighestBidPrice"]), "fee": 0.005}
    except:
        return None

def fetch_coinbase(symbol):  # USD
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{symbol}/spot").json()
        price = float(r["data"]["amount"])
        return {"buy": price * USD_TO_AUD, "sell": price * USD_TO_AUD, "fee": 0.005}
    except:
        return None

def fetch_coinjar(symbol):  # AUD
    try:
        r = requests.get(f"https://data.exchange.coinjar.com/products/{symbol}/aud/ticker").json()
        return {"buy": float(r["ask"]), "sell": float(r["bid"]), "fee": 0.01}
    except:
        return None

def fetch_crypto(symbol):  # USDT
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}").json()
        data = r["result"]["data"]
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

def fetch_okx(symbol):  # USDT
    try:
        r = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={symbol}").json()
        data = r["data"][0]
        return {"buy": float(data["askPx"]) * USD_TO_AUD, "sell": float(data["bidPx"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

def fetch_kucoin(symbol):  # USDT
    try:
        r = requests.get(f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}").json()
        data = r["data"]
        return {"buy": float(data["askPrice"]) * USD_TO_AUD, "sell": float(data["bidPrice"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

def fetch_bybit(symbol):  # USDT
    try:
        r = requests.get(f"https://api.bybit.com/v2/public/tickers?symbol={symbol}").json()
        data = r["result"][0]
        return {"buy": float(data["ask_price"]) * USD_TO_AUD, "sell": float(data["bid_price"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

# Mapping of exchanges to fetchers
fetchers = {
    "binance": fetch_binance,
    "kraken": fetch_kraken,
    "coinspot": fetch_coinspot,
    "indres": fetch_indres,
    "coinbase": fetch_coinbase,
    "coinjar": fetch_coinjar,
    "crypto": fetch_crypto,
    "okx": fetch_okx,
    "kucoin": fetch_kucoin,
    "bybit": fetch_bybit
}

# Run fetch and show best arbitrage opportunity
results = {ex: fetchers[ex](COINS[coin][ex]) for ex in exchanges if fetchers[ex](COINS[coin][ex])}
valid = {ex: res for ex, res in results.items() if res}

if valid:
    best_buy = min(valid.items(), key=lambda x: x[1]['buy'])
    best_sell = max(valid.items(), key=lambda x: x[1]['sell'])
    spread = best_sell[1]["sell"] - best_buy[1]["buy"]
    profit_pct = round((spread / best_buy[1]["buy"]) * 100, 2)
    buy_fee = round(best_buy[1]["buy"] * best_buy[1]["fee"], 2)
    sell_fee = round(best_sell[1]["sell"] * best_sell[1]["fee"], 2)
    net_profit = investment * (profit_pct / 100) - buy_fee - sell_fee

    if profit_pct >= min_profit:
        st.success(f"🕒 {datetime.now().strftime('%H:%M:%S')} — Arbitrage Found!")
        st.write(f"🛒 Buy from: **{best_buy[0].title()}** at AUD ${best_buy[1]['buy']:.2f}")
        st.write(f"💰 Sell on: **{best_sell[0].title()}** at AUD ${best_sell[1]['sell']:.2f}")
        st.write(f"🔄 Spread: AUD ${spread:.2f} ({profit_pct}%)")
        st.write(f"💸 Fees: Buy Fee = AUD ${buy_fee}, Sell Fee = AUD ${sell_fee}")
        st.write(f"✅ Net Profit: AUD ${net_profit:.2f}")
    else:
        st.warning("No arbitrage opportunity above minimum net profit threshold.")
else:
    st.error("No valid data from selected exchanges.")

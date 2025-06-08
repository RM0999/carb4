
import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Live Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>💱 Live Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

USD_TO_AUD = 1.52  # fallback conversion rate

COINS = {
    "BTC": {"symbol_binance": "BTCUSDT"},
    "ETH": {"symbol_binance": "ETHUSDT"},
    "LTC": {"symbol_binance": "LTCUSDT"},
    "ADA": {"symbol_binance": "ADAUSDT"},
    "XRP": {"symbol_binance": "XRPUSDT"}
}

EXCHANGES = ["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase", "CoinJar", "Crypto.com", "OKX", "KuCoin", "Bybit"]

# Sidebar
with st.sidebar:
    st.title("⚙️ Scanner Settings")
    coin = st.selectbox("Select Coin", list(COINS.keys()), index=0)
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    selected_exchanges = st.multiselect("Exchanges", EXCHANGES, default=EXCHANGES)

# Fetch functions
def fetch_binance(symbol):  # USD
    r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}").json()
    return {"buy": float(r["askPrice"]) * USD_TO_AUD, "sell": float(r["bidPrice"]) * USD_TO_AUD, "fee": 0.001}

def fetch_kraken(symbol):  # USD
    kraken_symbol = {"BTC": "XXBTZUSD", "ETH": "XETHZUSD", "LTC": "XLTCZUSD", "ADA": "ADAUSD", "XRP": "XXRPZUSD"}[symbol]
    r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={symbol}USD").json()
    d = r["result"][kraken_symbol]
    return {"buy": float(d["a"][0]) * USD_TO_AUD, "sell": float(d["b"][0]) * USD_TO_AUD, "fee": 0.0026}

def fetch_coinspot(symbol):  # AUD
    r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
    d = r["prices"][symbol]
    return {"buy": float(d["ask"]), "sell": float(d["bid"]), "fee": 0.01}

def fetch_independent_reserve(symbol):  # AUD
    r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={symbol}&secondaryCurrencyCode=AUD").json()
    return {"buy": float(r["CurrentLowestOfferPrice"]), "sell": float(r["CurrentHighestBidPrice"]), "fee": 0.005}

def fetch_coinbase(symbol):  # USD
    r = requests.get(f"https://api.pro.coinbase.com/products/{symbol}-USD/ticker").json()
    return {"buy": float(r["ask"]) * USD_TO_AUD, "sell": float(r["bid"]) * USD_TO_AUD, "fee": 0.005}

def fetch_coinjar(symbol):  # AUD
    r = requests.get(f"https://data.exchange.coinjar.com/products/{symbol}AUD/ticker").json()
    return {"buy": float(r["ask"]), "sell": float(r["bid"]), "fee": 0.01}

def fetch_crypto_com(symbol):  # USDT
    r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT").json()
    d = r["result"]["data"]
    return {"buy": float(d["a"]) * USD_TO_AUD, "sell": float(d["b"]) * USD_TO_AUD, "fee": 0.004}

def fetch_okx(symbol):  # USDT
    r = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT").json()
    d = r["data"][0]
    return {"buy": float(d["askPx"]) * USD_TO_AUD, "sell": float(d["bidPx"]) * USD_TO_AUD, "fee": 0.0015}

def fetch_kucoin(symbol):  # USDT
    r = requests.get(f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT").json()
    d = r["data"]
    return {"buy": float(d["ask"]) * USD_TO_AUD, "sell": float(d["bid"]) * USD_TO_AUD, "fee": 0.001}

def fetch_bybit(symbol):  # USDT
    r = requests.get(f"https://api.bybit.com/v2/public/tickers?symbol={symbol}USDT").json()
    d = r["result"][0]
    return {"buy": float(d["ask_price"]) * USD_TO_AUD, "sell": float(d["bid_price"]) * USD_TO_AUD, "fee": 0.001}

fetchers = {
    "Binance": lambda: fetch_binance(COINS[coin]["symbol_binance"]),
    "Kraken": lambda: fetch_kraken(coin),
    "CoinSpot": lambda: fetch_coinspot(coin),
    "IndependentReserve": lambda: fetch_independent_reserve(coin),
    "Coinbase": lambda: fetch_coinbase(coin),
    "CoinJar": lambda: fetch_coinjar(coin),
    "Crypto.com": lambda: fetch_crypto_com(coin),
    "OKX": lambda: fetch_okx(coin),
    "KuCoin": lambda: fetch_kucoin(coin),
    "Bybit": lambda: fetch_bybit(coin)
}

# Run fetch
results = {ex: fetchers[ex]() for ex in selected_exchanges if ex in fetchers}
valid_results = {ex: data for ex, data in results.items() if data}

if valid_results:
    best_buy = min(valid_results.items(), key=lambda x: x[1]["buy"])
    best_sell = max(valid_results.items(), key=lambda x: x[1]["sell"])

    spread = best_sell[1]["sell"] - best_buy[1]["buy"]
    gross_pct = round((spread / best_buy[1]["buy"]) * 100, 2)

    buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit = investment * ((spread - buy_fee - sell_fee) / best_buy[1]["buy"])
    net_pct = round((net_profit / investment) * 100, 2)

    st.subheader(f"📈 Opportunity for {coin}/AUD")
    if net_pct >= min_profit:
        st.success(f"🛒 Buy from: {best_buy[0]} at AUD ${best_buy[1]['buy']:.2f}")
        st.success(f"💰 Sell on: {best_sell[0]} at AUD ${best_sell[1]['sell']:.2f}")
        st.info(f"🔄 Spread: AUD ${spread:.2f} ({gross_pct}%)")
        st.info(f"💸 Net Profit: {net_pct}% | AUD ${net_profit:.2f}")
        st.caption(f"Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
    else:
        st.warning("No arbitrage opportunity above minimum net profit threshold.")
else:
    st.error("No valid data returned from selected exchanges.")

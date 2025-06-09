
import streamlit as st
import asyncio
import requests
from datetime import datetime

st.set_page_config(page_title="Hybrid Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>Hybrid WebSocket/REST Arbitrage Scanner</h1>", unsafe_allow_html=True)

USD_TO_AUD = 1.52
COINS = {
    "BTC": {"symbol_binance": "btcusdt"},
    "ETH": {"symbol_binance": "ethusdt"},
    "LTC": {"symbol_binance": "ltcusdt"},
    "XRP": {"symbol_binance": "xrpusdt"},
    "ADA": {"symbol_binance": "adausdt"},
    "DOGE": {"symbol_binance": "dogeusdt"},
    "SHIB": {"symbol_binance": "shibusdt"},
    "MATIC": {"symbol_binance": "maticusdt"}
}

with st.sidebar:
    st.title("Settings")
    coin = st.selectbox("Select Coin", list(COINS.keys()))
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 10.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    selected_exchanges = st.multiselect(
        "Exchanges",
        ["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Crypto.com", "Coinbase", "CoinJar"],
        default=["Binance", "Kraken", "Crypto.com", "CoinSpot"]
    )

def fetch_binance(symbol):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol.upper()}").json()
        return {
            'buy': float(r['askPrice']) * USD_TO_AUD,
            'sell': float(r['bidPrice']) * USD_TO_AUD,
            'fee': 0.001
        }
    except:
        return None

def fetch_kraken():
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDT").json()
        data = r["result"]["XXBTZUSD"]
        ask = float(data["a"][0])
        bid = float(data["b"][0])
        return {'buy': ask * USD_TO_AUD, 'sell': bid * USD_TO_AUD, 'fee': 0.0026}
    except:
        return None

def fetch_coinspot():
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        ask = float(r['prices']['BTC']['ask'])
        bid = float(r['prices']['BTC']['bid'])
        return {'buy': ask, 'sell': bid, 'fee': 0.01}
    except:
        return None

def fetch_independent_reserve():
    try:
        r = requests.get("https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode=Xbt&secondaryCurrencyCode=Aud").json()
        ask = float(r['CurrentLowestOfferPrice'])
        bid = float(r['CurrentHighestBidPrice'])
        return {'buy': ask, 'sell': bid, 'fee': 0.005}
    except:
        return None

def fetch_crypto_com():
    try:
        r = requests.get("https://api.crypto.com/v2/public/get-ticker?instrument_name=BTC_USDT").json()
        data = r['result']['data']
        return {'buy': float(data['a']) * USD_TO_AUD, 'sell': float(data['b']) * USD_TO_AUD, 'fee': 0.001}
    except:
        return None

def fetch_coinbase():
    try:
        r = requests.get("https://api.pro.coinbase.com/products/BTC-USD/ticker").json()
        return {
            'buy': float(r['ask']) * USD_TO_AUD,
            'sell': float(r['bid']) * USD_TO_AUD,
            'fee': 0.005
        }
    except:
        return None

def fetch_coinjar():
    try:
        r = requests.get("https://data.exchange.coinjar.com/products/BTC/AUD/ticker").json()
        return {
            'buy': float(r['ask']),
            'sell': float(r['bid']),
            'fee': 0.01
        }
    except:
        return None

fetchers = {
    "Binance": lambda: fetch_binance(COINS[coin]["symbol_binance"]),
    "Kraken": fetch_kraken,
    "CoinSpot": fetch_coinspot,
    "IndependentReserve": fetch_independent_reserve,
    "Crypto.com": fetch_crypto_com,
    "Coinbase": fetch_coinbase,
    "CoinJar": fetch_coinjar
}

placeholder = st.empty()
with placeholder.container():
    st.subheader(f"Scanning Arbitrage for {coin}")
    results = {ex: fetchers[ex]() for ex in selected_exchanges if fetchers[ex]()}

    if not results:
        st.error("No valid price data available.")
    else:
        best_buy = min(results.items(), key=lambda x: x[1]['buy'])
        best_sell = max(results.items(), key=lambda x: x[1]['sell'])
        spread = best_sell[1]['sell'] - best_buy[1]['buy']
        spread_pct = round((spread / best_buy[1]['buy']) * 100, 2)
        buy_fee = best_buy[1]['fee'] * investment
        sell_fee = best_sell[1]['fee'] * investment
        net_profit = investment * ((spread_pct - best_buy[1]['fee']*100 - best_sell[1]['fee']*100) / 100)

        if spread_pct > min_profit:
            st.success(f"Buy from: {best_buy[0]} at AUD ${best_buy[1]['buy']:.2f}")
            st.write(f"Sell on: {best_sell[0]} at AUD ${best_sell[1]['sell']:.2f}")
            st.write(f"Spread: AUD ${spread:.2f} ({spread_pct}%)")
            st.write(f"Net Profit: AUD ${net_profit:.2f}")
            st.write(f"Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
        else:
            st.info("No profitable arbitrage opportunity found above your threshold.")


import streamlit as st
import requests
from datetime import datetime

# Exchange and fee configuration
USD_TO_AUD = 1.52
EXCHANGES = ["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase", "CoinJar", "Crypto.com"]
COINS = {
    "BTC": {"symbol_binance": "BTCUSDT", "symbol_kraken": "XBTUSD", "symbol_crypto": "BTC_USDT"},
    "ETH": {"symbol_binance": "ETHUSDT", "symbol_kraken": "ETHUSD", "symbol_crypto": "ETH_USDT"},
    "LTC": {"symbol_binance": "LTCUSDT", "symbol_kraken": "LTCUSD", "symbol_crypto": "LTC_USDT"},
    "XRP": {"symbol_binance": "XRPUSDT", "symbol_kraken": "XRPUSD", "symbol_crypto": "XRP_USDT"},
    "ADA": {"symbol_binance": "ADAUSDT", "symbol_kraken": "ADAUSD", "symbol_crypto": "ADA_USDT"},
    "DOGE": {"symbol_binance": "DOGEUSDT", "symbol_kraken": "XDGUSD", "symbol_crypto": "DOGE_USDT"},
    "SHIB": {"symbol_binance": "SHIBUSDT", "symbol_kraken": "SHIBUSD", "symbol_crypto": "SHIB_USDT"},
    "MATIC": {"symbol_binance": "MATICUSDT", "symbol_kraken": "MATICUSD", "symbol_crypto": "MATIC_USDT"}
}

st.set_page_config(page_title="Live Crypto Arbitrage Scanner", layout="wide")
st.title("📈 Live Crypto Arbitrage Scanner")

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Cryptocurrency", list(COINS.keys()), index=0)
    min_profit = st.slider("Minimum Profit (%)", 0.5, 10.0, 2.0)
    investment = st.number_input("Investment (AUD)", min_value=10.0, value=1000.0)
    refresh_rate = st.slider("Refresh Interval (sec)", 5, 60, 10)
    selected_exchanges = st.multiselect("Exchanges", EXCHANGES, default=EXCHANGES)

# API fetch functions
def fetch_binance(symbol):
    url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
    r = requests.get(url).json()
    return {'buy': float(r['askPrice']) * USD_TO_AUD, 'sell': float(r['bidPrice']) * USD_TO_AUD, 'fee': 0.001}

def fetch_kraken(symbol):
    url = f"https://api.kraken.com/0/public/Ticker?pair={symbol}"
    r = requests.get(url).json()
    key = list(r["result"].keys())[0]
    data = r["result"][key]
    return {'buy': float(data["a"][0]) * USD_TO_AUD, 'sell': float(data["b"][0]) * USD_TO_AUD, 'fee': 0.0026}

def fetch_coinspot(coin):
    r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
    price = r["prices"].get(coin)
    return {'buy': float(price["ask"]), 'sell': float(price["bid"]), 'fee': 0.01} if price else None

def fetch_independent_reserve(coin):
    url = f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD"
    r = requests.get(url).json()
    return {'buy': float(r["CurrentLowestOfferPrice"]), 'sell': float(r["CurrentHighestBidPrice"]), 'fee': 0.005}

def fetch_coinbase(coin):
    r_buy = requests.get(f"https://api.coinbase.com/v2/prices/{coin}-USD/buy").json()
    r_sell = requests.get(f"https://api.coinbase.com/v2/prices/{coin}-USD/sell").json()
    return {'buy': float(r_buy["data"]["amount"]) * USD_TO_AUD, 'sell': float(r_sell["data"]["amount"]) * USD_TO_AUD, 'fee': 0.006}

def fetch_coinjar(coin):
    url = f"https://data.exchange.coinjar.com/products/{coin.lower()}aud/ticker"
    r = requests.get(url).json()
    return {'buy': float(r['ask']), 'sell': float(r['bid']), 'fee': 0.005}

def fetch_crypto_com(symbol):
    url = f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}"
    r = requests.get(url).json()
    data = r["result"]["data"][0]
    return {'buy': float(data["a"]) * USD_TO_AUD, 'sell': float(data["b"]) * USD_TO_AUD, 'fee': 0.004}

# Main scanner
fetchers = {
    "Binance": lambda: fetch_binance(COINS[coin]["symbol_binance"]),
    "Kraken": lambda: fetch_kraken(COINS[coin]["symbol_kraken"]),
    "CoinSpot": lambda: fetch_coinspot(coin),
    "IndependentReserve": lambda: fetch_independent_reserve(coin),
    "Coinbase": lambda: fetch_coinbase(coin),
    "CoinJar": lambda: fetch_coinjar(coin),
    "Crypto.com": lambda: fetch_crypto_com(COINS[coin]["symbol_crypto"])
}

results = {ex: fetchers[ex]() for ex in selected_exchanges if fetchers[ex]()}
valid = {ex: val for ex, val in results.items() if val}

if valid:
    best_buy = min(valid.items(), key=lambda x: x[1]['buy'])
    best_sell = max(valid.items(), key=lambda x: x[1]['sell'])
    spread = best_sell[1]['sell'] - best_buy[1]['buy']
    profit_pct = round((spread / best_buy[1]['buy']) * 100, 2)
    profit_aud = round((profit_pct / 100) * investment, 2)
    if profit_pct >= min_profit:
        st.success(f"🚀 Arbitrage Opportunity")
        st.write(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"🛒 Buy from: {best_buy[0]} at AUD ${best_buy[1]['buy']:.2f}")
        st.write(f"💰 Sell on: {best_sell[0]} at AUD ${best_sell[1]['sell']:.2f}")
        st.write(f"🔄 Spread: AUD ${spread:.2f} ({profit_pct}%)")
        st.write(f"💸 Net Profit: AUD ${profit_aud} (after estimated fees)")
    else:
        st.warning("No arbitrage opportunity above the selected threshold.")
else:
    st.error("No valid market data found.")

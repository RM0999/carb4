
import streamlit as st
import requests
from datetime import datetime

# AUD conversion rate
USD_TO_AUD = 1.52

# Streamlit page config
st.set_page_config(page_title="Live Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔍 Live Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

# Sidebar settings
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Select Coin", ["BTC", "ETH", "LTC", "XRP", "ADA", "DOGE", "SHIB", "MATIC"])
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 10.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    selected_exchanges = st.multiselect("Exchanges", ["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase", "CoinJar", "Crypto.com"],
                                        default=["Binance", "Kraken", "CoinSpot", "IndependentReserve"])

COINS = {
    "BTC": {
        "symbol_binance": "BTCUSDT",
        "symbol_kraken": "XBTUSDT",
        "symbol_coinspot": "BTC",
        "symbol_independentreserve": "Xbt",
        "symbol_coinbase": "BTC-USD",
        "symbol_coinjar": "btcaud",
        "symbol_cryptocom": "BTC_USDT"
    },
    "ETH": {
        "symbol_binance": "ETHUSDT",
        "symbol_kraken": "ETHUSDT",
        "symbol_coinspot": "ETH",
        "symbol_independentreserve": "Eth",
        "symbol_coinbase": "ETH-USD",
        "symbol_coinjar": "ethaud",
        "symbol_cryptocom": "ETH_USDT"
    },
    "LTC": {
        "symbol_binance": "LTCUSDT",
        "symbol_kraken": "LTCUSDT",
        "symbol_coinspot": "LTC",
        "symbol_independentreserve": "Ltc",
        "symbol_coinbase": "LTC-USD",
        "symbol_coinjar": "ltcaud",
        "symbol_cryptocom": "LTC_USDT"
    },
    "XRP": {
        "symbol_binance": "XRPUSDT",
        "symbol_kraken": "XRPUSDT",
        "symbol_coinspot": "XRP",
        "symbol_independentreserve": "Xrp",
        "symbol_coinbase": "XRP-USD",
        "symbol_coinjar": "xrpaud",
        "symbol_cryptocom": "XRP_USDT"
    },
    "ADA": {
        "symbol_binance": "ADAUSDT",
        "symbol_kraken": "ADAUSDT",
        "symbol_coinspot": "ADA",
        "symbol_independentreserve": "Ada",
        "symbol_coinbase": "ADA-USD",
        "symbol_coinjar": "adaaud",
        "symbol_cryptocom": "ADA_USDT"
    },
    "DOGE": {
        "symbol_binance": "DOGEUSDT",
        "symbol_kraken": "DOGEUSDT",
        "symbol_coinspot": "DOGE",
        "symbol_independentreserve": "Doge",
        "symbol_coinbase": "DOGE-USD",
        "symbol_coinjar": "dogeaud",
        "symbol_cryptocom": "DOGE_USDT"
    },
    "SHIB": {
        "symbol_binance": "SHIBUSDT",
        "symbol_kraken": "SHIBUSDT",
        "symbol_coinspot": "SHIB",
        "symbol_independentreserve": "Shib",
        "symbol_coinbase": "SHIB-USD",
        "symbol_coinjar": "shibaud",
        "symbol_cryptocom": "SHIB_USDT"
    },
    "MATIC": {
        "symbol_binance": "MATICUSDT",
        "symbol_kraken": "MATICUSDT",
        "symbol_coinspot": "MATIC",
        "symbol_independentreserve": "Matic",
        "symbol_coinbase": "MATIC-USD",
        "symbol_coinjar": "maticaud",
        "symbol_cryptocom": "MATIC_USDT"
    }
}

# Fetching functions (some simplified for brevity)
def fetch_binance(symbol):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}").json()
        return {'buy': float(r['askPrice']) * USD_TO_AUD, 'sell': float(r['bidPrice']) * USD_TO_AUD, 'fee': 0.001}
    except:
        return None

def fetch_kraken(symbol):
    try:
        pair = symbol.replace("USDT", "").replace("XBT", "BTC")
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={symbol}").json()
        key = list(r['result'].keys())[0]
        return {'buy': float(r['result'][key]['a'][0]) * USD_TO_AUD, 'sell': float(r['result'][key]['b'][0]) * USD_TO_AUD, 'fee': 0.0026}
    except:
        return None

def fetch_coinspot(symbol):
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        return {'buy': float(r['prices'][symbol]['ask']), 'sell': float(r['prices'][symbol]['bid']), 'fee': 0.01}
    except:
        return None

def fetch_independent_reserve(symbol):
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={symbol}&secondaryCurrencyCode=AUD").json()
        return {'buy': float(r['CurrentLowestOfferPrice']), 'sell': float(r['CurrentHighestBidPrice']), 'fee': 0.005}
    except:
        return None

def fetch_coinbase(symbol):
    try:
        r = requests.get(f"https://api.exchange.coinbase.com/products/{symbol}/ticker").json()
        return {'buy': float(r['ask']) * USD_TO_AUD, 'sell': float(r['bid']) * USD_TO_AUD, 'fee': 0.006}
    except:
        return None

def fetch_coinjar(symbol):
    try:
        r = requests.get(f"https://data.exchange.coinjar.com/products/{symbol}/ticker").json()
        return {'buy': float(r['ask']), 'sell': float(r['bid']), 'fee': 0.005}
    except:
        return None

def fetch_cryptocom(symbol):
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}").json()
        data = r['result']['data']
        return {'buy': float(data['a']) * USD_TO_AUD, 'sell': float(data['b']) * USD_TO_AUD, 'fee': 0.004}
    except:
        return None

# Fetcher setup
fetchers = {
    "Binance": lambda: fetch_binance(COINS[coin]["symbol_binance"]),
    "Kraken": lambda: fetch_kraken(COINS[coin]["symbol_kraken"]),
    "CoinSpot": lambda: fetch_coinspot(COINS[coin]["symbol_coinspot"]),
    "IndependentReserve": lambda: fetch_independent_reserve(COINS[coin]["symbol_independentreserve"]),
    "Coinbase": lambda: fetch_coinbase(COINS[coin]["symbol_coinbase"]),
    "CoinJar": lambda: fetch_coinjar(COINS[coin]["symbol_coinjar"]),
    "Crypto.com": lambda: fetch_cryptocom(COINS[coin]["symbol_cryptocom"])
}

# Run scan
results = {ex: fetchers[ex]() for ex in selected_exchanges if fetchers[ex]()}
valid_results = {k: v for k, v in results.items() if v}

if valid_results:
    best_buy = min(valid_results.items(), key=lambda x: x[1]["buy"])
    best_sell = max(valid_results.items(), key=lambda x: x[1]["sell"])
    
    spread = round(best_sell[1]["sell"] - best_buy[1]["buy"], 2)
    gross_profit_pct = round(spread / best_buy[1]["buy"] * 100, 2)

    # Net profit after fees
    buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit = spread - buy_fee - sell_fee
    net_profit_pct = round(net_profit / best_buy[1]["buy"] * 100, 2)
    net_profit_aud = round(investment * net_profit_pct / 100, 2)

    if net_profit_pct >= min_profit:
        st.success(f"🚀 Opportunity Found! {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"🪙 Coin: **{coin}**")
        st.write(f"🛒 Buy from: **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
        st.write(f"💰 Sell on: **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
        st.write(f"🔄 Spread: **AUD ${spread:.2f}** ({gross_profit_pct}%)")
        st.write(f"💸 Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
        st.write(f"✅ Net Profit: **{net_profit_pct}%** | **AUD ${net_profit_aud:.2f}**")
    else:
        st.warning("⚠️ No arbitrage opportunity above minimum net profit threshold.")
else:
    st.error("❌ Could not fetch data from selected exchanges.")

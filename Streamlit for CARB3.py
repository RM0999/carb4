
import streamlit as st
import requests
from datetime import datetime

# AUD conversion fallback rate
USD_TO_AUD = 1.52

st.set_page_config(page_title="🔍 Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>💹 Live Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Select Coin", ["BTC", "ETH", "XRP", "LTC", "ADA"])
    pair = f"{coin}/USDT"
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 10.0, 0.5)
    investment = st.number_input("Investment Amount (AUD)", min_value=10, value=1000)
    refresh_rate = st.slider("Auto Refresh Rate (sec)", 5, 60, 10)
    selected_exchanges = st.multiselect("Exchanges", [
        "Binance", "Kraken", "CoinSpot", "IndependentReserve",
        "Coinbase", "CoinJar", "Crypto.com"
    ], default=[
        "Binance", "Kraken", "CoinSpot", "IndependentReserve"
    ])

# === Fetch Functions === #
def fetch_binance(symbol):
    try:
        r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}").json()
        return {'buy': float(r['askPrice']) * USD_TO_AUD, 'sell': float(r['bidPrice']) * USD_TO_AUD, 'fee': 0.001}
    except: return None

def fetch_kraken(symbol):
    symbol_map = {"BTC": "XBT", "ETH": "ETH", "XRP": "XRP", "LTC": "LTC", "ADA": "ADA"}
    try:
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={symbol_map[symbol]}USDT").json()
        key = list(r["result"].keys())[0]
        return {'buy': float(r["result"][key]["a"][0]) * USD_TO_AUD, 'sell': float(r["result"][key]["b"][0]) * USD_TO_AUD, 'fee': 0.0026}
    except: return None

def fetch_coinspot(symbol):
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        data = r['prices'].get(symbol, {})
        return {'buy': float(data.get('ask', 0)), 'sell': float(data.get('bid', 0)), 'fee': 0.01} if data else None
    except: return None

def fetch_independent_reserve(symbol):
    code_map = {"BTC": "Xbt", "ETH": "Eth", "XRP": "Xrp", "LTC": "Ltc", "ADA": "Ada"}
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={code_map[symbol]}&secondaryCurrencyCode=Aud").json()
        return {'buy': float(r['CurrentLowestOfferPrice']), 'sell': float(r['CurrentHighestBidPrice']), 'fee': 0.005}
    except: return None

def fetch_coinbase(symbol):
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot").json()
        price = float(r['data']['amount']) * USD_TO_AUD
        return {'buy': price * 1.001, 'sell': price * 0.999, 'fee': 0.005}
    except: return None

def fetch_coinjar(symbol):
    try:
        r = requests.get(f"https://data.exchange.coinjar.com/products/{symbol}usdt/ticker").json()
        return {'buy': float(r['ask']) * USD_TO_AUD, 'sell': float(r['bid']) * USD_TO_AUD, 'fee': 0.01}
    except: return None

def fetch_crypto_com(symbol):
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}_USDT").json()
        data = r["result"]["data"]
        return {'buy': float(data['a']) * USD_TO_AUD, 'sell': float(data['b']) * USD_TO_AUD, 'fee': 0.004}
    except: return None

# Map fetchers
fetchers = {
    "Binance": fetch_binance,
    "Kraken": fetch_kraken,
    "CoinSpot": fetch_coinspot,
    "IndependentReserve": fetch_independent_reserve,
    "Coinbase": fetch_coinbase,
    "CoinJar": fetch_coinjar,
    "Crypto.com": fetch_crypto_com
}

# === Fetch Market Data === #
market_data = {}
for ex in selected_exchanges:
    result = fetchers[ex](coin)
    if result:
        market_data[ex] = result

if market_data:
    best_buy = min(market_data.items(), key=lambda x: x[1]['buy'])
    best_sell = max(market_data.items(), key=lambda x: x[1]['sell'])

    spread = round(best_sell[1]['sell'] - best_buy[1]['buy'], 2)
    spread_pct = round((spread / best_buy[1]['buy']) * 100, 2)

    # Net profit considering fees
    fee_buy = best_buy[1]['buy'] * best_buy[1]['fee']
    fee_sell = best_sell[1]['sell'] * best_sell[1]['fee']
    net_profit_per_coin = best_sell[1]['sell'] - best_buy[1]['buy'] - fee_buy - fee_sell
    net_profit_pct = round((net_profit_per_coin / best_buy[1]['buy']) * 100, 2)
    net_aud_profit = round(investment * (net_profit_pct / 100), 2)

    if net_profit_pct >= min_profit:
        st.success(f"🚀 Arbitrage Opportunity Found for {pair} at {datetime.now().strftime('%H:%M:%S')}")
        st.markdown(f"""
        - 🛒 **Buy from:** `{best_buy[0]}` at **AUD ${best_buy[1]['buy']:.2f}**
        - 💰 **Sell on:** `{best_sell[0]}` at **AUD ${best_sell[1]['sell']:.2f}**
        - 🔄 **Spread:** AUD ${spread:.2f} ({spread_pct}%)
        - 💸 **Net Profit:** **{net_profit_pct}%** | **AUD ${net_aud_profit}**
        - 📉 **Fees:** Buy Fee = AUD ${fee_buy:.2f}, Sell Fee = AUD ${fee_sell:.2f}
        """)
    else:
        st.warning("📉 No profitable arbitrage opportunity at this time.")
else:
    st.error("❌ Could not fetch live data from selected exchanges.")


import streamlit as st
import requests
from datetime import datetime

# Constants
USD_TO_AUD = 1.52
INVESTMENT = 1000  # Default investment for fee calculation

# Supported coins and their exchange-specific symbols
COINS = {
    "BTC": {"binance": "BTCUSDT", "kraken": "XBTUSDT"},
    "ETH": {"binance": "ETHUSDT", "kraken": "ETHUSDT"},
    "LTC": {"binance": "LTCUSDT", "kraken": "LTCUSDT"},
    "XRP": {"binance": "XRPUSDT", "kraken": "XRPUSDT"},
    "ADA": {"binance": "ADAUSDT", "kraken": "ADAUSDT"},
    "DOGE": {"binance": "DOGEUSDT", "kraken": "DOGEUSDT"},
    "SHIB": {"binance": "SHIBUSDT", "kraken": "SHIBUSDT"},
    "MATIC": {"binance": "MATICUSDT", "kraken": "MATICUSDT"}
}

# Exchange fetch functions
def fetch_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
        r = requests.get(url).json()
        return {"buy": float(r["askPrice"]) * USD_TO_AUD, "sell": float(r["bidPrice"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

def fetch_kraken(symbol):
    try:
        url = f"https://api.kraken.com/0/public/Ticker?pair={symbol}"
        r = requests.get(url).json()
        data = list(r["result"].values())[0]
        return {"buy": float(data["a"][0]) * USD_TO_AUD, "sell": float(data["b"][0]) * USD_TO_AUD, "fee": 0.0026}
    except:
        return None

def fetch_coinspot(coin):
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        return {"buy": float(r["prices"][coin]["ask"]), "sell": float(r["prices"][coin]["bid"]), "fee": 0.01}
    except:
        return None

def fetch_independent_reserve(coin):
    try:
        url = f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD"
        r = requests.get(url).json()
        return {"buy": float(r["CurrentLowestOfferPrice"]), "sell": float(r["CurrentHighestBidPrice"]), "fee": 0.005}
    except:
        return None

# Streamlit UI
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔍 Crypto Arbitrage Scanner (Live)</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Settings")
    selected_coin = st.selectbox("Select Coin", list(COINS.keys()))
    min_profit = st.slider("Minimum Profit Threshold (%)", 0.1, 10.0, 0.5)
    investment = st.number_input("Investment Amount (AUD)", min_value=10, value=1000)
    selected_exchanges = st.multiselect("Exchanges", ["Binance", "Kraken", "CoinSpot", "IndependentReserve"], default=["Binance", "Kraken", "CoinSpot", "IndependentReserve"])

# Fetch data once per exchange
results = {}
for ex in selected_exchanges:
    if ex == "Binance":
        results[ex] = fetch_binance(COINS[selected_coin]["binance"])
    elif ex == "Kraken":
        results[ex] = fetch_kraken(COINS[selected_coin]["kraken"])
    elif ex == "CoinSpot":
        results[ex] = fetch_coinspot(selected_coin)
    elif ex == "IndependentReserve":
        results[ex] = fetch_independent_reserve(selected_coin)

# Filter valid results
valid_data = {ex: val for ex, val in results.items() if val}
st.write("🔎 Price Table (Live Fetch)")
st.dataframe(valid_data)

# Arbitrage logic
if len(valid_data) >= 2:
    best_buy = min(valid_data.items(), key=lambda x: x[1]['buy'])
    best_sell = max(valid_data.items(), key=lambda x: x[1]['sell'])

    buy_total = best_buy[1]['buy'] * (1 + best_buy[1]['fee'])
    sell_total = best_sell[1]['sell'] * (1 - best_sell[1]['fee'])

    spread = round(sell_total - buy_total, 2)
    profit_pct = round((sell_total - buy_total) / buy_total * 100, 2)
    profit_aud = round(investment * profit_pct / 100, 2)

    if profit_pct >= min_profit:
        st.success(f"🚀 Arbitrage Opportunity Found at {datetime.now().strftime('%H:%M:%S')}")
        st.markdown(f"🛒 **Buy from:** `{best_buy[0]}` at **AUD ${best_buy[1]['buy']:.2f}**")
        st.markdown(f"💰 **Sell on:** `{best_sell[0]}` at **AUD ${best_sell[1]['sell']:.2f}**")
        st.markdown(f"🔄 **Spread:** AUD ${spread} ({profit_pct}%)")
        st.markdown(f"💸 **Net Profit:** {profit_pct}% | **AUD ${profit_aud}**")
        st.markdown(f"📉 **Fees:** Buy = AUD ${best_buy[1]['buy'] * best_buy[1]['fee']:.2f}, Sell = AUD ${best_sell[1]['sell'] * best_sell[1]['fee']:.2f}")
    else:
        st.warning("⚠️ No profitable arbitrage opportunity found above your threshold.")
else:
    st.error("❌ Not enough data to compare exchanges.")

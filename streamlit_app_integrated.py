
import streamlit as st
import requests
from datetime import datetime
from fetch_all_exchanges_full import (
    fetch_coinspot,
    fetch_kraken,
    fetch_coinbase,
    fetch_independent_reserve,
    fetch_crypto_com
)

st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔒 Secure Arbitrage Scanner</h1>", unsafe_allow_html=True)

# Live FX rate
def get_fx_rate():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD").json()
        return r["rates"]["AUD"]
    except:
        return 1.52

USD_TO_AUD = get_fx_rate()

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Select Coin", ["BTC", "ETH", "LTC", "XRP", "ADA", "DOGE", "SHIB", "MATIC"])
    min_profit = st.slider("Minimum Net Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    exchanges = st.multiselect("Exchanges", ["Coinbase", "Crypto.com", "CoinSpot", "Kraken", "IndependentReserve"],
                               default=["Coinbase", "Kraken", "CoinSpot", "Crypto.com", "IndependentReserve"])

fetchers = {
    "Coinbase": lambda: fetch_coinbase(coin),
    "Crypto.com": lambda: fetch_crypto_com(coin),
    "CoinSpot": lambda: fetch_coinspot(coin),
    "Kraken": lambda: fetch_kraken(coin),
    "IndependentReserve": lambda: fetch_independent_reserve(coin)
}

# --- Arbitrage Logic ---
data = {ex: fetchers[ex]() for ex in exchanges if fetchers[ex]() is not None}
valid = {ex: val for ex, val in data.items() if val}

if valid:
    best_buy = min(valid.items(), key=lambda x: x[1]["buy"])
    best_sell = max(valid.items(), key=lambda x: x[1]["sell"])
    spread = best_sell[1]["sell"] - best_buy[1]["buy"]

    buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit = spread - buy_fee - sell_fee
    profit_pct = round((net_profit / best_buy[1]["buy"]) * 100, 2)
    profit_aud = round((net_profit / best_buy[1]["buy"]) * investment, 2)

    if profit_pct >= min_profit:
        st.success(f"🟢 Arbitrage Opportunity Found at {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"🛒 Buy from: **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
        st.write(f"💰 Sell on: **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
        st.write(f"🔄 Spread: **AUD ${spread:.2f}**")
        st.write(f"💸 Net Profit: **{profit_pct}%** | **AUD ${profit_aud}**")
        st.caption(f"Fees: Buy Fee = AUD ${buy_fee:.2f}, Sell Fee = AUD ${sell_fee:.2f}")
    else:
        st.warning("No profitable arbitrage opportunity found above your threshold.")
else:
    st.error("⚠️ Could not retrieve valid data from selected exchanges.")


import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Crypto Arbitrage Debug", layout="wide")
st.title("🔍 Debug Crypto Arbitrage Scanner")

# --- Settings ---
USD_TO_AUD = 1.52  # Replace with dynamic fetch if needed

with st.sidebar:
    st.title("⚙️ Settings")
    coin = st.selectbox("Coin", ["BTC", "ETH", "LTC", "XRP", "ADA", "DOGE", "SHIB", "MATIC"])
    min_profit = st.slider("Minimum Profit (%)", 0.1, 5.0, 1.0)
    investment = st.number_input("Investment (AUD)", value=1000)
    exchanges = st.multiselect("Exchanges", ["Crypto.com", "Coinbase", "CoinSpot", "Kraken", "IndependentReserve"],
                               default=["Crypto.com", "Coinbase", "CoinSpot", "Kraken", "IndependentReserve"])

def fetch_crypto_com():
    try:
        r = requests.get("https://api.crypto.com/v2/public/get-ticker?instrument_name=BTC_USDT").json()
        data = r["result"]["data"]
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.001}
    except Exception as e:
        return {"error": str(e)}

def fetch_coinbase():
    try:
        r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot").json()
        price = float(r["data"]["amount"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except Exception as e:
        return {"error": str(e)}

def fetch_coinspot():
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        ask = float(r['prices']['BTC']['ask'])
        bid = float(r['prices']['BTC']['bid'])
        return {"buy": ask, "sell": bid, "fee": 0.01}
    except Exception as e:
        return {"error": str(e)}

def fetch_kraken():
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD").json()
        data = r["result"]["XXBTZUSD"]
        return {"buy": float(data["a"][0]) * USD_TO_AUD, "sell": float(data["b"][0]) * USD_TO_AUD, "fee": 0.0026}
    except Exception as e:
        return {"error": str(e)}

def fetch_independent_reserve():
    try:
        r = requests.get("https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode=Xbt&secondaryCurrencyCode=Aud").json()
        return {"buy": float(r["CurrentLowestOfferPrice"]), "sell": float(r["CurrentHighestBidPrice"]), "fee": 0.005}
    except Exception as e:
        return {"error": str(e)}

# Exchange mapping
fetchers = {
    "Crypto.com": fetch_crypto_com,
    "Coinbase": fetch_coinbase,
    "CoinSpot": fetch_coinspot,
    "Kraken": fetch_kraken,
    "IndependentReserve": fetch_independent_reserve,
}

# Fetch data with debug output
data = {}
st.subheader("🔎 Raw Exchange Data")
for ex in exchanges:
    result = fetchers[ex]()
    st.write(f"{ex}:", result)
    if "buy" in result and "sell" in result:
        data[ex] = result

# Arbitrage logic
if len(data) >= 2:
    best_buy = min(data.items(), key=lambda x: x[1]['buy'])
    best_sell = max(data.items(), key=lambda x: x[1]['sell'])

    spread = best_sell[1]["sell"] - best_buy[1]["buy"]
    buy_fee = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit = spread - buy_fee - sell_fee
    profit_pct = round((net_profit / best_buy[1]["buy"]) * 100, 2)
    profit_aud = round((net_profit / best_buy[1]["buy"]) * investment, 2)

    st.subheader("📊 Arbitrage Result")
    st.write(f"Buy from: {best_buy[0]} at AUD ${best_buy[1]['buy']:.2f}")
    st.write(f"Sell on: {best_sell[0]} at AUD ${best_sell[1]['sell']:.2f}")
    st.write(f"Spread: AUD ${spread:.2f}")
    st.write(f"Buy Fee: AUD ${buy_fee:.2f}")
    st.write(f"Sell Fee: AUD ${sell_fee:.2f}")
    st.write(f"Net Profit: {profit_pct}% | AUD ${profit_aud}")

    if profit_pct >= min_profit:
        st.success("✅ Profitable Arbitrage Opportunity Found!")
    else:
        st.warning("⚠️ No arbitrage opportunity above your threshold.")
else:
    st.error("🚫 Not enough valid exchange data to calculate arbitrage.")

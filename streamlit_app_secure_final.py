
import streamlit as st
import requests, time, hmac, hashlib, json, base64, urllib.parse
from datetime import datetime

# Load secrets
api = st.secrets["api_keys"]

# Live FX rate
def get_fx_rate():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD").json()
        return r["rates"]["AUD"]
    except:
        return 1.52

USD_TO_AUD = get_fx_rate()

# --- CoinSpot ---
def fetch_coinspot(coin: str):
    try:
        nonce = str(int(time.time()*1000))
        body = json.dumps({"nonce": nonce}).encode()
        sign = hmac.new(api["coinspot_api_secret"].encode(), body, hashlib.sha512).hexdigest()
        headers = {"Content-Type": "application/json", "key": api["coinspot_api_key"], "sign": sign}
        r = requests.post("https://www.coinspot.com.au/api/quotes", headers=headers, data=body, timeout=7)
        data = r.json()
        ask = float(data[coin.lower()]["buy"])
        bid = float(data[coin.lower()]["sell"])
        return {"buy": ask, "sell": bid, "fee": 0.01}
    except Exception as e:
        st.error(f"CoinSpot error: {e}")
        return None

# --- Kraken ---
def fetch_kraken(coin: str):
    try:
        uri_path = "/0/public/Ticker"
        pair_map = {"BTC": "XBTUSD", "ETH": "ETHUSD", "LTC": "LTCUSD", "XRP": "XRPUSD", "ADA": "ADAUSD", "DOGE": "DOGEUSD", "SHIB": "SHIBUSD", "MATIC": "MATICUSD"}
        pair = pair_map[coin]
        r = requests.get(f"https://api.kraken.com{uri_path}?pair={pair}", timeout=7)
        data = r.json()
        tkr = list(data["result"].values())[0]
        ask = float(tkr["a"][0]) * USD_TO_AUD
        bid = float(tkr["b"][0]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.0026}
    except Exception as e:
        st.error(f"Kraken error: {e}")
        return None

# --- Coinbase ---
def fetch_coinbase(coin: str):
    try:
        ts = str(int(time.time()))
        req = f"/api/v3/brokerage/products/{coin}-USD"
        msg = ts + "GET" + req
        sign = hmac.new(api["coinbase_api_secret"].encode(), msg.encode(), hashlib.sha256).digest()
        headers = {
            "CB-ACCESS-KEY": api["coinbase_api_key"],
            "CB-ACCESS-SIGN": base64.b64encode(sign).decode(),
            "CB-ACCESS-TIMESTAMP": ts,
            "CB-VERSION": "2023-01-01"
        }
        r = requests.get("https://api.coinbase.com" + req, headers=headers, timeout=7)
        if r.status_code != 200:
            raise Exception(r.text)
        data = r.json()
        price = float(data["price"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except Exception as e:
        st.error(f"Coinbase error: {e}")
        return None

# --- Independent Reserve ---
def fetch_independent_reserve(coin: str):
    try:
        path = "/Private/GetMarketSummary"
        nonce = str(int(time.time()*1000))
        qs = f"primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD"
        sigmsg = path + nonce + qs
        sig = hmac.new(api["independent_reserve_secret"].encode(), sigmsg.encode(), hashlib.sha256).hexdigest()
        headers = {"api-key": api["independent_reserve_key"], "timestamp": nonce, "signature": sig}
        url = "https://api.independentreserve.com" + path + "?" + qs
        r = requests.get(url, headers=headers, timeout=7)
        data = json.loads(r.content.decode("utf-8-sig"))
        ask = float(data["CurrentLowestOfferPrice"])
        bid = float(data["CurrentHighestBidPrice"])
        return {"buy": ask, "sell": bid, "fee": 0.005}
    except Exception as e:
        st.error(f"IR error: {e}")
        return None

# --- Crypto.com ---
def fetch_crypto_com(coin: str):
    try:
        url = "https://api.crypto.com/v2/private/get-ticker"
        nonce = int(time.time()*1000)
        payload = {
            "id": 11,
            "method": "private/get-ticker",
            "api_key": api["crypto_api_key"],
            "params": {"instrument_name": f"{coin}_USDT"},
            "nonce": nonce
        }
        sig = hmac.new(api["crypto_api_secret"].encode(), (str(nonce)+api["crypto_api_key"]).encode(), hashlib.sha256).hexdigest()
        payload["sig"] = sig
        r = requests.post(url, json=payload, timeout=7)
        data = r.json()["result"]["data"]
        ask = float(data["a"]) * USD_TO_AUD
        bid = float(data["b"]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.001}
    except Exception as e:
        st.error(f"Crypto.com error: {e}")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔒 Secure Arbitrage Scanner</h1>", unsafe_allow_html=True)

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

# --- Arbitrage Scan ---
data = {}
for ex in exchanges:
    result = fetchers[ex]()
    if result:
        data[ex] = result

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

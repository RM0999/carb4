
import requests, time, hmac, hashlib, json, base64, urllib.parse
import streamlit as st

USD_TO_AUD = 1.52  # fallback FX
api = st.secrets["api_keys"]  # shorthand for secrets access

def fetch_coinspot(coin: str):
    try:
        nonce = str(int(time.time()*1000))
        body = json.dumps({"nonce": nonce}).encode()
        sign = hmac.new(api["coinspot_api_secret"].encode(), body, hashlib.sha512).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "key": api["coinspot_api_key"],
            "sign": sign
        }
        r = requests.post("https://www.coinspot.com.au/api/quotes", headers=headers, data=body, timeout=7).json()
        ask = float(r[coin.lower()]["buy"])
        bid = float(r[coin.lower()]["sell"])
        return {"buy": ask, "sell": bid, "fee": 0.01}
    except Exception as e:
        st.error(f"CoinSpot error: {e}")
        return None

def fetch_kraken(coin: str):
    try:
        uri_path = "/0/public/Ticker"
        pair_map = {"BTC": "XBTUSD", "ETH": "ETHUSD", "LTC": "LTCUSD", "XRP": "XRPUSD", "ADA": "ADAUSD",
                    "DOGE": "DOGEUSD", "SHIB": "SHIBUSD", "MATIC": "MATICUSD"}
        pair = pair_map.get(coin, f"{coin}USD")
        url = f"https://api.kraken.com{uri_path}?pair={pair}"
        r = requests.get(url, timeout=7).json()
        key = list(r["result"].keys())[0]
        data = r["result"][key]
        ask = float(data["a"][0]) * USD_TO_AUD
        bid = float(data["b"][0]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.0026}
    except Exception as e:
        st.error(f"Kraken error: {e}")
        return None

def fetch_coinbase(coin: str):
    try:
        ts = str(int(time.time()))
        req = f"/api/v3/brokerage/products/{coin}-USD"
        msg = ts + "GET" + req
        sign = hmac.new(api["coinbase_api_secret"].encode(), msg.encode(), hashlib.sha256).digest()
        headers = {
            "CB-ACCESS-KEY": api["coinbase_api_key"],
            "CB-ACCESS-SIGN": base64.b64encode(sign),
            "CB-ACCESS-TIMESTAMP": ts,
            "CB-VERSION": "2023-01-01"
        }
        r = requests.get("https://api.coinbase.com"+req, headers=headers, timeout=7).json()
        price = float(r["price"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except Exception as e:
        st.error(f"Coinbase error: {e}")
        return None

def fetch_independent_reserve(coin: str):
    try:
        path = "/Public/GetMarketSummary"
        url = f"https://api.independentreserve.com{path}?primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD"
        r = requests.get(url, timeout=7).json()
        ask = float(r["CurrentLowestOfferPrice"])
        bid = float(r["CurrentHighestBidPrice"])
        return {"buy": ask, "sell": bid, "fee": 0.005}
    except Exception as e:
        st.error(f"Independent Reserve error: {e}")
        return None

def fetch_crypto(coin: str):
    try:
        url = "https://api.crypto.com/v2/public/get-ticker"
        r = requests.get(f"{url}?instrument_name={coin}_USDT", timeout=7).json()
        data = r["result"]["data"]
        ask = float(data["a"]) * USD_TO_AUD
        bid = float(data["b"]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.001}
    except Exception as e:
        st.error(f"Crypto.com error: {e}")
        return None

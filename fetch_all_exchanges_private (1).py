
import requests, time, hmac, hashlib, json, base64, urllib.parse
import streamlit as st

USD_TO_AUD = 1.52  # fallback FX rate

# ---------- CoinSpot ----------
def fetch_coinspot(coin: str):
    try:
        api = st.secrets["api_keys"]
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

# ---------- Kraken ----------
def fetch_kraken(coin: str):
    try:
        api = st.secrets["api_keys"]
        uri_path = "/0/private/Ticker"
        nonce = str(int(time.time()*1000))
        pair_map = {"BTC": "XBTUSD", "ETH": "ETHUSD", "LTC": "LTCUSD", "XRP": "XRPUSD",
                    "ADA": "ADAUSD", "DOGE": "DOGEUSD", "SHIB": "SHIBUSD", "MATIC": "MATICUSD"}
        data = {"nonce": nonce, "pair": pair_map[coin]}
        postdata = urllib.parse.urlencode(data)
        m = hashlib.sha256((nonce + postdata).encode()).digest()
        sig = hmac.new(base64.b64decode(api["kraken_api_secret"]), (uri_path.encode() + m), hashlib.sha512).digest()
        headers = {
            "API-Key": api["kraken_api_key"],
            "API-Sign": base64.b64encode(sig)
        }
        r = requests.post("https://api.kraken.com" + uri_path, data=data, headers=headers, timeout=7).json()
        tkr = list(r["result"].values())[0]
        ask = float(tkr["a"][0]) * USD_TO_AUD
        bid = float(tkr["b"][0]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.0026}
    except Exception as e:
        st.error(f"Kraken error: {e}")
        return None

# ---------- Coinbase ----------
def fetch_coinbase(coin: str):
    try:
        api = st.secrets["api_keys"]
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
        r = requests.get("https://api.coinbase.com" + req, headers=headers, timeout=7).json()
        price = float(r["price"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except Exception as e:
        st.error(f"Coinbase error: {e}")
        return None

# ---------- Independent Reserve ----------
def fetch_independent_reserve(coin: str):
    try:
        api = st.secrets["api_keys"]
        path = "/Private/GetMarketSummary"
        nonce = str(int(time.time()*1000))
        qs = f"primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD"
        sigmsg = path + nonce + qs
        sig = hmac.new(api["independent_reserve_secret"].encode(), sigmsg.encode(), hashlib.sha256).hexdigest()
        headers = {
            "api-key": api["independent_reserve_key"],
            "timestamp": nonce,
            "signature": sig
        }
        url = "https://api.independentreserve.com" + path + "?" + qs
        r = requests.get(url, headers=headers, timeout=7).json()
        ask = float(r["CurrentLowestOfferPrice"])
        bid = float(r["CurrentHighestBidPrice"])
        return {"buy": ask, "sell": bid, "fee": 0.005}
    except Exception as e:
        st.error(f"Independent Reserve error: {e}")
        return None

# ---------- Crypto.com ----------
def fetch_crypto(coin: str):
    try:
        api = st.secrets["api_keys"]
        url = "https://api.crypto.com/v2/private/get-ticker"
        nonce = int(time.time()*1000)
        payload = {
            "id": 11,
            "method": "private/get-ticker",
            "api_key": api["crypto_api_key"],
            "params": {"instrument_name": f"{coin}_USDT"},
            "nonce": nonce
        }
        sig = hmac.new(api["crypto_api_secret"].encode(), (str(nonce) + api["crypto_api_key"]).encode(), hashlib.sha256).hexdigest()
        payload["sig"] = sig
        r = requests.post(url, json=payload, timeout=7).json()
        data = r["result"]["data"]
        ask = float(data["a"]) * USD_TO_AUD
        bid = float(data["b"]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.001}
    except Exception as e:
        st.error(f"Crypto.com error: {e}")
        return None

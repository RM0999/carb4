
import requests
import time
import hmac
import hashlib
import json
import streamlit as st

USD_TO_AUD = 1.52  # fallback in case FX API is not called

def fetch_coinspot(coin):
    try:
        key = st.secrets["api_keys"]["coinspot_api_key"]
        secret = st.secrets["api_keys"]["coinspot_api_secret"]
        nonce = str(int(time.time() * 1000))
        request_body = {"nonce": nonce}
        message = json.dumps(request_body).encode()
        signature = hmac.new(secret.encode(), message, hashlib.sha512).hexdigest()
        headers = {
            "Content-type": "application/json",
            "key": key,
            "sign": signature
        }
        r = requests.post("https://www.coinspot.com.au/api/quotes", headers=headers, data=message).json()
        ask = float(r[coin.lower()]["buy"])
        bid = float(r[coin.lower()]["sell"])
        return {"buy": ask, "sell": bid, "fee": 0.01}
    except:
        return None

def fetch_kraken(coin):
    try:
        pair = f"X{coin}ZUSD" if coin == "BTC" else f"{coin}USD"
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={pair}").json()
        key = list(r["result"].keys())[0]
        data = r["result"][key]
        ask = float(data["a"][0]) * USD_TO_AUD
        bid = float(data["b"][0]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.0026}
    except:
        return None

def fetch_coinbase(coin):
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{coin}-USD/spot").json()
        price = float(r["data"]["amount"]) * USD_TO_AUD
        return {"buy": price * 1.002, "sell": price * 0.998, "fee": 0.005}
    except:
        return None

def fetch_independent_reserve(coin):
    try:
        r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={coin}&secondaryCurrencyCode=AUD").json()
        ask = float(r["CurrentLowestOfferPrice"])
        bid = float(r["CurrentHighestBidPrice"])
        return {"buy": ask, "sell": bid, "fee": 0.005}
    except:
        return None

def fetch_crypto_com(coin):
    try:
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={coin}_USDT").json()
        data = r["result"]["data"]
        ask = float(data["a"]) * USD_TO_AUD
        bid = float(data["b"]) * USD_TO_AUD
        return {"buy": ask, "sell": bid, "fee": 0.001}
    except:
        return None


from __future__ import annotations
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf

TD_BASE = "https://api.twelvedata.com"

@dataclass
class Quote:
    symbol: str
    price: float | None
    source: str
    timestamp: str | None = None
    status: str = "ok"
    message: str = ""

def _get_json(url: str, timeout: int = 12):
    req = urllib.request.Request(url, headers={"User-Agent": "ASX-AI-Investment-Analyst/10.2"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def twelve_price(symbol: str, api_key: str) -> Quote:
    if not api_key:
        return Quote(symbol, None, "Twelve Data", status="no_key", message="No Twelve Data API key configured.")
    qs = urllib.parse.urlencode({"symbol": symbol, "apikey": api_key})
    try:
        data = _get_json(f"{TD_BASE}/price?{qs}")
        if data.get("status") == "error" or "price" not in data:
            return Quote(symbol, None, "Twelve Data", status="error",
                         message=data.get("message", "No price returned."))
        return Quote(symbol, float(data["price"]), "Twelve Data",
                     datetime.now(timezone.utc).isoformat())
    except Exception as e:
        return Quote(symbol, None, "Twelve Data", status="error", message=str(e))

def twelve_series(symbol: str, api_key: str, interval="1day", outputsize=500) -> pd.DataFrame:
    if not api_key:
        return pd.DataFrame()
    qs = urllib.parse.urlencode({
        "symbol": symbol, "interval": interval, "outputsize": int(outputsize),
        "order": "ASC", "apikey": api_key
    })
    try:
        data = _get_json(f"{TD_BASE}/time_series?{qs}")
        vals = data.get("values", [])
        if not vals:
            return pd.DataFrame()
        df = pd.DataFrame(vals)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime").sort_index()
        for c in ["open","high","low","close","volume"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()

def yahoo_history(symbol: str, period="5y", interval="1d") -> pd.DataFrame:
    try:
        return yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
    except Exception:
        return pd.DataFrame()

def yahoo_quote(symbol: str) -> Quote:
    try:
        h = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=True)
        if h.empty:
            return Quote(symbol, None, "Yahoo/yfinance", status="error", message="No price returned.")
        return Quote(symbol, float(h["Close"].iloc[-1]), "Yahoo/yfinance",
                     datetime.now(timezone.utc).isoformat())
    except Exception as e:
        return Quote(symbol, None, "Yahoo/yfinance", status="error", message=str(e))

def smart_quote(symbol: str, api_key: str = "", prefer_twelve=True) -> Quote:
    """Use Twelve Data where configured; fall back to Yahoo for development."""
    if prefer_twelve and api_key:
        q = twelve_price(symbol, api_key)
        if q.price is not None:
            return q
    return yahoo_quote(symbol)

def market_snapshot(api_key: str = "") -> pd.DataFrame:
    # Symbols chosen as compact cross-market indicators. Availability depends on plan.
    symbols = [
        ("S&P 500 ETF","SPY"), ("Nasdaq 100 ETF","QQQ"),
        ("AUD/USD","AUD/USD"), ("Gold","XAU/USD"),
        ("WTI crude","WTI/USD"), ("Copper","XCU/USD"),
    ]
    rows = []
    for label, symbol in symbols:
        q = twelve_price(symbol, api_key) if api_key else Quote(symbol,None,"Twelve Data",status="no_key")
        rows.append({"Market": label, "Symbol": symbol, "Price": q.price,
                     "Source": q.source, "Status": q.status, "Message": q.message})
    return pd.DataFrame(rows)

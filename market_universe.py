
from __future__ import annotations
import yfinance as yf

BENCHMARKS = {
    "ASX 200": "^AXJO",
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "Dow Jones": "^DJI",
}

def normalise_ticker(raw: str) -> str:
    t = (raw or "").strip().upper()
    # Preserve explicit exchange suffixes and common index/FX notation.
    if not t:
        return t
    if "." in t or t.startswith("^") or "/" in t or "=" in t:
        return t
    # V10.4 does not blindly append .AX because bare US symbols must work.
    return t

def detect_market(ticker: str, info: dict | None = None) -> dict:
    info = info or {}
    exchange = str(info.get("exchange") or info.get("fullExchangeName") or "").upper()
    quote_type = str(info.get("quoteType") or "").upper()
    if ticker.endswith(".AX") or "ASX" in exchange or "AUSTRAL" in exchange:
        market = "ASX"
        benchmark = "^AXJO"
    elif "NASDAQ" in exchange or exchange in {"NMS","NGM","NCM"}:
        market = "NASDAQ"
        benchmark = "^NDX"
    elif "NYSE" in exchange or exchange in {"NYQ","ASE"}:
        market = "NYSE"
        benchmark = "^GSPC"
    else:
        market = exchange or "Unknown"
        benchmark = "^GSPC" if not ticker.endswith(".AX") else "^AXJO"
    return {
        "market": market,
        "exchange": exchange or "Unknown",
        "benchmark": benchmark,
        "quote_type": quote_type or "Unknown",
        "currency": info.get("currency") or "Unknown",
        "timezone": info.get("exchangeTimezoneName") or "Unknown",
    }

def resolve_bare_ticker(raw: str) -> str:
    """Prefer an exact US symbol; fall back to ASX suffix for bare symbols."""
    t = normalise_ticker(raw)
    if not t or "." in t or t.startswith("^") or "/" in t or "=" in t:
        return t
    try:
        i = yf.Ticker(t).fast_info
        # Accessing last_price forces resolution in current yfinance versions.
        p = i.get("last_price")
        if p is not None:
            return t
    except Exception:
        pass
    return t + ".AX"

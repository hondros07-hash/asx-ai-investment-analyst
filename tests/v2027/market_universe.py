
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

def detect_market(ticker: str, info=None) -> dict:
    # yfinance can return dict-like objects, None, or fail upstream.
    # Never allow market detection to crash the dashboard.
    if not isinstance(info, dict):
        try:
            info = dict(info) if info is not None and hasattr(info, "items") else {}
        except Exception:
            info = {}
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
    """Resolve bare symbols without assuming they are ASX.

    Explicit .AX remains ASX. Bare symbols are first tested as US/global Yahoo
    symbols (KO, AAPL, JPM, etc). If no history exists, then try .AX.
    """
    t = normalise_ticker(raw)
    if not t or "." in t or t.startswith("^") or "/" in t or "=" in t:
        return t
    try:
        h = yf.Ticker(t).history(period="5d", interval="1d", auto_adjust=True)
        if h is not None and not h.empty:
            return t
    except Exception:
        pass
    try:
        ax = t + ".AX"
        h = yf.Ticker(ax).history(period="5d", interval="1d", auto_adjust=True)
        if h is not None and not h.empty:
            return ax
    except Exception:
        pass
    return t

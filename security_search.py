
from __future__ import annotations
import json, urllib.parse, urllib.request
import pandas as pd
import yfinance as yf
from market_universe import resolve_bare_ticker

TD="https://api.twelvedata.com"

def _json(path,params):
    url=TD+path+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"Market-Investment-Analyst/11.3"})
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def provider_search(query,api_key):
    """Provider-backed symbol/name search. Returns all matches supplied by the provider."""
    if not api_key or not query.strip(): return pd.DataFrame()
    try:
        j=_json("/symbol_search",{"symbol":query.strip(),"apikey":api_key,"outputsize":100})
        rows=j.get("data") or []
        out=[]
        for x in rows:
            out.append({
                "Symbol":x.get("symbol",""),
                "Company":x.get("instrument_name") or x.get("name") or "",
                "Exchange":x.get("exchange",""),
                "Country":x.get("country",""),
                "Currency":x.get("currency",""),
                "Type":x.get("instrument_type") or x.get("type") or "",
                "Source":"Twelve Data"
            })
        return pd.DataFrame(out)
    except Exception:
        return pd.DataFrame()

def _fallback_universe():
    from sector_peer_engine import ASX_UNIVERSE, US_UNIVERSE
    rows=[]
    for t in ASX_UNIVERSE+US_UNIVERSE:
        try:
            m=yf.Ticker(t).info
            m=m if isinstance(m,dict) else {}
        except Exception:m={}
        rows.append({
            "Symbol":t,
            "Company":m.get("longName") or m.get("shortName") or t,
            "Exchange":m.get("fullExchangeName") or m.get("exchange") or ("ASX" if t.endswith(".AX") else ""),
            "Country":m.get("country") or "",
            "Currency":m.get("currency") or "",
            "Type":m.get("quoteType") or "EQUITY",
            "Source":"Curated fallback"
        })
    return pd.DataFrame(rows)

def search_securities(query,api_key=""):
    q=query.strip()
    if not q:return pd.DataFrame()
    df=provider_search(q,api_key)
    if df.empty:
        df=_fallback_universe()
        mask=(df["Symbol"].astype(str).str.contains(q,case=False,regex=False) |
              df["Company"].astype(str).str.contains(q,case=False,regex=False))
        df=df[mask].copy()
    if df.empty:return df
    # Exact ticker/name first, then prefix, then other matches.
    uq=q.upper(); lq=q.lower()
    def score(r):
        s=str(r["Symbol"]).upper(); n=str(r["Company"]).lower()
        if s==uq:return 0
        if n==lq:return 1
        if s.startswith(uq):return 2
        if n.startswith(lq):return 3
        return 4
    df["_rank"]=df.apply(score,axis=1)
    return df.sort_values(["_rank","Exchange","Symbol"]).drop(columns="_rank").drop_duplicates(
        subset=["Symbol","Exchange"],keep="first").reset_index(drop=True)

def yahoo_identity(ticker):
    t=resolve_bare_ticker(ticker)
    try:
        m=yf.Ticker(t).info
        m=m if isinstance(m,dict) else {}
    except Exception:m={}
    return {
        "ticker":t,
        "name":m.get("longName") or m.get("shortName") or t,
        "exchange":m.get("fullExchangeName") or m.get("exchange") or "",
        "currency":m.get("currency") or "",
    }


from __future__ import annotations
import pandas as pd
import numpy as np
import yfinance as yf

# Curated seed universes. The engine also filters these using Yahoo sector/industry
# metadata, so it can work for companies beyond the examples below.
ASX_UNIVERSE = [
"QAN.AX","AIZ.AX","FLT.AX","WEB.AX","CTD.AX","SYD.AX",
"ZIP.AX","SQ2.AX","HUB.AX","NWL.AX","TYR.AX",
"BHP.AX","RIO.AX","FMG.AX","MIN.AX","S32.AX","IGO.AX",
"CBA.AX","WBC.AX","NAB.AX","ANZ.AX","MQG.AX",
"WES.AX","WOW.AX","COL.AX","JBH.AX","HVN.AX",
"CSL.AX","RMD.AX","COH.AX","SHL.AX","PME.AX",
"REA.AX","CAR.AX","SEK.AX","XRO.AX","WTC.AX","TNE.AX",
"TLS.AX","TPG.AX","ALL.AX","TCL.AX","BXB.AX","GMG.AX"
]
US_UNIVERSE = [
"AAPL","MSFT","NVDA","GOOGL","META","AMZN","TSLA","AVGO","ORCL","CRM","ADBE",
"KO","PEP","KDP","MNST","COST","WMT","TGT","MCD","SBUX",
"JPM","BAC","C","WFC","GS","MS","V","MA","AXP","PYPL",
"DAL","UAL","AAL","LUV","ALK","JBLU",
"XOM","CVX","COP","SLB","EOG",
"JNJ","PFE","MRK","LLY","ABBV","UNH",
"CAT","DE","GE","HON","UPS","FDX",
"DIS","NFLX","CMCSA","T","VZ",
"BA","LMT","RTX","NOC","GD"
]

def _safe_info(ticker):
    try:
        x=yf.Ticker(ticker).info
        return x if isinstance(x,dict) else {}
    except Exception:
        return {}

def classification(ticker, meta=None):
    meta = meta if isinstance(meta,dict) else _safe_info(ticker)
    return {
        "sector": meta.get("sector") or "Unknown",
        "industry": meta.get("industry") or "Unknown",
        "name": meta.get("longName") or meta.get("shortName") or ticker,
        "market_cap": meta.get("marketCap"),
    }

def default_benchmark(ticker, meta=None):
    if ticker.endswith(".AX"): return "^AXJO", "ASX 200"
    ex=str((meta or {}).get("exchange") or "").upper()
    if "NASDAQ" in ex or ex in {"NMS","NGM","NCM"}: return "^NDX","Nasdaq 100"
    return "^GSPC","S&P 500"

def _candidate_universe(ticker):
    return ASX_UNIVERSE if ticker.endswith(".AX") else US_UNIVERSE

def find_peers(ticker, meta=None, max_peers=8):
    """Find same-industry first, then same-sector peers from a curated liquid universe."""
    target=classification(ticker,meta)
    same_industry=[]; same_sector=[]
    for p in _candidate_universe(ticker):
        if p==ticker: continue
        m=_safe_info(p)
        if not m: continue
        row={
            "ticker":p,
            "name":m.get("shortName") or m.get("longName") or p,
            "sector":m.get("sector") or "Unknown",
            "industry":m.get("industry") or "Unknown",
            "market_cap":m.get("marketCap")
        }
        if target["industry"]!="Unknown" and row["industry"]==target["industry"]:
            same_industry.append(row)
        elif target["sector"]!="Unknown" and row["sector"]==target["sector"]:
            same_sector.append(row)
    # Prefer industry relevance, then larger/liquid sector peers.
    key=lambda x: x["market_cap"] or 0
    same_industry.sort(key=key,reverse=True)
    same_sector.sort(key=key,reverse=True)
    return (same_industry+same_sector)[:max_peers]

def period_return(ticker, period):
    try:
        h=yf.Ticker(ticker).history(period=period,auto_adjust=True)
        if h is None or len(h)<2: return np.nan
        return float(h["Close"].iloc[-1]/h["Close"].iloc[0]-1)
    except Exception: return np.nan

def latest_price(ticker):
    try:
        h=yf.Ticker(ticker).history(period="5d",auto_adjust=True)
        return float(h["Close"].iloc[-1]) if h is not None and not h.empty else np.nan
    except Exception: return np.nan

def peer_table(ticker, peers):
    rows=[]
    all_rows=[{"ticker":ticker,"name":classification(ticker)["name"]}]+peers
    for r in all_rows:
        t=r["ticker"]
        rows.append({
            "Ticker":t,"Company":r.get("name",t),"Price":latest_price(t),
            "1M":period_return(t,"1mo"),"3M":period_return(t,"3mo"),
            "6M":period_return(t,"6mo"),"1Y":period_return(t,"1y")
        })
    return pd.DataFrame(rows)

def normalized_history(tickers, period="6mo"):
    series={}
    for t in tickers:
        try:
            h=yf.Ticker(t).history(period=period,auto_adjust=True)
            if h is not None and not h.empty:
                s=h["Close"].dropna()
                series[t]=(s/s.iloc[0]-1)*100
        except Exception: pass
    if not series: return pd.DataFrame()
    df=pd.concat(series,axis=1).sort_index().ffill()
    return df

def equal_weight_peer_basket(df, target):
    peers=[c for c in df.columns if c!=target]
    return df[peers].mean(axis=1) if peers else pd.Series(dtype=float)

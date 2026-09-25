
from __future__ import annotations
import json, urllib.parse, urllib.request
import pandas as pd, numpy as np, yfinance as yf

TD="https://api.twelvedata.com"

COMMODITY_FALLBACK=[
("XAU/USD","Gold Spot","Precious Metal"),("XAG/USD","Silver Spot","Precious Metal"),
("HG1","Copper Spot","Industrial Metal"),("WTI/USD","WTI Crude Oil Spot","Energy"),
("BRENT/USD","Brent Crude Oil Spot","Energy"),("NG/USD","Natural Gas","Energy"),
]

def _json(path, params):
    url=TD+path+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"ASX-AI-Analyst/11.1"})
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def td_catalog(api_key, exchange, page=1, outputsize=100):
    if not api_key: return pd.DataFrame()
    try:
        j=_json("/stocks",{"exchange":exchange,"page":page,"outputsize":outputsize,
                            "apikey":api_key,"show_plan":"true"})
        data=j.get("data") or j.get("values") or []
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

def td_commodities(api_key, page=1, outputsize=100):
    if not api_key: return pd.DataFrame()
    try:
        j=_json("/commodities",{"page":page,"outputsize":outputsize,"apikey":api_key})
        return pd.DataFrame(j.get("data") or j.get("values") or [])
    except Exception: return pd.DataFrame()

def td_quote(api_key,symbol,exchange=None):
    if not api_key: return {}
    p={"symbol":symbol,"apikey":api_key}
    if exchange: p["exchange"]=exchange
    try:
        j=_json("/quote",p)
        return j if isinstance(j,dict) and j.get("status")!="error" else {}
    except Exception: return {}

def yahoo_quote(symbol):
    try:
        h=yf.Ticker(symbol).history(period="5d",interval="1d",auto_adjust=False)
        if h is None or h.empty:return {}
        last=h.iloc[-1]; prev=float(h["Close"].iloc[-2]) if len(h)>1 else np.nan
        close=float(last["Close"])
        return {"symbol":symbol,"close":close,"previous_close":prev,
                "change":close-prev if pd.notna(prev) else np.nan,
                "percent_change":(close/prev-1)*100 if pd.notna(prev) and prev else np.nan,
                "open":float(last["Open"]),"high":float(last["High"]),"low":float(last["Low"]),
                "volume":float(last.get("Volume",np.nan)),"datetime":str(h.index[-1])}
    except Exception:return {}

def live_rows(symbols, api_key="", exchange=None, asx_suffix=False):
    rows=[]
    for raw in symbols:
        s=str(raw).strip().upper()
        if not s: continue
        provider="Twelve Data" if api_key else "Yahoo/yfinance fallback"
        q=td_quote(api_key,s,exchange) if api_key else {}
        if not q:
            ys=s+".AX" if asx_suffix and not s.endswith(".AX") else s
            q=yahoo_quote(ys); provider="Yahoo/yfinance fallback"
        if not q: continue
        price=q.get("close",q.get("price"))
        rows.append({
          "Symbol":s,"Price":pd.to_numeric(price,errors="coerce"),
          "Change":pd.to_numeric(q.get("change"),errors="coerce"),
          "% Change":pd.to_numeric(q.get("percent_change"),errors="coerce"),
          "Open":pd.to_numeric(q.get("open"),errors="coerce"),
          "High":pd.to_numeric(q.get("high"),errors="coerce"),
          "Low":pd.to_numeric(q.get("low"),errors="coerce"),
          "Volume":pd.to_numeric(q.get("volume"),errors="coerce"),
          "Timestamp":q.get("datetime") or q.get("timestamp") or "—","Source":provider})
    return pd.DataFrame(rows)

def commodity_catalog(api_key=""):
    d=td_commodities(api_key,1,500)
    if not d.empty:return d
    return pd.DataFrame(COMMODITY_FALLBACK,columns=["symbol","name","category"])

def fallback_catalog(exchange):
    """Curated discovery fallback when a licensed/full exchange catalog is unavailable."""
    from sector_peer_engine import ASX_UNIVERSE, US_UNIVERSE
    curated={
        "ASX": [(s.replace(".AX",""),s) for s in ASX_UNIVERSE],
        "NASDAQ": [(s,s) for s in US_UNIVERSE],
        "NYSE": [("KO","Coca-Cola"),("JPM","JPMorgan Chase"),("V","Visa"),("MA","Mastercard"),
                 ("WMT","Walmart"),("DIS","Walt Disney"),("CAT","Caterpillar"),("XOM","Exxon Mobil")],
        "LSE": [("SHEL","Shell"),("AZN","AstraZeneca"),("HSBA","HSBC"),("ULVR","Unilever"),
                ("BP","BP"),("RIO","Rio Tinto"),("GSK","GSK"),("REL","RELX")],
        "HKEX": [("0700","Tencent"),("9988","Alibaba"),("3690","Meituan"),("1299","AIA"),
                 ("0005","HSBC Holdings"),("0388","HKEX"),("1810","Xiaomi"),("9618","JD.com")],
        "TSE": [("7203","Toyota"),("6758","Sony Group"),("9984","SoftBank Group"),("8306","Mitsubishi UFJ"),
                ("6861","Keyence"),("8035","Tokyo Electron"),("9432","NTT"),("7974","Nintendo")],
        "TSX": [("RY","Royal Bank of Canada"),("TD","Toronto-Dominion Bank"),("SHOP","Shopify"),
                ("ENB","Enbridge"),("CNR","Canadian National Railway"),("BNS","Bank of Nova Scotia"),
                ("CP","Canadian Pacific Kansas City"),("SU","Suncor Energy")],
    }
    rows=curated.get(exchange,[(s,s) for s in US_UNIVERSE])
    return pd.DataFrame({"symbol":[x[0] for x in rows],"name":[x[1] for x in rows],
                         "exchange":exchange,"type":"Curated fallback"})

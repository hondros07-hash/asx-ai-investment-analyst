
from __future__ import annotations
import json, urllib.parse, urllib.request
import pandas as pd, yfinance as yf

ALIASES={
 "coca cola":[("KO","The Coca-Cola Company","NYSE")],
 "coca-cola":[("KO","The Coca-Cola Company","NYSE")],
 "apple":[("AAPL","Apple Inc.","NASDAQ")],
 "qantas":[("QAN.AX","Qantas Airways Limited","ASX")],
 "zip":[("ZIP.AX","Zip Co Limited","ASX"),("ZIP","ZipRecruiter, Inc.","NYSE")],
 "bhp":[("BHP.AX","BHP Group Limited","ASX"),("BHP","BHP Group Limited","NYSE")],
}
TD="https://api.twelvedata.com"

def _json(path,params):
    url=TD+path+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"Market-Investment-Analyst/11.3.1"})
    with urllib.request.urlopen(req,timeout=15) as r:return json.loads(r.read().decode())

def _valid(t):
    try:
        h=yf.Ticker(t).history(period="5d",auto_adjust=True)
        return h is not None and not h.empty
    except:return False

def search_securities(q,key=""):
    q=q.strip()
    if not q:return pd.DataFrame()
    rows=[]
    if key:
        try:
            j=_json("/symbol_search",{"symbol":q,"apikey":key,"outputsize":100})
            for x in j.get("data",[]):
                rows.append({"Symbol":x.get("symbol",""),"Company":x.get("instrument_name") or x.get("name") or "",
                  "Exchange":x.get("exchange",""),"Country":x.get("country",""),"Currency":x.get("currency",""),"Source":"Twelve Data"})
        except:pass
    # Reliable local aliases also ensure common company-name searches work if provider search is unavailable.
    for sym,name,ex in ALIASES.get(q.lower(),[]):
        rows.append({"Symbol":sym,"Company":name,"Exchange":ex,"Country":"","Currency":"","Source":"Verified alias"})
    # Direct ticker candidate.
    uq=q.upper()
    candidates=[uq]
    if "." not in uq:candidates.append(uq+".AX")
    for t in candidates:
        if _valid(t):
            try:m=yf.Ticker(t).info or {}
            except:m={}
            rows.append({"Symbol":t,"Company":m.get("longName") or m.get("shortName") or t,
              "Exchange":m.get("fullExchangeName") or m.get("exchange") or "",
              "Country":m.get("country") or "","Currency":m.get("currency") or "","Source":"Yahoo"})
    df=pd.DataFrame(rows)
    if df.empty:return df
    return df.drop_duplicates(["Symbol","Exchange"]).reset_index(drop=True)

def resolve_listing(symbol,exchange="",country=""):
    raw=str(symbol).upper().strip(); ex=str(exchange).upper()
    candidates=[]
    if raw.endswith(".AX"): candidates=[raw]
    elif ex in {"ASX","AUSTRALIAN SECURITIES EXCHANGE","XASX"} or str(country).upper()=="AUSTRALIA":
        candidates=[raw+".AX",raw]
    else:candidates=[raw,raw.replace(".","-"),raw.replace("/","-")]
    for t in dict.fromkeys(candidates):
        if _valid(t):return t
    return candidates[0]

def identity(t):
    try:m=yf.Ticker(t).info or {}
    except:m={}
    return m.get("longName") or m.get("shortName") or t

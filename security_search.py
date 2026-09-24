
from __future__ import annotations
import json, urllib.parse, urllib.request
import pandas as pd, yfinance as yf

ALIASES={
 "coca cola":[("KO","The Coca-Cola Company","NYSE")],
 "coca-cola":[("KO","The Coca-Cola Company","NYSE")],
 "apple":[("AAPL","Apple Inc.","NASDAQ")],
 "nike":[("NKE","NIKE, Inc.","NYSE")],
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

def yahoo_search(q, limit=30):
    """Broad global company/ticker discovery using Yahoo Finance search."""
    q=str(q).strip()
    if not q:return []
    try:
        url="https://query1.finance.yahoo.com/v1/finance/search?"+urllib.parse.urlencode(
            {"q":q,"quotesCount":int(limit),"newsCount":0,"enableFuzzyQuery":"true"})
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 Market-Investment-Analyst"})
        with urllib.request.urlopen(req,timeout=10) as r:j=json.loads(r.read().decode())
        rows=[]
        for x in j.get("quotes",[]):
            qt=str(x.get("quoteType") or "").upper()
            if qt not in {"EQUITY","ETF","MUTUALFUND","INDEX"}:continue
            rows.append({"Symbol":x.get("symbol",""),
                "Company":x.get("longname") or x.get("shortname") or x.get("symbol",""),
                "Exchange":x.get("exchDisp") or x.get("exchange") or "",
                "Country":"","Currency":"","Type":qt.title(),"Source":"Yahoo Search"})
        return rows
    except Exception:return []

def _country_from_exchange(exchange, symbol=""):
    ex=str(exchange or "").upper(); sym=str(symbol or "").upper()
    if sym.endswith('.AX') or 'ASX' in ex or 'AUSTRAL' in ex: return 'Australia'
    if sym.endswith('.L') or 'LONDON' in ex or ex in {'LSE','LSEIOB'}: return 'United Kingdom'
    if sym.endswith('.T') or 'TOKYO' in ex or ex in {'JPX','TSE'}: return 'Japan'
    if sym.endswith('.HK') or 'HONG KONG' in ex or ex in {'HKG','HKEX'}: return 'Hong Kong'
    if sym.endswith('.TO') or sym.endswith('.V') or 'TORONTO' in ex or ex in {'TSX','TSXV'}: return 'Canada'
    if ex in {'NASDAQ','NYSE','NYSEARCA','AMEX','NMS','NYQ','NGM','NCM'} or 'NASDAQ' in ex or 'NYSE' in ex: return 'United States'
    return ''

def _ticker_root(symbol):
    return str(symbol or '').upper().split('.')[0].split(':')[-1]

def search_securities(q,key=""):
    """Global security resolver.

    Exact ticker roots are intentionally NOT restricted to the selected dashboard
    country. Results from Yahoo, Twelve Data and local aliases are merged, then
    ranked exact ticker -> ticker prefix -> company-name match.
    """
    q=str(q or '').strip()
    if not q:return pd.DataFrame()
    uq=q.upper(); rows=[]
    rows.extend(yahoo_search(q,50))
    if key:
        try:
            j=_json("/symbol_search",{"symbol":q,"apikey":key,"outputsize":100})
            for x in j.get("data",[]):
                rows.append({"Symbol":x.get("symbol",""),"Company":x.get("instrument_name") or x.get("name") or "",
                  "Exchange":x.get("exchange",""),"Country":x.get("country","") or "","Currency":x.get("currency","") or "",
                  "Type":x.get("instrument_type") or "Stock","Source":"Twelve Data"})
        except Exception:pass
    for sym,name,ex in ALIASES.get(q.lower(),[]):
        rows.append({"Symbol":sym,"Company":name,"Exchange":ex,"Country":_country_from_exchange(ex,sym),"Currency":"","Type":"Stock","Source":"Verified alias"})
    # Validate common exchange-qualified forms as a final discovery fallback.
    suffixes=['','.AX','.L','.T','.HK','.TO','.V']
    if '.' in uq: suffixes=['']
    for suffix in suffixes:
        t=uq+suffix
        if _valid(t):
            try:m=yf.Ticker(t).info or {}
            except Exception:m={}
            rows.append({"Symbol":t,"Company":m.get("longName") or m.get("shortName") or t,
              "Exchange":m.get("fullExchangeName") or m.get("exchange") or "",
              "Country":m.get("country") or "","Currency":m.get("currency") or "","Type":m.get("quoteType") or "Stock","Source":"Yahoo"})
    df=pd.DataFrame(rows)
    if df.empty:return df
    for c in ['Symbol','Company','Exchange','Country','Currency','Type','Source']:
        if c not in df.columns: df[c]=''
        df[c]=df[c].fillna('').astype(str)
    df.loc[df['Country'].eq(''),'Country']=[_country_from_exchange(ex,sym) for ex,sym in zip(df.loc[df['Country'].eq(''),'Exchange'],df.loc[df['Country'].eq(''),'Symbol'])]
    roots=df['Symbol'].map(_ticker_root)
    names=df['Company'].str.upper()
    df['_rank']=3
    df.loc[roots.eq(uq),'_rank']=0
    df.loc[(df['_rank']>0)&roots.str.startswith(uq),'_rank']=1
    df.loc[(df['_rank']>1)&names.str.contains(uq,regex=False),'_rank']=2
    df['_source_rank']=df['Source'].map({'Twelve Data':0,'Yahoo Search':1,'Yahoo':2,'Verified alias':3}).fillna(9)
    df=df.sort_values(['_rank','_source_rank','Country','Exchange','Symbol'])
    df=df.drop_duplicates(['Symbol','Exchange'],keep='first').reset_index(drop=True)
    return df.drop(columns=['_rank','_source_rank'])

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

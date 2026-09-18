from __future__ import annotations
from datetime import date, timedelta
import json, urllib.parse, urllib.request
import pandas as pd
from global_dividends import upcoming_dividends as yahoo_upcoming_dividends

UA={"User-Agent":"Mozilla/5.0 Chrimata/20.5.9","Accept":"application/json"}
COUNTRY={
    "Australia":"Australia","United States":"United States","United Kingdom":"United Kingdom",
    "Japan":"Japan","Hong Kong":"Hong Kong","Canada":"Canada",
}
SUFFIX={"Australia":".AX","United Kingdom":".L","Japan":".T","Hong Kong":".HK","Canada":".TO"}

def _get_json(url, timeout=12):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def _norm_symbol(s):
    return str(s or "").upper().replace("-",".").strip()

def _belongs(symbol, market, universe):
    s=_norm_symbol(symbol); u={_norm_symbol(x) for x in universe}
    if s in u:return True
    # Calendar APIs commonly omit Yahoo exchange suffixes.
    bases={x.split('.')[0] for x in u}
    if s.split('.')[0] in bases:return True
    suf=SUFFIX.get(market)
    if suf and s.endswith(suf):return True
    return market=="United States" and "." not in s and s in bases

def _twelve_calendar(market,start,end,key,universe):
    if not key:return []
    params={"apikey":key,"country":COUNTRY.get(market,market),"start_date":start.isoformat(),"end_date":end.isoformat(),"outputsize":500}
    try:j=_get_json("https://api.twelvedata.com/dividends_calendar?"+urllib.parse.urlencode(params))
    except Exception:return []
    if isinstance(j,dict) and (j.get("status")=="error" or j.get("code")):return []
    items=j if isinstance(j,list) else (j.get("data") or j.get("dividends") or []) if isinstance(j,dict) else []
    out=[]
    for x in items:
        sym=x.get("symbol")
        if not sym or not _belongs(sym,market,universe):continue
        ex=x.get("ex_date") or x.get("date")
        if not ex:continue
        out.append({"Ticker":sym,"Company":x.get("name") or sym,"Ex-Date":ex,"Record-Date":x.get("record_date") or "—","Pay-Date":x.get("payment_date") or "—","Amount":x.get("amount"),"Currency":x.get("currency") or "—","Status":"Confirmed","Source":"Twelve Data calendar"})
    return out

def _fmp_calendar(market,start,end,key,universe):
    if not key:return []
    params={"apikey":key,"from":start.isoformat(),"to":end.isoformat()}
    urls=["https://financialmodelingprep.com/stable/dividends-calendar?"+urllib.parse.urlencode(params),
          "https://financialmodelingprep.com/api/v3/stock_dividend_calendar?"+urllib.parse.urlencode(params)]
    items=[]
    for url in urls:
        try:
            j=_get_json(url)
            if isinstance(j,list):items=j;break
        except Exception:pass
    out=[]
    for x in items:
        sym=x.get("symbol")
        if not sym or not _belongs(sym,market,universe):continue
        ex=x.get("date") or x.get("exDate")
        if not ex:continue
        out.append({"Ticker":sym,"Company":x.get("name") or sym,"Ex-Date":ex,"Record-Date":x.get("recordDate") or "—","Pay-Date":x.get("paymentDate") or "—","Amount":x.get("dividend") if x.get("dividend") is not None else x.get("adjDividend"),"Currency":x.get("currency") or "—","Status":"Confirmed","Source":"FMP calendar"})
    return out

def corporate_actions_calendar(market, universe, horizon_days=120, twelve_data_key="", fmp_key=""):
    """Confirmed forward dividend calendar with provider hierarchy.

    Priority: Twelve Data forward dividends calendar -> Financial Modeling Prep
    forward calendar -> per-security Yahoo declared-calendar fallback. Historical
    patterns are never projected as future corporate actions.
    """
    start=date.today(); end=start+timedelta(days=horizon_days)
    rows=[]
    rows.extend(_twelve_calendar(market,start,end,twelve_data_key,universe))
    rows.extend(_fmp_calendar(market,start,end,fmp_key,universe))
    # Yahoo remains a fallback/supplement for the configured local universe.
    try:
        y=yahoo_upcoming_dividends(tuple(universe),horizon_days)
        if y is not None and not y.empty:
            for _,x in y.iterrows():
                rows.append({"Ticker":x.get("Ticker"),"Company":x.get("Company"),"Ex-Date":x.get("Ex-Date"),"Record-Date":"—","Pay-Date":x.get("Pay-Date","—"),"Amount":x.get("Amount"),"Currency":"—","Status":"Confirmed","Source":x.get("Source","Yahoo declared calendar")})
    except Exception:pass
    df=pd.DataFrame(rows)
    if df.empty:return df
    df["_date"]=pd.to_datetime(df["Ex-Date"],errors="coerce")
    df=df[df["_date"].notna() & (df["_date"].dt.date>=start) & (df["_date"].dt.date<=end)]
    df=df.sort_values(["_date","Ticker","Source"]).drop_duplicates(["Ticker","Ex-Date"],keep="first")
    return df.drop(columns=["_date"]).reset_index(drop=True)

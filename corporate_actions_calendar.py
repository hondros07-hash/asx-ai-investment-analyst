from __future__ import annotations
from datetime import date, timedelta
import json, urllib.parse, urllib.request
import pandas as pd
from global_dividends import upcoming_dividends as yahoo_upcoming_dividends

UA={"User-Agent":"Mozilla/5.0 Chrimata/20.6.0","Accept":"application/json"}
COUNTRY_ALIASES={
    "Australia":["AU","Australia"],
    "United States":["US","United States"],
    "United Kingdom":["GB","United Kingdom"],
    "Japan":["JP","Japan"],
    "Hong Kong":["HK","Hong Kong"],
    "Canada":["CA","Canada"],
}
MIC_CODES={
    "Australia":{"XASX","CXAC"},
    "United States":{"XNAS","XNGS","XNMS","XNYS","XASE","ARCX","BATS"},
    "United Kingdom":{"XLON"},"Japan":{"XTKS"},"Hong Kong":{"XHKG"},"Canada":{"XTSE","XTSX"},
}
EXCHANGES={
    "Australia":{"ASX","CBOE AUSTRALIA"},
    "United States":{"NASDAQ","NYSE","AMEX","NYSE ARCA","CBOE"},
    "United Kingdom":{"LSE","LONDON STOCK EXCHANGE"},"Japan":{"TSE","JPX"},
    "Hong Kong":{"HKEX","HONG KONG STOCK EXCHANGE"},"Canada":{"TSX","TSXV"},
}
SUFFIX={"Australia":".AX","United Kingdom":".L","Japan":".T","Hong Kong":".HK","Canada":".TO"}

def _get_json(url, timeout=12):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def _norm_symbol(s):
    return str(s or "").upper().replace("-",".").strip()

def _bases(universe):
    return {_norm_symbol(x).split('.')[0] for x in universe}

def _belongs(symbol, market, universe, mic_code="", exchange=""):
    s=_norm_symbol(symbol); u={_norm_symbol(x) for x in universe}; bases=_bases(universe)
    if s in u or s.split('.')[0] in bases:return True
    suf=SUFFIX.get(market)
    if suf and s.endswith(suf) and s[:-len(suf)].split('.')[0] in bases:return True
    # Some calendar feeds return exchange-qualified symbols differently.  Only
    # accept those when the exchange itself belongs to the selected market AND
    # the base ticker is in Chrímata's configured universe.
    mic=str(mic_code or '').upper(); exch=str(exchange or '').upper()
    return s.split('.')[0] in bases and (mic in MIC_CODES.get(market,set()) or exch in EXCHANGES.get(market,set()))

def _calendar_items(j):
    if isinstance(j,list):return j
    if not isinstance(j,dict):return []
    if j.get("status")=="error" or (j.get("code") and not j.get("data")):return []
    for key in ("data","dividends","values","result"):
        v=j.get(key)
        if isinstance(v,list):return v
        if isinstance(v,dict):
            for k2 in ("data","list","dividends","values"):
                if isinstance(v.get(k2),list):return v[k2]
    return []

def _row(x, source):
    sym=x.get("symbol") or x.get("ticker")
    ex=x.get("ex_date") or x.get("exDate") or x.get("date")
    if not sym or not ex:return None
    return {"Ticker":sym,"Company":x.get("name") or sym,"Ex-Date":ex,
            "Record-Date":x.get("record_date") or x.get("recordDate") or "—",
            "Pay-Date":x.get("payment_date") or x.get("paymentDate") or "—",
            "Amount":x.get("amount") if x.get("amount") is not None else (x.get("dividend") if x.get("dividend") is not None else x.get("adjDividend")),
            "Currency":x.get("currency") or "—","Status":"Confirmed","Source":source}

def _twelve_calendar(market,start,end,key,universe):
    if not key:return []
    base={"apikey":key,"start_date":start.isoformat(),"end_date":end.isoformat(),"outputsize":500}
    out=[]
    # V20.6.0: try both ISO alpha-2 and provider country names. Australia and
    # US were the two markets observed returning empty country-filtered payloads.
    for country in COUNTRY_ALIASES.get(market,[market]):
        params=dict(base,country=country)
        try:j=_get_json("https://api.twelvedata.com/dividends_calendar?"+urllib.parse.urlencode(params))
        except Exception:continue
        for x in _calendar_items(j):
            if _belongs(x.get("symbol"),market,universe,x.get("mic_code"),x.get("exchange")):
                r=_row(x,"Twelve Data calendar")
                if r:out.append(r)
        if out:break
    # Final calendar-level fallback: request the date range without a country
    # filter and keep only the configured universe. This avoids silently losing
    # AU/US events when a provider's country vocabulary changes.
    if not out:
        try:j=_get_json("https://api.twelvedata.com/dividends_calendar?"+urllib.parse.urlencode(base))
        except Exception:j=[]
        for x in _calendar_items(j):
            if _belongs(x.get("symbol"),market,universe,x.get("mic_code"),x.get("exchange")):
                r=_row(x,"Twelve Data calendar")
                if r:out.append(r)
    return out

def _twelve_next_per_security(market,start,end,key,universe):
    """Last-resort declared-event lookup using /dividends?range=next.

    This is intentionally only called when the calendar endpoint returned no
    selected-market rows, avoiding unnecessary API usage.
    """
    if not key:return []
    out=[]
    exchange_hint={"Australia":"ASX","United Kingdom":"LSE","Japan":"TSE","Hong Kong":"HKEX","Canada":"TSX"}.get(market)
    for raw in universe:
        base_symbol=_norm_symbol(raw).split('.')[0]
        params={"apikey":key,"symbol":base_symbol,"range":"next"}
        if exchange_hint:params["exchange"]=exchange_hint
        if market in COUNTRY_ALIASES:params["country"]=COUNTRY_ALIASES[market][0]
        try:j=_get_json("https://api.twelvedata.com/dividends?"+urllib.parse.urlencode(params),timeout=8)
        except Exception:continue
        meta=j.get("meta",{}) if isinstance(j,dict) else {}
        vals=j.get("dividends",[]) if isinstance(j,dict) else []
        for x in vals if isinstance(vals,list) else []:
            ex=x.get("ex_date") or x.get("date")
            try:d=pd.to_datetime(ex,errors="coerce").date()
            except Exception:continue
            if not ex or d<start or d>end:continue
            y=dict(x); y["symbol"]=meta.get("symbol") or base_symbol; y["name"]=meta.get("name") or y["symbol"]; y["currency"]=meta.get("currency")
            r=_row(y,"Twelve Data next dividend")
            if r:out.append(r)
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
        if not _belongs(x.get("symbol"),market,universe,x.get("mic_code"),x.get("exchange")):continue
        r=_row(x,"FMP calendar")
        if r:out.append(r)
    return out

def corporate_actions_calendar(market, universe, horizon_days=120, twelve_data_key="", fmp_key=""):
    """Confirmed forward dividend calendar with resilient global fallbacks."""
    start=date.today(); end=start+timedelta(days=horizon_days)
    rows=[]
    td=_twelve_calendar(market,start,end,twelve_data_key,universe); rows.extend(td)
    rows.extend(_fmp_calendar(market,start,end,fmp_key,universe))
    try:
        y=yahoo_upcoming_dividends(tuple(universe),horizon_days)
        if y is not None and not y.empty:
            for _,x in y.iterrows():
                rows.append({"Ticker":x.get("Ticker"),"Company":x.get("Company"),"Ex-Date":x.get("Ex-Date"),"Record-Date":"—","Pay-Date":x.get("Pay-Date","—"),"Amount":x.get("Amount"),"Currency":"—","Status":"Confirmed","Source":x.get("Source","Yahoo declared calendar")})
    except Exception:pass
    # AU/US hardening: if all calendar/fallback sources are still empty, ask
    # Twelve Data for each configured security's next declared dividend.
    if not rows and market in {"Australia","United States"}:
        rows.extend(_twelve_next_per_security(market,start,end,twelve_data_key,universe))
    df=pd.DataFrame(rows)
    if df.empty:return df
    df["_date"]=pd.to_datetime(df["Ex-Date"],errors="coerce")
    df=df[df["_date"].notna() & (df["_date"].dt.date>=start) & (df["_date"].dt.date<=end)]
    df=df.sort_values(["_date","Ticker","Source"]).drop_duplicates(["Ticker","Ex-Date"],keep="first")
    return df.drop(columns=["_date"]).reset_index(drop=True)

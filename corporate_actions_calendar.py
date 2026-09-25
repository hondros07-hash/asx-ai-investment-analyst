from __future__ import annotations
from datetime import date, timedelta
import json, urllib.parse, urllib.request
import pandas as pd
from global_dividends import upcoming_dividends as yahoo_upcoming_dividends

UA={"User-Agent":"Mozilla/5.0 Chrimata/20.6.2","Accept":"application/json"}
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

def _venue_belongs(market, mic_code="", exchange=""):
    """Market-wide venue test; deliberately does NOT depend on dashboard universe."""
    mic=str(mic_code or "").upper().strip()
    exch=str(exchange or "").upper().strip()
    if mic and mic in MIC_CODES.get(market,set()): return True
    if exch and exch in EXCHANGES.get(market,set()): return True
    # Provider venue labels vary (e.g. NASDAQ Capital Market, ASX).
    return any(x and (x in exch or exch in x) for x in EXCHANGES.get(market,set()))

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
             "Currency":x.get("currency") or "—",
            "Type":x.get("type") or x.get("dividend_type") or x.get("dividendType") or "—",
            "Franking":x.get("franking") or x.get("franking_percentage") or x.get("frankingPercentage") or "N/A",
            "Status":"Confirmed","Source":source,"Verified":True}

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
        # Country-filtered calendar is already market-wide. Do NOT filter it
        # through Chrímata's small dashboard universe; that was the AU/US bug.
        for x in _calendar_items(j):
            r=_row(x,"Twelve Data calendar")
            if r:out.append(r)
        if out:break
    # V20.6.2: AU/US venue-specific repair. Some provider responses are more
    # reliable by MIC/exchange than by country. Query the actual venues directly.
    if not out and market in {"Australia","United States"}:
        venue_params=[]
        for mic in sorted(MIC_CODES.get(market,set())):
            venue_params.append(dict(base,mic_code=mic))
        for exch in sorted(EXCHANGES.get(market,set())):
            venue_params.append(dict(base,exchange=exch))
        for params in venue_params:
            try:j=_get_json("https://api.twelvedata.com/dividends_calendar?"+urllib.parse.urlencode(params))
            except Exception:continue
            for x in _calendar_items(j):
                if _venue_belongs(market,x.get("mic_code"),x.get("exchange")):
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
            if _venue_belongs(market,x.get("mic_code"),x.get("exchange")):
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


def _empty_calendar(status, market, diagnostics):
    cols=["Ticker","Company","Ex-Date","Record-Date","Pay-Date","Amount","Currency","Type","Franking","Status","Source","Verified"]
    df=pd.DataFrame(columns=cols)
    df.attrs.update({"status":status,"market":market,"diagnostics":diagnostics,"provider_success":False})
    return df

def _normalize_final(df, market, start, end, diagnostics):
    if df is None or df.empty:
        attempted=diagnostics.get("attempted",[])
        configured=diagnostics.get("configured",[])
        status="NO_CONFIRMED_EVENTS" if configured else "PROVIDERS_NOT_CONFIGURED"
        return _empty_calendar(status,market,diagnostics)
    for c,default in [("Record-Date","—"),("Pay-Date","—"),("Amount",None),("Currency","—"),
                      ("Type","—"),("Franking","N/A"),("Status","Confirmed"),("Source","—"),("Verified",True)]:
        if c not in df.columns: df[c]=default
    df["_date"]=pd.to_datetime(df["Ex-Date"],errors="coerce")
    df=df[df["_date"].notna() & (df["_date"].dt.date>=start) & (df["_date"].dt.date<=end)].copy()
    if df.empty:return _empty_calendar("NO_CONFIRMED_EVENTS",market,diagnostics)
    df["Ticker"]=df["Ticker"].astype(str).str.strip()
    df["Company"]=df["Company"].fillna(df["Ticker"]).astype(str).str.strip()
    df=df.sort_values(["_date","Ticker","Source"]).drop_duplicates(["Ticker","Ex-Date"],keep="first")
    df=df.drop(columns=["_date"]).reset_index(drop=True)
    df.attrs.update({"status":"SUCCESS","market":market,"diagnostics":diagnostics,
                     "provider_success":True,"row_count":len(df)})
    return df

class DividendCorporateActionBroker:
    """Provider-neutral confirmed-dividend broker.

    No historical dividend is projected forward. Market-wide structured calendars
    are preferred; exchange-qualified Yahoo declared events are a fallback.
    """
    def fetch(self, market, universe, horizon_days=120, twelve_data_key="", fmp_key=""):
        start=date.today(); end=start+timedelta(days=horizon_days)
        universe=tuple(dict.fromkeys(str(x).strip() for x in universe if str(x).strip()))
        diagnostics={"attempted":[],"configured":[],"market":market,"universe_size":len(universe)}
        rows=[]

        if twelve_data_key:
            diagnostics["configured"].append("Twelve Data")
            diagnostics["attempted"].append("Twelve Data market calendar")
            td=_twelve_calendar(market,start,end,twelve_data_key,universe)
            rows.extend(td)
            if not td:
                diagnostics["attempted"].append("Twelve Data next-dividend security fallback")
                rows.extend(_twelve_next_per_security(market,start,end,twelve_data_key,universe))

        if fmp_key:
            diagnostics["configured"].append("FMP")
            diagnostics["attempted"].append("FMP dividend calendar")
            rows.extend(_fmp_calendar(market,start,end,fmp_key,universe))

        # Yahoo is always a declared-event fallback. It is not treated as a
        # market-wide calendar and cannot prove that a market has no events.
        diagnostics["configured"].append("Yahoo declared events")
        diagnostics["attempted"].append("Yahoo calendar + corporate-action events")
        try:
            y=yahoo_upcoming_dividends(universe,horizon_days)
            if y is not None and not y.empty:
                for _,x in y.iterrows():
                    rows.append({"Ticker":x.get("Ticker"),"Company":x.get("Company"),
                      "Ex-Date":x.get("Ex-Date"),"Record-Date":"—","Pay-Date":x.get("Pay-Date","—"),
                      "Amount":x.get("Amount"),"Currency":"—","Type":"—","Franking":"N/A",
                      "Status":"Confirmed","Source":x.get("Source","Yahoo declared calendar"),"Verified":True})
        except Exception as exc:
            diagnostics["yahoo_error"]=type(exc).__name__

        return _normalize_final(pd.DataFrame(rows),market,start,end,diagnostics)

_DIVIDEND_BROKER=DividendCorporateActionBroker()

def corporate_actions_calendar(market, universe, horizon_days=120, twelve_data_key="", fmp_key=""):
    """V23.4.3 confirmed forward dividend calendar with provider diagnostics."""
    return _DIVIDEND_BROKER.fetch(market, universe, horizon_days, twelve_data_key, fmp_key)

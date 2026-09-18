from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json, urllib.parse, urllib.request
import pandas as pd
import yfinance as yf

UA={"User-Agent":"Mozilla/5.0 Chrimata/20.5.8"}

def _dt(value):
    if value is None or value is False or value=="": return pd.NaT
    try:
        if isinstance(value,(int,float)) and value>0:
            # Yahoo timestamps are seconds; tolerate milliseconds too.
            unit="ms" if value>10_000_000_000 else "s"
            return pd.to_datetime(value,unit=unit,utc=True,errors="coerce")
        return pd.to_datetime(value,utc=True,errors="coerce")
    except Exception:return pd.NaT

def _calendar_value(cal, keys):
    if not isinstance(cal,dict): return None
    low={str(k).lower().replace(" ","").replace("-",""):v for k,v in cal.items()}
    for k in keys:
        v=low.get(k.lower().replace(" ","").replace("-",""))
        if isinstance(v,(list,tuple)) and v:v=v[0]
        if v is not None:return v
    return None

def _chart_declared_dividends(ticker, start, end):
    """Yahoo chart corporate-action feed. It can expose declared future dividends."""
    try:
        p1=int(start.timestamp()); p2=int(end.timestamp())
        url=("https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(ticker,safe="")+
             "?"+urllib.parse.urlencode({"period1":p1,"period2":p2,"interval":"1d","events":"div","includeAdjustedClose":"true"}))
        req=urllib.request.Request(url,headers=UA)
        with urllib.request.urlopen(req,timeout=8) as r:j=json.loads(r.read().decode())
        result=((j.get("chart") or {}).get("result") or [None])[0] or {}
        divs=((result.get("events") or {}).get("dividends") or {})
        out=[]
        for ev in divs.values():
            dt=_dt(ev.get("date"))
            if pd.notna(dt) and start<=dt<=end:
                out.append((dt,ev.get("amount")))
        return out
    except Exception:return []

def upcoming_dividends(tickers, horizon_days=365):
    """Declared upcoming dividends for the supplied exchange-qualified universe.

    Uses independent Yahoo sources in order: calendar, quote metadata, then the
    chart corporate-action event feed. No future dividend is estimated from
    historical payment patterns.
    """
    now=pd.Timestamp.now(tz="UTC").normalize(); end=now+pd.Timedelta(days=horizon_days)
    rows=[]
    for ticker in dict.fromkeys(str(x).strip() for x in tickers if str(x).strip()):
        try:
            tk=yf.Ticker(ticker)
            try: cal=tk.calendar or {}
            except Exception: cal={}
            try: meta=tk.info or {}
            except Exception: meta={}
            name=meta.get("longName") or meta.get("shortName") or ticker
            ex=_dt(_calendar_value(cal,["Ex-Dividend Date","ExDividendDate"]))
            if pd.isna(ex): ex=_dt(meta.get("exDividendDate"))
            pay=_dt(_calendar_value(cal,["Dividend Date","DividendDate","Payment Date","Pay Date"]))
            if pd.isna(pay): pay=_dt(meta.get("dividendDate"))
            amount=meta.get("lastDividendValue")
            if amount is None: amount=meta.get("dividendRate")
            if pd.notna(ex) and now-pd.Timedelta(days=1)<=ex<=end:
                rows.append({"Ticker":ticker,"Company":name,"Ex-Date":ex.date().isoformat(),
                             "Pay-Date":pay.date().isoformat() if pd.notna(pay) else "—",
                             "Amount":amount,"Source":"Yahoo declared calendar"})
                continue
            # Independent corporate-action fallback, especially useful outside US listings.
            events=_chart_declared_dividends(ticker,now.to_pydatetime(),end.to_pydatetime())
            for edt,eamt in events:
                rows.append({"Ticker":ticker,"Company":name,"Ex-Date":edt.date().isoformat(),
                             "Pay-Date":pay.date().isoformat() if pd.notna(pay) and pay>=edt else "—",
                             "Amount":eamt,"Source":"Yahoo corporate action"})
        except Exception:continue
    df=pd.DataFrame(rows)
    if df.empty:return df
    df=df.drop_duplicates(["Ticker","Ex-Date"],keep="first")
    return df.sort_values(["Ex-Date","Ticker"]).reset_index(drop=True)

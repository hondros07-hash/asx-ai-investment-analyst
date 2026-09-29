"""AXÍA shared AU/NZ dividend calendar presentation and evidence normalization.

Payment-date window: today through 90 days. A provider event is NOT official
exchange-filing verification. Unknown payment dates are excluded, not guessed.
"""
from datetime import date, timedelta
import pandas as pd

SUFFIX={"Australia":".AX","New Zealand":".NZ"}
COLUMNS=["Ticker","Company","Ex-Date","Record-Date","Pay-Date","Amount","Currency","Type","Franking","Source","Evidence status","Source URL"]


def normalize_dividends(raw, country, today=None, days=90):
    today=today or date.today()
    end=today+timedelta(days=days)
    if country not in SUFFIX: raise ValueError("Unsupported dividend market")
    if raw is None or raw.empty: return pd.DataFrame(columns=COLUMNS)
    rows=[]
    for _,item in raw.iterrows():
        ticker=str(item.get("Ticker") or "").strip().upper()
        if not ticker.endswith(SUFFIX[country]): continue
        pay=pd.to_datetime(item.get("Pay-Date"),errors="coerce")
        ex=pd.to_datetime(item.get("Ex-Date"),errors="coerce")
        if pd.isna(pay) or pd.isna(ex): continue
        if not today<=pay.date()<=end: continue
        source=str(item.get("Source") or "Provider calendar")
        # A provider's 'Verified' flag does not prove reconciliation to an issuer filing.
        rows.append({"Ticker":ticker,"Company":str(item.get("Company") or ticker),
            "Ex-Date":ex.date().isoformat(),"Record-Date":str(item.get("Record-Date") or "—"),
            "Pay-Date":pay.date().isoformat(),"Amount":item.get("Amount"),
            "Currency":str(item.get("Currency") or "—"),"Type":str(item.get("Type") or "—"),
            "Franking":str(item.get("Franking") or "N/A") if country=="Australia" else "N/A",
            "Source":source,"Evidence status":"Provider-reported · official filing not reconciled",
            "Source URL":str(item.get("Source URL") or "")})
    df=pd.DataFrame(rows,columns=COLUMNS)
    if df.empty:return df
    return df.drop_duplicates(["Ticker","Ex-Date","Pay-Date"]).sort_values(["Pay-Date","Ticker"]).reset_index(drop=True)


def top_five(calendar):
    return calendar.head(5).copy()


def source_link(row):
    url=str(row.get("Source URL") or "").strip()
    return url if url.startswith(("https://","http://")) else None

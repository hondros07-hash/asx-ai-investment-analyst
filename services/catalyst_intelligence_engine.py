"""AXÍA V23.8.2 — evidence-first catalyst registry and preview.

Pure Python: accepts existing calendar rows and independently sourced candidate
events. It does not fabricate calendar dates, predict price moves or fetch
unlicensed feeds. Provider adapters can be added without coupling to Streamlit.
"""
from __future__ import annotations
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import urlparse
import pandas as pd

CATEGORIES = {"financial","corporate","regulatory","strategic","economic","industry","shareholder"}
STATUSES = {"confirmed","estimated","potential","completed"}
def _value(row, *keys):
    for key in keys:
        value=row.get(key)
        if value is not None and str(value).strip().lower() not in ("","nan","none","nat"):
            return value
    return None

def _date(value):
    if value is None or str(value).strip().upper() in ("TBD","UNKNOWN",""):
        return None
    parsed=pd.to_datetime(value,utc=True,errors="coerce")
    return None if pd.isna(parsed) else parsed

def normalize_event(row, ticker, now=None):
    row=dict(row)
    name=str(_value(row,"event","Event","title","Title") or "").strip()
    if not name: return None
    symbol=str(_value(row,"ticker","Ticker") or ticker).upper().strip()
    if symbol!=str(ticker).upper().strip(): return None
    source=str(_value(row,"source","Source") or "User calendar").strip()
    url=str(_value(row,"source_url","url","URL") or "").strip()
    if url and urlparse(url).scheme not in ("https","http"): url=""
    date=_date(_value(row,"event_date","date","Date"))
    evidence=str(_value(row,"evidence_status","date_status","date_confidence") or "").lower().strip()
    official=bool(url and any(urlparse(url).hostname == host or (urlparse(url).hostname or "").endswith("."+host) for host in ("asx.com.au","sec.gov","rba.gov.au","federalreserve.gov")))
    # Official-looking links are provenance hints, not proof of the date.
    status=evidence if evidence in STATUSES else "potential"
    if status=="confirmed" and not (date is not None and bool(_value(row,"source_published_at","verified_at")) and url):
        status="estimated" if date is not None else "potential"
    if status=="estimated" and date is None: status="potential"
    now=now or datetime.now(timezone.utc)
    if status=="completed" and not _value(row,"outcome_source","outcome_url"):
        status="potential" if date is None else "estimated"
    category=str(_value(row,"category","Category") or "corporate").lower()
    if category not in CATEGORIES: category="corporate"
    previous=_date(_value(row,"previous_date","previous_event_date"))
    return {"ticker":symbol,"event":name,"event_date":date,"date_status":status,
            "category":category,"scope":str(_value(row,"scope") or "corporate").lower(),
            "source":source,"source_url":url,"source_published_at":_value(row,"source_published_at"),
            "previous_date":previous,"date_revised":bool(previous is not None and date is not None and previous!=date),
            "impact_context":"Historical event moves are not a forecast.",
            "outcome":_value(row,"outcome"),"outcome_source":_value(row,"outcome_source","outcome_url"),
            "thesis_kpi":_value(row,"thesis_kpi"),"official_domain":official}

def build_catalyst_preview(ticker, stored_rows=None, discovered_rows=None, now=None, limit=5):
    now=now or datetime.now(timezone.utc)
    candidates=[]
    for origin,rows in (("stored",stored_rows),("discovered",discovered_rows)):
        if rows is None: continue
        iterable=rows.to_dict("records") if isinstance(rows,pd.DataFrame) else rows
        for raw in iterable:
            event=normalize_event(raw,ticker,now)
            if event:
                event["origin"]=origin
                candidates.append(event)
    upcoming=[]
    for event in candidates:
        dt=event["event_date"]
        if event["date_status"]=="completed" or (dt is not None and dt.to_pydatetime()<now):
            continue
        duplicate=next((x for x in upcoming if x["event_date"]==dt and
            SequenceMatcher(None,x["event"].casefold(),event["event"].casefold()).ratio()>=.85),None)
        if duplicate:
            if event["date_status"]=="confirmed" and duplicate["date_status"]!="confirmed":
                upcoming[upcoming.index(duplicate)]=event
            continue
        upcoming.append(event)
    upcoming.sort(key=lambda x:(x["event_date"] is None,
                  x["event_date"] if x["event_date"] is not None else pd.Timestamp.max.tz_localize("UTC")))
    return upcoming[:max(1,min(int(limit),5))]

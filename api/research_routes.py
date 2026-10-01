"""Read-only research endpoints for the V24.1 Command Centre migration.

These endpoints do not create user thesis rules or catalysts. Those require
authenticated persistent storage in a later migration stage.
"""
from __future__ import annotations
from datetime import datetime, timezone
from math import isfinite
from urllib.request import Request, urlopen
import json
import os
import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException, Query
from services.technical_engine import calculate_technical_snapshot, core_indicator_frame

router = APIRouter(prefix="/v1/companies", tags=["company-research"])


def _ticker(value):
    value = value.strip().upper()
    if not value or len(value)>24 or not all(c.isalnum() or c in ".^=-_" for c in value):
        raise HTTPException(422, "Invalid ticker")
    return value


def _clean(value):
    import numpy as np
    if isinstance(value, dict):
        return {str(k):_clean(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (np.integer,)):return int(value)
    if isinstance(value, (float,np.floating)):return float(value) if isfinite(value) else None
    if isinstance(value, (pd.Timestamp,datetime)):return value.isoformat()
    if value is pd.NaT:return None
    return value


def _provider(fn):
    # Reuse the bounded provider pool/timeout from the existing API.
    from api.main import _provider as bounded
    return bounded(fn)


def _history(ticker):
    return _provider(lambda: yf.Ticker(ticker).history(period="2y",interval="1d",auto_adjust=True))


@router.get("/{ticker}/technical")
def technical(ticker: str):
    ticker=_ticker(ticker)
    history=_history(ticker)
    result=calculate_technical_snapshot(history)
    return {"ticker":ticker,"data":_clean(result),"source":"Yahoo Finance adjusted daily price history",
            "checked_at":datetime.now(timezone.utc).isoformat(),"issuer_reconciled":False}


@router.get("/{ticker}/quant")
def quant(ticker: str):
    ticker=_ticker(ticker)
    frame=core_indicator_frame(_history(ticker))
    if frame.empty:return {"ticker":ticker,"status":"pending","metrics":{},"source":"Yahoo Finance adjusted daily price history"}
    last=frame.iloc[-1]
    return {"ticker":ticker,"status":"available","metrics":_clean({k:float(v) if pd.notna(v) else None for k,v in last.items()}),
            "source":"Yahoo Finance adjusted daily price history","calculation":"deterministic_python",
            "checked_at":datetime.now(timezone.utc).isoformat()}


@router.get("/{ticker}/news")
def news(ticker: str, limit: int=Query(10,ge=1,le=20)):
    ticker=_ticker(ticker)
    rows=_provider(lambda: yf.Ticker(ticker).news or [])
    articles=[]
    for item in rows[:limit]:
        data=item.get("content") or item
        link=(data.get("canonicalUrl") or data.get("clickThroughUrl") or {})
        url=link.get("url") if isinstance(link,dict) else link
        if not isinstance(url,str) or not url.startswith(("https://","http://")):continue
        articles.append({"title":data.get("title") or "Untitled","url":url,
                         "published_at":data.get("pubDate") or item.get("providerPublishTime"),
                         "publisher":(data.get("provider") or {}).get("displayName") if isinstance(data.get("provider"),dict) else item.get("publisher")})
    return {"ticker":ticker,"articles":articles,"source":"Yahoo Finance news feed",
            "checked_at":datetime.now(timezone.utc).isoformat()}


@router.get("/{ticker}/catalysts")
def catalysts(ticker: str):
    ticker=_ticker(ticker)
    calendar=_provider(lambda: yf.Ticker(ticker).calendar)
    if not isinstance(calendar,dict):calendar={}
    events=[]
    for label,value in calendar.items():
        if isinstance(value,(list,tuple)):
            for date in value:
                if isinstance(date,(datetime,pd.Timestamp)):
                    events.append({"event":str(label),"date":date.isoformat(),"status":"Provider estimate / verify"})
        elif isinstance(value,(datetime,pd.Timestamp)):
            events.append({"event":str(label),"date":value.isoformat(),"status":"Provider estimate / verify"})
    return {"ticker":ticker,"events":events,"source":"Yahoo Finance company calendar",
            "checked_at":datetime.now(timezone.utc).isoformat(),"user_events_migrated":False}


@router.get("/{ticker}/announcements")
def announcements(ticker: str):
    ticker=_ticker(ticker)
    # Only US listings with an issuer CIK can be resolved through SEC submissions.
    if ticker.endswith((".AX",".L",".HK",".T",".TO",".V")):
        return {"ticker":ticker,"status":"unavailable","filings":[],"source":None,
                "message":"An official exchange filing connector is not yet configured for this listing."}
    user_agent=os.getenv("AXIA_SEC_USER_AGENT","").strip()
    if not user_agent:
        return {"ticker":ticker,"status":"unavailable","filings":[],"source":"SEC EDGAR",
                "message":"Configure AXIA_SEC_USER_AGENT with a real application name and contact before SEC retrieval."}

    # Resolve US issuer identity from the SEC's official ticker directory.
    def fetch_ticker_directory():
        req=Request("https://www.sec.gov/files/company_tickers.json",
                    headers={"User-Agent":user_agent,"Accept":"application/json"})
        with urlopen(req,timeout=12) as response:return json.load(response)

    ticker_directory=_provider(fetch_ticker_directory)
    matches=[
        entry for entry in ticker_directory.values()
        if str(entry.get("ticker","")).upper()==ticker
    ] if isinstance(ticker_directory,dict) else []

    if len(matches)!=1:
        return {"ticker":ticker,"status":"unavailable","filings":[],"source":"SEC EDGAR",
                "message":"Issuer identity could not be uniquely verified through the SEC ticker directory."}

    try:cik=int(matches[0].get("cik_str"))
    except (TypeError,ValueError):
        return {"ticker":ticker,"status":"unavailable","filings":[],"source":"SEC EDGAR",
                "message":"Issuer CIK not verified; SEC filings cannot be matched safely."}


    def fetch():
        req=Request(f"https://data.sec.gov/submissions/CIK{cik:010d}.json",
                    headers={"User-Agent":user_agent,"Accept":"application/json"})
        with urlopen(req,timeout=12) as response:return json.load(response)
    filing_data=_provider(fetch)

    # Fail closed unless the SEC submissions record reconciles to the
    # ticker-directory identity resolved above.
    try:
        returned_cik=int(filing_data.get("cik"))
    except (TypeError,ValueError):
        returned_cik=None

    returned_tickers=[
        str(value).upper()
        for value in (filing_data.get("tickers") or [])
    ]

    if returned_cik!=cik or ticker not in returned_tickers:
        return {"ticker":ticker,"status":"unavailable","filings":[],"source":"SEC EDGAR",
                "message":"SEC submissions identity did not reconcile with the verified issuer."}

    recent=(filing_data.get("filings") or {}).get("recent") or {}
    fields=("accessionNumber","form","filingDate","primaryDocument","primaryDocDescription")
    rows=[dict(zip(fields,values)) for values in zip(*(recent.get(field,[]) for field in fields))]
    filings=[]
    for row in rows[:30]:
        accession=row["accessionNumber"]
        document=row["primaryDocument"]
        if not accession or not document:continue
        filings.append({"form":row["form"],"date":row["filingDate"],"description":row["primaryDocDescription"],
                        "url":f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-','')}/{document}"})
    return {"ticker":ticker,"status":"available","filings":filings,"source":"SEC EDGAR submissions",
            "issuer":filing_data.get("name"),"checked_at":datetime.now(timezone.utc).isoformat()}


@router.get("/{ticker}/report-intelligence")
def report_intelligence(ticker: str):
    result=announcements(ticker)
    return {**result,"analysis_status":"not_migrated",
            "message":"Official filing links are provided when verified. AI extraction and document analysis are not yet connected."}


@router.get("/{ticker}/thesis")
def thesis(ticker: str):
    ticker=_ticker(ticker)
    from api.main import _snapshot
    data=_snapshot(ticker,"Annual (5Y)")
    # No user-configured thresholds are assumed. Return verified provider context,
    # leaving personal thesis condition evaluation pending.
    return {"ticker":ticker,"status":"pending_user_conditions",
            "integrity":_clean(data.get("integrity") or {}),
            "provider":data.get("provider"),"checked_at":data.get("provider_checked_at"),
            "conditions":[],"message":"User-authored thesis rules require authenticated storage migration. No default pass/fail score is invented."}

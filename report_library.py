
from __future__ import annotations
import io, re, json, urllib.request
from datetime import datetime
import pandas as pd
from pypdf import PdfReader

UA="Market Investment Analyst research@example.com"

def _get_json(url,headers=None):
    req=urllib.request.Request(url,headers=headers or {"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def _get_bytes(url,headers=None):
    req=urllib.request.Request(url,headers=headers or {"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read(),r.headers.get("Content-Type","")

def sec_reports(ticker, cik=None, limit=100):
    """Official SEC submissions feed. Returns filings with direct filing document URLs."""
    if not cik:
        try:
            tickers=_get_json("https://www.sec.gov/files/company_tickers.json",{"User-Agent":UA})
            hit=[v for v in tickers.values() if str(v.get("ticker","")).upper()==ticker.upper()]
            if not hit:return pd.DataFrame()
            cik=int(hit[0]["cik_str"])
        except Exception:return pd.DataFrame()
    try:
        j=_get_json(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",{"User-Agent":UA})
        r=j["filings"]["recent"]; rows=[]
        forms={"10-K","10-K/A","10-Q","10-Q/A","8-K","8-K/A","20-F","20-F/A","6-K","40-F"}
        for i,form in enumerate(r.get("form",[])):
            if form not in forms:continue
            accession=r["accessionNumber"][i]
            primary=r["primaryDocument"][i]
            acc=accession.replace("-","")
            url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{primary}"
            rows.append({"Date":r["filingDate"][i],"Type":form,"Title":f"{form} — {primary}",
                         "Source":"SEC EDGAR","URL":url,"Accession":accession})
            if len(rows)>=limit:break
        return pd.DataFrame(rows)
    except Exception:return pd.DataFrame()

def asx_reports(ticker, limit=100):
    """ASX announcements endpoint. Availability can change; returns official announcement metadata when accessible."""
    code=ticker.upper().replace(".AX","")
    try:
        j=_get_json(f"https://www.asx.com.au/asx/1/company/{code}/announcements?count={int(limit)}")
        data=j.get("data",j) if isinstance(j,dict) else j
        rows=[]
        for x in data or []:
            url=x.get("url") or x.get("document_url") or x.get("documentUrl") or ""
            if url.startswith("/"):url="https://www.asx.com.au"+url
            rows.append({"Date":x.get("document_date") or x.get("date") or "",
                         "Type":x.get("header") or x.get("type") or "Announcement",
                         "Title":x.get("header") or x.get("headline") or x.get("title") or "ASX announcement",
                         "Source":"ASX","URL":url,"Accession":x.get("id","")})
        return pd.DataFrame(rows)
    except Exception:return pd.DataFrame()

def report_catalog(ticker,limit=100):
    return asx_reports(ticker,limit) if ticker.upper().endswith(".AX") else sec_reports(ticker,limit=limit)

def download_report(url):
    if not url:return None,""
    try:return _get_bytes(url,{"User-Agent":UA})
    except Exception:return None,""

def extract_text(data,content_type="",max_pages=40):
    if not data:return ""
    # PDF
    if data[:4]==b"%PDF" or "pdf" in (content_type or "").lower():
        try:
            reader=PdfReader(io.BytesIO(data))
            return "\n".join((p.extract_text() or "") for p in reader.pages[:max_pages])
        except Exception:return ""
    # HTML/text filings
    try:
        text=data.decode("utf-8",errors="ignore")
        text=re.sub(r"<script.*?</script>|<style.*?</style>"," ",text,flags=re.I|re.S)
        text=re.sub(r"<[^>]+>"," ",text)
        return re.sub(r"\s+"," ",text)
    except Exception:return ""

def local_summary(text,max_chars=1800):
    """Extractive, deterministic summary when no LLM client is configured."""
    if not text:return "The report could not be converted to readable text automatically."
    clean=re.sub(r"\s+"," ",text).strip()
    # Favor early substantive sentences; no invented interpretation.
    sentences=re.split(r"(?<=[.!?])\s+",clean)
    useful=[]
    boiler=("table of contents","commission file","forward-looking statements")
    for s in sentences:
        if 50<=len(s)<=500 and not any(b in s.lower() for b in boiler):
            useful.append(s)
        if sum(len(x) for x in useful)>=max_chars:break
    return " ".join(useful)[:max_chars] or clean[:max_chars]

def report_summary(url):
    data,ctype=download_report(url)
    text=extract_text(data,ctype)
    return local_summary(text),data,ctype

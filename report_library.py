
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

def _asx_html(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":"Mozilla/5.0 Market Investment Analyst",
        "Accept":"text/html,application/xhtml+xml"
    })
    with urllib.request.urlopen(req,timeout=25) as r:
        return r.read().decode("utf-8",errors="ignore")

def _parse_asx_rows(html, code):
    """Parse official ASX historical-announcement result rows and preserve PDF links."""
    from html.parser import HTMLParser
    from urllib.parse import urljoin

    class P(HTMLParser):
        def __init__(self):
            super().__init__(); self.rows=[]; self.row=None; self.cell=None
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=="tr":
                self.row={"cells":[],"links":[]}
            elif tag in ("td","th") and self.row is not None:
                self.cell=[]
            elif tag=="a" and self.row is not None:
                href=attrs.get("href","")
                if href:self.row["links"].append(href)
        def handle_data(self,data):
            if self.cell is not None:self.cell.append(data)
        def handle_endtag(self,tag):
            if tag in ("td","th") and self.row is not None and self.cell is not None:
                self.row["cells"].append(re.sub(r"\s+"," "," ".join(self.cell)).strip())
                self.cell=None
            elif tag=="tr" and self.row is not None:
                self.rows.append(self.row); self.row=None; self.cell=None

    p=P(); p.feed(html)
    out=[]
    date_re=re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")
    for row in p.rows:
        text=" | ".join(x for x in row["cells"] if x)
        dm=date_re.search(text)
        pdfs=[u for u in row["links"] if "asxpdf" in u.lower() or u.lower().endswith(".pdf")]
        if not dm or not pdfs: continue
        # Headline is generally the longest non-date, non-size/time cell.
        candidates=[]
        for c in row["cells"]:
            if not c or date_re.search(c): continue
            if re.fullmatch(r"\d{1,2}:\d{2}\s*(am|pm)?",c,re.I): continue
            if re.fullmatch(r"[\d.]+\s*(kb|mb|pages?)?.*",c,re.I): continue
            if c.upper()==code.upper(): continue
            candidates.append(c)
        title=max(candidates,key=len) if candidates else "ASX announcement"
        href=pdfs[0]
        if href.startswith("//"): href="https:"+href
        elif href.startswith("/"): href=urljoin("https://www.asx.com.au",href)
        out.append({"Date":dm.group(1),"Type":_asx_report_type(title),
                    "Title":title,"Source":"ASX","URL":href,"Accession":href.rsplit("/",1)[-1]})
    return out

def _asx_report_type(title):
    t=(title or "").lower()
    if "annual report" in t or "appendix 4e" in t:return "Annual Report / FY Results"
    if "half year" in t or "half-year" in t or "appendix 4d" in t:return "Half-Year Report"
    if "quarter" in t:return "Quarterly Report"
    if "presentation" in t:return "Results / Investor Presentation"
    if "trading update" in t:return "Trading Update"
    if "results" in t or "result" in t:return "Results"
    return "ASX Announcement"

def asx_reports(ticker, limit=100):
    """Official ASX historical-announcement search, including direct ASX PDF links."""
    code=ticker.upper().replace(".AX","")[:3]
    current=datetime.now().year
    rows=[]
    # Query calendar years individually so the history is not restricted to the recent window.
    for year in range(current,current-12,-1):
        try:
            params=urllib.parse.urlencode({
                "asxCode":code,"by":"asxCode","timeframe":"Y","year":year
            })
            html=_asx_html("https://www.asx.com.au/asx/v2/statistics/announcements.do?"+params)
            rows.extend(_parse_asx_rows(html,code))
        except Exception:
            continue
        if len(rows)>=int(limit): break
    if not rows:return pd.DataFrame()
    df=pd.DataFrame(rows).drop_duplicates(subset=["URL"])
    dt=pd.to_datetime(df["Date"],dayfirst=True,errors="coerce")
    df=df.assign(_date=dt).sort_values("_date",ascending=False).drop(columns="_date")
    return df.head(int(limit)).reset_index(drop=True)


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

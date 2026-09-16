
from __future__ import annotations
import io, os, re, json, urllib.parse, urllib.request
from datetime import datetime, timedelta
import pandas as pd
from pypdf import PdfReader

UA="Market Investment Analyst/12.0 research application"
ASX_ARCHIVE="https://www.asx.com.au/asx/v2/statistics/announcements.do"

def _get(url, headers=None, timeout=25):
    req=urllib.request.Request(url,headers=headers or {
        "User-Agent":"Mozilla/5.0 (compatible; MarketInvestmentAnalyst/12.0)",
        "Accept":"text/html,application/xhtml+xml,application/pdf,*/*"
    })
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type","")

def classify(title):
    t=(title or "").lower()
    rules=[
      ("Annual Report",["annual report","appendix 4e","preliminary final"]),
      ("Half-Year Report",["half year","half-year","appendix 4d","interim report"]),
      ("Quarterly Report",["quarterly","appendix 4c","appendix 5b"]),
      ("Results",["results","financial statements","accounts"]),
      ("Investor Presentation",["presentation","investor day"]),
      ("Trading Update",["trading update","business update"]),
      ("Guidance",["guidance","outlook"]),
      ("Capital / Funding",["capital raising","placement","entitlement offer","buy-back","buyback"]),
      ("Ownership",["substantial holder","substantial holding"]),
      ("Director Notice",["director's interest","director interest","appendix 3x","appendix 3y","appendix 3z"]),
      ("Corporate Action",["dividend","scheme","acquisition","merger","takeover"]),
    ]
    for label,terms in rules:
        if any(x in t for x in terms): return label
    return "ASX Announcement"

def _parse_asx(html, code):
    # ASX archive HTML contains direct asxpdf links. Capture row-level text around each PDF.
    rows=[]
    tr_blocks=re.findall(r"<tr\b[^>]*>(.*?)</tr>",html,flags=re.I|re.S)
    for tr in tr_blocks:
        hrefs=re.findall(r'href=["\']([^"\']+)["\']',tr,flags=re.I)
        pdfs=[h for h in hrefs if "asxpdf" in h.lower() or ".pdf" in h.lower() or "displayannouncement.do" in h.lower()]
        if not pdfs: continue
        text=re.sub(r"<[^>]+>"," ",tr)
        text=re.sub(r"&nbsp;|&#160;"," ",text,flags=re.I)
        text=re.sub(r"&amp;","&",text,flags=re.I)
        text=re.sub(r"\s+"," ",text).strip()
        dm=re.search(r"(\d{1,2}/\d{1,2}/\d{4})",text)
        if not dm: continue
        date=dm.group(1)
        # Remove date/time/size boilerplate to derive headline.
        title=text
        title=re.sub(r"\d{1,2}/\d{1,2}/\d{4}"," ",title)
        title=re.sub(r"\b\d{1,2}:\d{2}\s*(?:am|pm)?\b"," ",title,flags=re.I)
        title=re.sub(r"\b\d+\s+pages?\b"," ",title,flags=re.I)
        title=re.sub(r"\b[\d.]+\s*(?:KB|MB)\b"," ",title,flags=re.I)
        title=re.sub(r"\s+"," ",title).strip(" |-")
        href=pdfs[0]
        if href.startswith("//"): href="https:"+href
        elif href.startswith("/"): href="https://www.asx.com.au"+href
        sensitive=bool(re.search(r"price sensitive",tr,flags=re.I))
        rows.append({"Date":date,"Time":"","Type":classify(title),"Title":title or "ASX announcement",
                     "Price Sensitive":sensitive,"Source":"ASX historical announcements",
                     "URL":href,"ID":href.rsplit("/",1)[-1]})
    return rows

def asx_public_archive(code, years=12, limit=250):
    """Best-effort ASX website metadata fallback.
    Uses the public per-code announcements page rather than the invalid V12 year query.
    This is intentionally not presented as a licensed ComNews feed.
    """
    code=code.upper().replace(".AX","")[:3]
    urls=[
      f"https://www.asx.com.au/markets/trade-our-cash-market/announcements.{code}",
      ASX_ARCHIVE+"?"+urllib.parse.urlencode({"asx":code,"by":"asxCode","period":"M6","timeframe":"D"})
    ]
    rows=[]
    for url in urls:
        try:
            raw,_=_get(url)
            html=raw.decode("utf-8",errors="ignore")
            rows.extend(_parse_asx(html,code))
            if rows:break
        except Exception:
            continue
    if not rows:return pd.DataFrame()
    df=pd.DataFrame(rows).drop_duplicates("URL")
    df["_d"]=pd.to_datetime(df["Date"],dayfirst=True,errors="coerce")
    return df.sort_values("_d",ascending=False).drop(columns="_d").head(limit).reset_index(drop=True)


def asx_provider_api(code, api_url, api_key="", limit=250):
    """Generic adapter for a licensed/authorised ASX announcement vendor.
    Expected normalized JSON: results/data array with date/title/pdf URL fields.
    Configure ASX_ANNOUNCEMENTS_API_URL and optionally ASX_ANNOUNCEMENTS_API_KEY.
    """
    if not api_url:return pd.DataFrame()
    sep="&" if "?" in api_url else "?"
    url=api_url+sep+urllib.parse.urlencode({"company_code":code.upper().replace(".AX",""),"limit":limit})
    headers={"User-Agent":UA,"Accept":"application/json"}
    if api_key: headers["Authorization"]="Bearer "+api_key
    try:
        raw,_=_get(url,headers)
        j=json.loads(raw.decode())
        data=j.get("results") or j.get("data") or (j if isinstance(j,list) else [])
        rows=[]
        for x in data:
            rows.append({
              "Date":x.get("filing_date") or x.get("date") or x.get("release_date") or "",
              "Time":x.get("time") or "",
              "Type":x.get("document_type") or classify(x.get("title","")),
              "Title":x.get("title") or x.get("headline") or "ASX announcement",
              "Price Sensitive":bool(x.get("is_price_sensitive") or x.get("price_sensitive")),
              "Source":x.get("source") or "ASX announcement provider",
              "URL":x.get("pdf_url") or x.get("url") or x.get("document_url") or "",
              "ID":str(x.get("announcement_number") or x.get("id") or "")
            })
        return pd.DataFrame(rows)
    except Exception:return pd.DataFrame()

INVESTOR_FORMS={"10-K","10-K/A","10-Q","10-Q/A","8-K","8-K/A","20-F","20-F/A","40-F","6-K","ARS","DEF 14A"}

def _sec_group(form):
    if form in {"10-K","10-K/A","20-F","20-F/A","40-F","ARS"}: return "Financial Reports"
    if form in {"10-Q","10-Q/A"}: return "Quarterly Reports"
    if form in {"8-K","8-K/A","6-K"}: return "Company Announcements"
    if form=="DEF 14A": return "Proxy / Governance"
    return "Other Regulatory Filings"

def _sec_filing_base(cik, accession):
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-','')}/"

def _sec_pdf_from_index(cik, accession, headers):
    """Return a company-filed PDF if the SEC filing index contains one."""
    base=_sec_filing_base(cik,accession)
    index_url=base+accession+"-index.html"
    try:
        raw,_=_get(index_url,headers)
        html=raw.decode("utf-8",errors="ignore")
        hrefs=re.findall(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',html,flags=re.I)
        if hrefs:
            h=hrefs[0]
            if h.startswith("http"): return h,index_url
            if h.startswith("/"): return "https://www.sec.gov"+h,index_url
            return base+h,index_url
    except Exception:
        pass
    return "",index_url

def _sec_label(form, primary):
    labels={
      "10-K":"Annual Report (10-K)","10-K/A":"Annual Report Amendment (10-K/A)",
      "10-Q":"Quarterly Report (10-Q)","10-Q/A":"Quarterly Report Amendment (10-Q/A)",
      "8-K":"Current Report (8-K)","8-K/A":"Current Report Amendment (8-K/A)",
      "20-F":"Annual Report (20-F)","20-F/A":"Annual Report Amendment (20-F/A)",
      "40-F":"Annual Report (40-F)","6-K":"Foreign Issuer Report (6-K)",
      "DEF 14A":"Proxy Statement","4":"Insider Transaction (Form 4)",
      "3":"Initial Insider Ownership (Form 3)","5":"Annual Insider Statement (Form 5)"
    }
    return labels.get(form,form)+(f" — {primary}" if primary else "")

def _sec_primary_url(cik, accession, primary):
    base=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-','')}/"
    # SEC primaryDocument can contain an XSL display path such as xslF345X06/form4.xml.
    # That display URL is valid in a browser, but for programmatic retrieval the raw XML
    # is more reliable and machine-readable.
    raw=primary or ""
    if "/" in raw and raw.lower().endswith(".xml"):
        raw=raw.rsplit("/",1)[-1]
    return base+raw, base+accession+"-index.html"

def sec_archive(ticker, limit=250, include_regulatory=False):
    headers={"User-Agent":"Market Investment Analyst research contact@example.com",
             "Accept":"application/json,text/html,application/pdf,*/*"}
    try:
        raw,_=_get("https://www.sec.gov/files/company_tickers.json",headers)
        tickers=json.loads(raw.decode())
        hit=[v for v in tickers.values() if str(v.get("ticker","")).upper()==ticker.upper()]
        if not hit:return pd.DataFrame()
        cik=int(hit[0]["cik_str"])
        raw,_=_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json",headers)
        j=json.loads(raw.decode()); r=j["filings"]["recent"]; rows=[]
        for i,form in enumerate(r.get("form",[])):
            if not include_regulatory and form not in INVESTOR_FORMS:
                continue
            accession=r["accessionNumber"][i]; primary=r["primaryDocument"][i]
            base=_sec_filing_base(cik,accession)
            primary_url=base+primary
            pdf_url,index_url=_sec_pdf_from_index(cik,accession,headers)
            rows.append({
              "Date":r["filingDate"][i],"Time":"","Group":_sec_group(form),"Type":form,
              "Title":_sec_label(form,primary),"Price Sensitive":False,"Source":"SEC EDGAR",
              "PDFURL":pdf_url,"ReadURL":primary_url,"IndexURL":index_url,
              "URL":pdf_url or primary_url,"Has PDF":bool(pdf_url),"ID":accession})
            if len(rows)>=limit:break
        return pd.DataFrame(rows)
    except Exception:return pd.DataFrame()


def announcements(ticker, provider_url="", provider_key="", limit=250):
    if ticker.upper().endswith(".AX"):
        code=ticker[:-3]

        # Only use the licensed/provider route when it actually returns rows.
        p=asx_provider_api(code,provider_url,provider_key,limit)
        if p is not None and not p.empty:
            p=p.copy()
            if "URL" not in p.columns:p["URL"]=""
            if "PDFURL" not in p.columns:p["PDFURL"]=p["URL"]
            if "ReadURL" not in p.columns:p["ReadURL"]=p["URL"]
            if "Has PDF" not in p.columns:
                p["Has PDF"]=p["PDFURL"].astype(str).str.lower().str.contains(r"\\.pdf(?:$|\\?)",regex=True)
            if "Group" not in p.columns:p["Group"]="ASX Announcements"
            return p,"Provider-backed ASX announcements"

        # Provider unavailable/empty: continue to the public fallback.
        p=asx_public_archive(code,12,limit)
        if p is None or p.empty:
            cols=["Date","Time","Group","Type","Title","Price Sensitive",
                  "Source","URL","PDFURL","ReadURL","Has PDF","ID"]
            return pd.DataFrame(columns=cols),"ASX public archive fallback"

        p=p.copy()
        if "URL" not in p.columns:p["URL"]=""
        if "PDFURL" not in p.columns:p["PDFURL"]=p["URL"]
        if "ReadURL" not in p.columns:p["ReadURL"]=p["URL"]
        if "Has PDF" not in p.columns:
            p["Has PDF"]=p["PDFURL"].astype(str).str.lower().str.contains(r"\\.pdf(?:$|\\?)",regex=True)
        if "Group" not in p.columns:p["Group"]="ASX Announcements"
        return p,"ASX public archive fallback"

    return sec_archive(ticker,limit),"SEC EDGAR"

def fetch_document(url, fallback_url=""):
    if not url:return None,""
    candidates=[url]
    # If raw XML is unavailable, try the filing index page rather than failing outright.
    if fallback_url:candidates.append(fallback_url)
    for candidate in candidates:
        try:
            data,ctype=_get(candidate,timeout=40)
            if data:return data,ctype
        except Exception:
            continue
    return None,""


def extract_text(data,ctype="",max_pages=60):
    if not data:return ""
    if data[:4]==b"%PDF" or "pdf" in ctype.lower():
        try:
            r=PdfReader(io.BytesIO(data))
            return "\n".join((p.extract_text() or "") for p in r.pages[:max_pages])
        except:return ""
    text=data.decode("utf-8",errors="ignore")
    # Preserve readable values from SEC XML/HTML rather than treating XML as an error.
    text=re.sub(r"<script.*?</script>|<style.*?</style>"," ",text,flags=re.I|re.S)
    text=re.sub(r"</(?:name|value|issuerName|rptOwnerName|transactionCode|transactionShares|transactionPricePerShare)>","; ",text,flags=re.I)
    text=re.sub(r"<[^>]+>"," ",text)
    text=text.replace("&amp;","&").replace("&lt;","<").replace("&gt;",">")
    return re.sub(r"\s+"," ",text).strip()

def evidence_summary(text, max_chars=3500):
    if not text:return "No machine-readable text could be extracted from this document."
    clean=re.sub(r"\s+"," ",text).strip()
    sents=re.split(r"(?<=[.!?])\s+",clean)
    keywords=("revenue","ebitda","profit","loss","margin","cash","guidance","outlook","growth",
              "customer","volume","credit loss","bad debt","debt","capital","dividend","risk")
    scored=[]
    for i,s in enumerate(sents):
        if 45<=len(s)<=600:
            score=sum(k in s.lower() for k in keywords)+(2 if i<25 else 0)
            scored.append((score,-i,s))
    scored.sort(reverse=True)
    chosen=[]; used=set()
    for _,__,s in scored:
        key=s[:80]
        if key not in used:
            chosen.append(s); used.add(key)
        if sum(len(x) for x in chosen)>=max_chars:break
    return " ".join(chosen)[:max_chars]


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
        pdfs=[h for h in hrefs if "asxpdf" in h.lower() or ".pdf" in h.lower()]
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
    code=code.upper().replace(".AX","")[:3]
    rows=[]
    now=datetime.now().year
    for year in range(now,now-years,-1):
        params=urllib.parse.urlencode({"asxCode":code,"by":"asxCode","timeframe":"Y","year":year})
        try:
            raw,_=_get(ASX_ARCHIVE+"?"+params)
            rows.extend(_parse_asx(raw.decode("utf-8",errors="ignore"),code))
        except Exception:
            continue
        if len(rows)>=limit: break
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

def sec_archive(ticker, limit=250):
    headers={"User-Agent":"Market Investment Analyst research contact@example.com","Accept-Encoding":"gzip, deflate"}
    try:
        raw,_=_get("https://www.sec.gov/files/company_tickers.json",headers)
        tickers=json.loads(raw.decode())
        hit=[v for v in tickers.values() if str(v.get("ticker","")).upper()==ticker.upper()]
        if not hit:return pd.DataFrame()
        cik=int(hit[0]["cik_str"])
        raw,_=_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json",headers)
        j=json.loads(raw.decode()); r=j["filings"]["recent"]; rows=[]
        for i,form in enumerate(r.get("form",[])):
            accession=r["accessionNumber"][i]; primary=r["primaryDocument"][i]
            url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-','')}/{primary}"
            rows.append({"Date":r["filingDate"][i],"Time":"","Type":form,
              "Title":f"{form} — {primary}","Price Sensitive":False,"Source":"SEC EDGAR",
              "URL":url,"ID":accession})
            if len(rows)>=limit:break
        return pd.DataFrame(rows)
    except Exception:return pd.DataFrame()

def announcements(ticker, provider_url="", provider_key="", limit=250):
    if ticker.upper().endswith(".AX"):
        code=ticker[:-3]
        p=asx_provider_api(code,provider_url,provider_key,limit)
        if not p.empty:return p,"Provider-backed ASX announcements"
        return asx_public_archive(code,12,limit),"ASX public archive fallback"
    return sec_archive(ticker,limit),"SEC EDGAR"

def fetch_document(url):
    if not url:return None,""
    try:return _get(url,timeout=40)
    except Exception:return None,""

def extract_text(data,ctype="",max_pages=60):
    if not data:return ""
    if data[:4]==b"%PDF" or "pdf" in ctype.lower():
        try:
            r=PdfReader(io.BytesIO(data))
            return "\n".join((p.extract_text() or "") for p in r.pages[:max_pages])
        except:return ""
    text=data.decode("utf-8",errors="ignore")
    text=re.sub(r"<script.*?</script>|<style.*?</style>"," ",text,flags=re.I|re.S)
    text=re.sub(r"<[^>]+>"," ",text)
    return re.sub(r"\s+"," ",text)

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

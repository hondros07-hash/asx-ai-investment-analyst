
from __future__ import annotations
import io, os, re, json, urllib.parse, urllib.request
from datetime import datetime, timedelta
import pandas as pd
from pypdf import PdfReader

UA="Market Investment Analyst/12.0 research application"
ASX_ARCHIVE="https://www.asx.com.au/asx/v2/statistics/announcements.do"
ASX_COMPANY_API="https://asx.api.markitdigital.com/asx-research/1.0/companies/{code}/announcements"

def asx_company_announcements_api(code, limit=5):
    """Read the JSON announcements feed used by the ASX company pages.

    This is the preferred lightweight list route.  It returns the latest company
    announcements even when the legacy ASX HTML search is blocked by anti-bot
    middleware.  We keep the legacy search as a fallback because it can expose
    direct asxpdf links.
    """
    code=re.sub(r'[^A-Z0-9]','',str(code or '').upper().replace('.AX',''))[:3]
    cols=['Date','Time','Group','Type','Title','Price Sensitive','Source','URL','PDFURL','ReadURL','Has PDF','ID']
    if not code: return pd.DataFrame(columns=cols)
    url=ASX_COMPANY_API.format(code=code.lower())+'?'+urllib.parse.urlencode({'count':max(5,min(int(limit or 5),20))})
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36',
             'Accept':'application/json,text/plain,*/*','Origin':'https://www.asx.com.au','Referer':f'https://www.asx.com.au/markets/company/{code.lower()}'}
    try:
        raw,ctype=_get(url,headers,25); payload=json.loads(raw.decode('utf-8','ignore'))
        data=payload.get('data') or {}; items=data.get('items') or data.get('announcements') or []
        rows=[]
        search_url=ASX_ARCHIVE+'?'+urllib.parse.urlencode({'asxCode':code,'by':'asxCode','timeframe':'Y','year':datetime.now().year})
        for x in items:
            if not isinstance(x,dict): continue
            raw_date=x.get('date') or x.get('releaseDate') or x.get('publishedDate') or ''
            dt=pd.to_datetime(raw_date,errors='coerce',utc=True)
            date=dt.strftime('%d/%m/%Y') if pd.notna(dt) else str(raw_date)[:10]
            tm=dt.strftime('%I:%M %p').lstrip('0').lower() if pd.notna(dt) else ''
            title=str(x.get('headline') or x.get('title') or 'ASX announcement').strip()
            key=str(x.get('documentKey') or x.get('documentId') or x.get('id') or '').strip()
            direct=str(x.get('url') or x.get('documentUrl') or x.get('pdfUrl') or '').strip()
            if direct.startswith('/'): direct='https://www.asx.com.au'+direct
            # Never invent a document URL. If the feed omits it, link to the
            # authoritative ASX company search where the document is exposed.
            read_url=direct or search_url
            rows.append({'Date':date,'Time':tm,'Group':'ASX Announcements',
                         'Type':str(x.get('announcementType') or classify(title)).strip(),
                         'Title':title,'Price Sensitive':bool(x.get('isPriceSensitive') or x.get('priceSensitive')),
                         'Source':'ASX company announcements feed','URL':read_url,
                         'PDFURL':direct if direct.lower().split('?')[0].endswith('.pdf') else '',
                         'ReadURL':read_url,'Has PDF':bool(direct and direct.lower().split('?')[0].endswith('.pdf')),
                         'ID':key})
        df=pd.DataFrame(rows,columns=cols)
        df.attrs.update({'status':'OK' if rows else 'ASX_API_NO_ROWS','ticker':code,'source':'ASX company announcements feed','endpoint':url})
        return df.head(limit).reset_index(drop=True)
    except Exception as e:
        df=pd.DataFrame(columns=cols); df.attrs.update({'status':'ASX_API_FAILED','ticker':code,'error':type(e).__name__+': '+str(e)[:180],'endpoint':url}); return df


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

def _asx_abs_url(href):
    href=str(href or '').strip().replace('&amp;','&')
    if href.startswith('//'): return 'https:'+href
    if href.startswith('/'): return 'https://www.asx.com.au'+href
    if href.startswith('http'): return href
    return urllib.parse.urljoin('https://www.asx.com.au/',href)

def _parse_asx(html, code):
    """Parse ASX public announcement-search HTML defensively.

    Supports legacy/current table markup and link/container variants. A row is
    accepted only when it has a release date and an ASX document/display link;
    this prevents navigation links from becoming fake announcements.
    """
    from html import unescape
    rows=[]; seen=set()
    blocks=re.findall(r'<tr\b[^>]*>(.*?)</tr>',html,flags=re.I|re.S)
    # Also inspect bounded regions around likely document anchors. Current ASX
    # markup has varied between asxpdf, announcement/display routes and generic
    # anchors whose surrounding row contains page-count/file-size metadata.
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</a>',html,flags=re.I|re.S):
        href=m.group(1); low=href.lower()
        a=max(0,m.start()-1200); b=min(len(html),m.end()+1200); block=html[a:b]
        nearby=unescape(re.sub(r'<[^>]+>',' ',block)); nearby=re.sub(r'\s+',' ',nearby)
        likely=('asxpdf' in low or 'displayannouncement' in low or low.endswith('.pdf') or
                (re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b',nearby) and re.search(r'\b\d+\s+pages?\b',nearby,re.I)))
        if likely: blocks.append(block)
    for block in blocks:
        text=unescape(re.sub(r'<[^>]+>',' ',block)); text=re.sub(r'\s+',' ',text).strip()
        dm=re.search(r'(\d{1,2}/\d{1,2}/\d{4})',text)
        if not dm: continue
        anchors=[]
        for am in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',block,flags=re.I|re.S):
            href=am.group(1); label=unescape(re.sub(r'<[^>]+>',' ',am.group(2))); label=re.sub(r'\s+',' ',label).strip()
            low=href.lower()
            score=0
            if 'asxpdf' in low: score+=5
            if 'displayannouncement' in low: score+=5
            if low.split('?')[0].endswith('.pdf'): score+=4
            if label and not any(x in label.lower() for x in ('search again','adobe','how and when')): score+=1
            anchors.append((score,href,label))
        anchors.sort(reverse=True,key=lambda x:x[0])
        # V21.3.09: ASX has changed announcement-row markup more than once. Do not
        # discard a valid row merely because its headline link is not an asxpdf/
        # displayAnnouncement URL. A dated table row is still useful disclosure
        # metadata; in that case route VIEW to the official company search page.
        raw_href=''; title=''
        if anchors:
            _,raw_href,title=anchors[0]
        href=_asx_abs_url(raw_href) if raw_href else ''
        date=dm.group(1); tm=re.search(r'\b(\d{1,2}:\d{2}\s*(?:am|pm))\b',text,flags=re.I); time=tm.group(1) if tm else ''
        if not title:
            title=text
            for pat in (r'\d{1,2}/\d{1,2}/\d{4}',r'\b\d{1,2}:\d{2}\s*(?:am|pm)?\b',r'\b\d+\s+pages?\b',r'\b[\d.]+\s*(?:KB|MB)\b',r'Price\s*sens\.?'):
                title=re.sub(pat,' ',title,flags=re.I)
            title=re.sub(r'\s+',' ',title).strip(' |-')
        # Reject page chrome / non-announcement rows.
        if not title or any(x in title.lower() for x in ('released between','search results','search again','useful information','viewing market announcements')):
            continue
        fallback=ASX_ARCHIVE+'?'+urllib.parse.urlencode({'asxCode':code,'by':'asxCode','period':'M6','timeframe':'D'})
        read_url=href or fallback
        dedupe=(date+'|'+time+'|'+title).lower()
        if dedupe in seen: continue
        has_pdf=bool(href and ('asxpdf' in href.lower() or href.lower().split('?')[0].endswith('.pdf')))
        rows.append({'Date':date,'Time':time,'Group':'ASX Announcements','Type':classify(title),
                     'Title':title,'Price Sensitive':bool(re.search(r'price sensitive',block,re.I)),
                     'Source':'ASX Market Announcements','URL':read_url,'PDFURL':href if has_pdf else '',
                     'ReadURL':read_url,'Has PDF':has_pdf,'ID':dedupe})
        seen.add(dedupe)
    return rows



def _parse_asx_tables(html, code):
    """V21.3.11 fallback: parse the actual ASX results table as data, independent of anchor markup.
    This deliberately prefers truthful disclosure metadata over returning an empty card
    when ASX changes document-link HTML. Document access falls back to the official
    ticker search page when a direct PDF cannot be recovered.
    """
    from io import StringIO
    rows=[]; seen=set()
    try:
        tables=pd.read_html(StringIO(html))
    except Exception:
        return rows
    search_url=ASX_ARCHIVE+'?'+urllib.parse.urlencode({'asxCode':code,'by':'asxCode','period':'M6','timeframe':'D'})
    for table in tables:
        if table is None or table.empty: continue
        cols=[str(c).strip().lower() for c in table.columns]
        date_i=next((i for i,c in enumerate(cols) if 'date' in c),None)
        head_i=next((i for i,c in enumerate(cols) if 'headline' in c or 'announcement' in c),None)
        if date_i is None or head_i is None: continue
        for _,r in table.iterrows():
            dv=str(r.iloc[date_i] if date_i < len(r) else '').strip()
            title=str(r.iloc[head_i] if head_i < len(r) else '').strip()
            dm=re.search(r'(\d{1,2}/\d{1,2}/\d{4})',dv)
            if not dm or not title or title.lower() in ('nan','headline'): continue
            tm=re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm))',dv,re.I)
            date=dm.group(1); time=tm.group(1) if tm else ''
            key=(date+'|'+time+'|'+title).lower()
            if key in seen: continue
            rows.append({'Date':date,'Time':time,'Group':'ASX Announcements','Type':classify(title),
                         'Title':title,'Price Sensitive':False,'Source':'ASX Market Announcements',
                         'URL':search_url,'PDFURL':'','ReadURL':search_url,'Has PDF':False,'ID':key})
            seen.add(key)
    return rows

def asx_modern_company_page(code, limit=250):
    """Best-effort parser for ASX's current public company announcement page.

    This route is intentionally independent of the legacy statistics endpoint so
    hosted deployments have a second official-ASX path. No rows are fabricated.
    """
    code=re.sub(r'[^A-Z0-9]','',str(code or '').upper().replace('.AX',''))[:3]
    cols=['Date','Time','Group','Type','Title','Price Sensitive','Source','URL','PDFURL','ReadURL','Has PDF','ID']
    if not code: return pd.DataFrame(columns=cols)
    urls=[
      f'https://www.asx.com.au/markets/trade-our-cash-market/announcements.{code.lower()}',
      ASX_ARCHIVE+'?'+urllib.parse.urlencode({'asxCode':code,'by':'asxCode','timeframe':'Y','year':datetime.now().year}),
    ]
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36',
             'Accept':'text/html,application/xhtml+xml,*/*','Accept-Language':'en-AU,en;q=0.9'}
    diagnostics=[]
    for url in urls:
        try:
            raw,ctype=_get(url,headers,30); page=raw.decode('utf-8','ignore')
            rows=_parse_asx(page,code)
            if not rows: rows=_parse_asx_tables(page,code)
            diagnostics.append({'endpoint':url,'bytes':len(raw),'content_type':ctype,'rows':len(rows)})
            if rows:
                df=pd.DataFrame(rows).drop_duplicates(subset=['Date','Time','Title'])
                df['_d']=pd.to_datetime(df['Date'],dayfirst=True,errors='coerce')
                df=df.sort_values('_d',ascending=False,na_position='last').drop(columns='_d').head(limit).reset_index(drop=True)
                df.attrs.update({'status':'OK','ticker':code,'source':'ASX Market Announcements','diagnostics':diagnostics})
                return df
        except Exception as e:
            diagnostics.append({'endpoint':url,'error':type(e).__name__+': '+str(e)[:240]})
    df=pd.DataFrame(columns=cols); df.attrs.update({'status':'ASX_OFFICIAL_ROUTES_FAILED','ticker':code,'diagnostics':diagnostics}); return df

def asx_public_archive(code, years=12, limit=250):
    """Live public ASX search with explicit diagnostics and several supported windows."""
    code=re.sub(r'[^A-Z0-9]','',str(code or '').upper().replace('.AX',''))[:3]
    cols=['Date','Time','Group','Type','Title','Price Sensitive','Source','URL','PDFURL','ReadURL','Has PDF','ID']
    if not code: return pd.DataFrame(columns=cols)
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36',
             'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'en-AU,en;q=0.9',
             'Referer':'https://www.asx.com.au/markets/trade-our-cash-market/announcements'}
    diagnostics=[]; rows=[]
    queries=[
      {'asxCode':code,'by':'asxCode','period':'M6','timeframe':'D'},
      {'asxCode':code,'by':'asxCode','period':'M3','timeframe':'D'},
      {'asxCode':code,'by':'asxCode','period':'M1','timeframe':'D'},
      {'asxCode':code,'by':'asxCode','period':'W','timeframe':'D'},
      {'asxCode':code,'by':'asxCode','timeframe':'Y','year':datetime.now().year},
    ]
    for params in queries:
        try:
            url=ASX_ARCHIVE+'?'+urllib.parse.urlencode(params); raw,ctype=_get(url,headers,30)
            page=raw.decode('utf-8',errors='ignore'); parsed=_parse_asx(page,code)
            if not parsed: parsed=_parse_asx_tables(page,code)
            diagnostics.append({'query':params,'bytes':len(raw),'rows':len(parsed),'content_type':ctype})
            if parsed: rows=parsed; break
        except Exception as e:
            diagnostics.append({'query':params,'url':url if 'url' in locals() else ASX_ARCHIVE,'error':type(e).__name__+': '+str(e)[:240]})
    if not rows:
        df=pd.DataFrame(columns=cols); df.attrs.update({'status':'ASX_NO_PARSED_ROWS','ticker':code,'diagnostics':diagnostics}); return df
    df=pd.DataFrame(rows).drop_duplicates('URL'); df['_d']=pd.to_datetime(df['Date'],dayfirst=True,errors='coerce')
    df=df.sort_values('_d',ascending=False).drop(columns='_d').head(limit).reset_index(drop=True)
    df.attrs.update({'status':'OK','ticker':code,'diagnostics':diagnostics,'source':'ASX public company-announcement search'})
    return df

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

def _sec_headers():
    # SEC asks automated clients to declare a User-Agent. Operators can set a
    # real contact string in Streamlit/host secrets via SEC_USER_AGENT.
    ua=os.getenv("SEC_USER_AGENT", "Chrimata/21.3.06 (+https://github.com/hondros07-hash/asx-ai-investment-analyst; market-research application)")
    return {"User-Agent":ua,"Accept":"application/json,text/html,*/*"}


def _sec_ticker_to_cik(ticker, headers):
    """Resolve a US ticker using SEC's exchange-aware mapping first, then legacy mapping."""
    symbol=str(ticker or "").upper().strip().split(".",1)[0]
    errors=[]
    # Current SEC exchange-aware file. Schema is {fields:[...], data:[[...], ...]}.
    try:
        raw,_=_get("https://www.sec.gov/files/company_tickers_exchange.json",headers,30)
        j=json.loads(raw.decode("utf-8"))
        fields=j.get("fields") or []
        for vals in j.get("data") or []:
            row=dict(zip(fields,vals))
            if str(row.get("ticker") or "").upper()==symbol:
                return int(row.get("cik")), row, errors
    except Exception as e:
        errors.append("exchange_map:"+type(e).__name__)
    # SEC legacy ticker map fallback.
    try:
        raw,_=_get("https://www.sec.gov/files/company_tickers.json",headers,30)
        j=json.loads(raw.decode("utf-8"))
        for row in j.values():
            if str(row.get("ticker") or "").upper()==symbol:
                return int(row.get("cik_str")), row, errors
    except Exception as e:
        errors.append("ticker_map:"+type(e).__name__)
    return None,{},errors


def sec_archive(ticker, limit=250, include_regulatory=False):
    """Retrieve investor-relevant filings from the official SEC submissions API.

    V21.2.96 deliberately avoids an extra SEC request per filing. The previous
    implementation probed every filing index looking for a PDF, which made the
    overview card fragile and could trigger throttling. EDGAR's primary document
    is authoritative and is normally HTML, so the card links directly to it.
    """
    headers=_sec_headers(); diagnostics=[]
    cik,match,map_errors=_sec_ticker_to_cik(ticker,headers)
    diagnostics.extend(map_errors)
    if not cik:
        df=pd.DataFrame(columns=["Date","Time","Group","Type","Title","Price Sensitive","Source","PDFURL","ReadURL","IndexURL","URL","Has PDF","ID"])
        df.attrs.update({"status":"CIK_RESOLUTION_FAILED","ticker":str(ticker),"diagnostics":diagnostics})
        return df
    try:
        url=f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        raw,_=_get(url,headers,30)
        j=json.loads(raw.decode("utf-8")); recent=(j.get("filings") or {}).get("recent") or {}
    except Exception as e:
        df=pd.DataFrame(columns=["Date","Time","Group","Type","Title","Price Sensitive","Source","PDFURL","ReadURL","IndexURL","URL","Has PDF","ID"])
        df.attrs.update({"status":"SEC_REQUEST_FAILED","ticker":str(ticker),"cik":cik,"diagnostics":diagnostics+[type(e).__name__]})
        return df
    rows=[]
    forms=recent.get("form") or []
    for i,form in enumerate(forms):
        if not include_regulatory and form not in INVESTOR_FORMS: continue
        try:
            accession=(recent.get("accessionNumber") or [])[i]
            primary=(recent.get("primaryDocument") or [])[i]
            filed=(recent.get("filingDate") or [])[i]
        except Exception:
            continue
        primary_url,index_url=_sec_primary_url(cik,accession,primary)
        rows.append({"Date":filed,"Time":"","Group":_sec_group(form),"Type":form,
                     "Title":_sec_label(form,primary),"Price Sensitive":False,"Source":"SEC EDGAR",
                     "PDFURL":"","ReadURL":primary_url,"IndexURL":index_url,"URL":primary_url,
                     "Has PDF":False,"ID":accession})
        if len(rows)>=limit: break
    df=pd.DataFrame(rows)
    df.attrs.update({"status":"OK" if rows else "NO_INVESTOR_FILINGS","ticker":str(ticker),"cik":cik,
                     "company":j.get("name") or match.get("name") or match.get("title") or "",
                     "diagnostics":diagnostics,"source":"SEC submissions API"})
    return df


def announcement_provenance(ticker, coverage=""):
    t=str(ticker or "").upper()
    if t.endswith(".AX"):
        if "Provider-backed" in str(coverage):
            return {"authority":"Licensed/authorised ASX announcement provider","coverage":str(coverage),"document_policy":"Open original source document; do not silently re-host it."}
        return {"authority":"ASX public company-announcement search","coverage":str(coverage or "ASX public archive fallback"),"document_policy":"Open the original ASX-hosted announcement document. Public-site access is best-effort; production redistribution may require an ASX data licence."}
    return {"authority":"U.S. SEC EDGAR","coverage":str(coverage or "SEC EDGAR"),"document_policy":"Open the original SEC filing/document from sec.gov."}

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

        # Provider unavailable/empty: try ASX's current public company/announcement
        # routes first. This is exchange-driven and works for any selected ASX code.
        p=asx_modern_company_page(code,limit)
        if p is not None and not p.empty:
            return p,"ASX Market Announcements"

        # Secondary ASX JSON route (availability varies by deployment/ASX changes).
        p=asx_company_announcements_api(code,limit)
        if p is not None and not p.empty:
            return p,"ASX company announcements feed"

        # Final official-ASX legacy fallback.
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

# --- V21.2.92 Global Exchange Announcement & Filing Resolution Engine ---
GLOBAL_MARKETS = {
    "ASX": {"country":"Australia", "authority":"ASX Market Announcements", "portal":"https://www.asx.com.au/asx/v2/statistics/announcements.do"},
    "NASDAQ": {"country":"United States", "authority":"U.S. SEC EDGAR", "portal":"https://www.sec.gov/edgar/search/"},
    "NYSE": {"country":"United States", "authority":"U.S. SEC EDGAR", "portal":"https://www.sec.gov/edgar/search/"},
    "LSE": {"country":"United Kingdom", "authority":"London Stock Exchange / issuer regulatory disclosures", "portal":"https://www.londonstockexchange.com/news"},
    "HKEX": {"country":"Hong Kong", "authority":"HKEXnews", "portal":"https://www.hkexnews.hk/"},
    "TSE": {"country":"Japan", "authority":"JPX TDnet", "portal":"https://www.jpx.co.jp/english/listing/disclosure/"},
    "TSX": {"country":"Canada", "authority":"SEDAR+ / issuer regulatory disclosures", "portal":"https://www.sedarplus.ca/"},
}

def resolve_announcement_market(ticker, exchange="", country=""):
    """Resolve the selected *listing*, never the issuer name alone.
    Suffix wins, then supplied exchange/country, then bare symbols default to US only.
    """
    t=str(ticker or "").upper().strip(); ex=str(exchange or "").upper().strip(); co=str(country or "").upper().strip()
    # V21.3.04 — normalize common provider exchange labels/MICs before routing.
    ex_alias={"ASX":"ASX","AUSTRALIAN SECURITIES EXCHANGE":"ASX","XASX":"ASX",
              "NMS":"NASDAQ","NGM":"NASDAQ","NCM":"NASDAQ","NAS":"NASDAQ","XNAS":"NASDAQ",
              "NYQ":"NYSE","NYE":"NYSE","ASE":"NYSE","AMEX":"NYSE","XNYS":"NYSE",
              "LSE":"LSE","LONDON STOCK EXCHANGE":"LSE","XLON":"LSE",
              "HKG":"HKEX","HKEX":"HKEX","HONG KONG STOCK EXCHANGE":"HKEX","XHKG":"HKEX",
              "JPX":"TSE","TSE":"TSE","TOKYO STOCK EXCHANGE":"TSE","XTKS":"TSE",
              "TOR":"TSX","TSX":"TSX","TORONTO STOCK EXCHANGE":"TSX","XTSE":"TSX"}
    ex=ex_alias.get(ex,ex)
    if t.endswith(".AX") or "ASX" in ex or "AUSTRAL" in ex: market="ASX"
    elif t.endswith(".L") or "LONDON" in ex or ex in {"LSE","LSEIOB"}: market="LSE"
    elif t.endswith(".HK") or "HONG KONG" in ex or ex in {"HKG","HKEX"}: market="HKEX"
    elif t.endswith(".T") or "TOKYO" in ex or ex in {"JPX","TSE"}: market="TSE"
    elif t.endswith(".TO") or t.endswith(".V") or "TORONTO" in ex or ex in {"TSX","TSXV"}: market="TSX"
    elif "NASDAQ" in ex or ex in {"NMS","NGM","NCM"}: market="NASDAQ"
    elif "NYSE" in ex or ex in {"NYQ","ASE","AMEX"}: market="NYSE"
    elif co in {"AUSTRALIA"}: market="ASX"
    elif co in {"UNITED KINGDOM","UK"}: market="LSE"
    elif co in {"HONG KONG"}: market="HKEX"
    elif co in {"JAPAN"}: market="TSE"
    elif co in {"CANADA"}: market="TSX"
    elif "." not in t: market="NASDAQ"  # bare Yahoo US listings; SEC resolver validates ticker->CIK
    else: market="UNKNOWN"

    # V21.3.03 — last-resort listing identity enrichment. Some provider/search paths
    # preserve the Yahoo-qualified ticker but lose exchange/country metadata before
    # the Command Centre renders. Resolve that identity from Yahoo's public search
    # metadata instead of silently routing a non-US listing to SEC.
    if market=="UNKNOWN" and t:
        try:
            qurl="https://query1.finance.yahoo.com/v1/finance/search?"+urllib.parse.urlencode({"q":t,"quotesCount":10,"newsCount":0})
            raw,_=_get(qurl,{"User-Agent":"Mozilla/5.0 Market-Investment-Analyst","Accept":"application/json"},12)
            payload=json.loads(raw.decode("utf-8","ignore"))
            exact=None
            for q in payload.get("quotes",[]):
                if str(q.get("symbol") or "").upper()==t:
                    exact=q; break
            if exact:
                yex=str(exact.get("exchange") or exact.get("exchDisp") or "").upper()
                # Re-enter the deterministic resolver with discovered metadata.
                if yex and yex!=ex:
                    return resolve_announcement_market(t,yex,country)
        except Exception:
            pass
    meta=GLOBAL_MARKETS.get(market,{"country":country or "Unknown","authority":"Official disclosure source unresolved","portal":""})
    return {"ticker":t,"market":market,**meta}

def _generic_official_provider(ticker, market, limit=250):
    """Optional authorised adapters for markets whose public sites do not expose a stable redistribution API.
    Configure e.g. LSE_ANNOUNCEMENTS_API_URL / HKEX_ANNOUNCEMENTS_API_URL / TSE_ANNOUNCEMENTS_API_URL / TSX_ANNOUNCEMENTS_API_URL.
    The adapter expects normalized JSON and never substitutes SEC data for a non-US listing.
    """
    api_url=os.getenv(f"{market}_ANNOUNCEMENTS_API_URL","").strip()
    api_key=os.getenv(f"{market}_ANNOUNCEMENTS_API_KEY","").strip()
    if not api_url:return pd.DataFrame()
    sep="&" if "?" in api_url else "?"
    url=api_url+sep+urllib.parse.urlencode({"ticker":ticker,"limit":limit})
    headers={"User-Agent":UA,"Accept":"application/json"}
    if api_key:headers["Authorization"]="Bearer "+api_key
    try:
        raw,_=_get(url,headers); j=json.loads(raw.decode())
        data=j.get("results") or j.get("data") or (j if isinstance(j,list) else [])
        rows=[]
        for x in data:
            doc=x.get("pdf_url") or x.get("document_url") or x.get("url") or ""
            rows.append({"Date":x.get("date") or x.get("filing_date") or x.get("release_date") or "",
                         "Time":x.get("time") or "","Group":x.get("group") or f"{market} Announcements",
                         "Type":x.get("type") or x.get("document_type") or "Announcement",
                         "Title":x.get("title") or x.get("headline") or "Announcement","Price Sensitive":bool(x.get("price_sensitive")),
                         "Source":x.get("source") or GLOBAL_MARKETS[market]["authority"],"URL":doc,
                         "PDFURL":x.get("pdf_url") or "","ReadURL":doc,"Has PDF":str(doc).lower().split("?")[0].endswith(".pdf"),
                         "ID":str(x.get("id") or x.get("announcement_number") or "")})
        return pd.DataFrame(rows)
    except Exception:return pd.DataFrame()


def _issuer_ir_fallback(ticker, market, limit=250):
    """Best-effort issuer-owned disclosure fallback.

    Uses the issuer website reported by the market-data provider, then follows a
    small set of investor/news/report links. Only issuer-owned pages/documents are
    returned. This is a fallback when a jurisdiction does not expose a stable
    machine-readable public feed; it never fabricates filings.
    """
    try:
        import yfinance as yf
        info=yf.Ticker(str(ticker)).get_info() or {}
        root=str(info.get('website') or '').strip()
    except Exception:
        root=''
    if not root.startswith('http'): return pd.DataFrame()
    host=urllib.parse.urlparse(root).netloc.lower().removeprefix('www.')
    headers={'User-Agent':'Mozilla/5.0 (compatible; ChrimataResearch/21.3.05)','Accept':'text/html,*/*'}
    pages=[root]
    seen_pages=set(); rows=[]; seen_docs=set()
    keywords=('investor','announcement','news','report','results','financial','filing','regulatory','disclosure')
    for page_url in list(pages):
        if page_url in seen_pages: continue
        seen_pages.add(page_url)
        try:
            raw,ct=_get(page_url,headers,18); txt=raw.decode('utf-8','ignore')
        except Exception:
            continue
        # discover a few issuer-owned investor/report pages
        for href,label in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',txt,flags=re.I|re.S):
            label=re.sub(r'<[^>]+>',' ',label); label=re.sub(r'\s+',' ',label).strip()
            u=urllib.parse.urljoin(page_url,href)
            ph=urllib.parse.urlparse(u).netloc.lower().removeprefix('www.')
            if ph!=host: continue
            low=(u+' '+label).lower()
            if any(k in low for k in keywords) and u not in pages and len(pages)<8:
                pages.append(u)
            if (u.lower().split('?')[0].endswith('.pdf') or any(k in low for k in ('annual report','half year','quarterly','results','presentation','announcement'))) and u not in seen_docs:
                dm=re.search(r'\b(20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]20\d{2})\b',label)
                rows.append({'Date':dm.group(1) if dm else '', 'Time':'','Group':f'{market} Issuer Disclosures',
                    'Type':classify(label),'Title':label or 'Issuer disclosure','Price Sensitive':False,
                    'Source':'Issuer investor relations','URL':u,'PDFURL':u if u.lower().split('?')[0].endswith('.pdf') else '',
                    'ReadURL':u,'Has PDF':u.lower().split('?')[0].endswith('.pdf'),'ID':u})
                seen_docs.add(u)
        if len(rows)>=limit: break
    if not rows:return pd.DataFrame()
    df=pd.DataFrame(rows).drop_duplicates('URL')
    df['_d']=pd.to_datetime(df['Date'],dayfirst=True,errors='coerce')
    return df.sort_values('_d',ascending=False,na_position='last').drop(columns='_d').head(limit).reset_index(drop=True)

def announcements_global(ticker, provider_url="", provider_key="", limit=250, exchange="", country=""):
    ident=resolve_announcement_market(ticker,exchange,country); market=ident["market"]
    if market=="ASX":
        # V21.3.08: routing is exchange-driven, not suffix-driven. Company Search
        # can legitimately persist an ASX identity whose provider symbol is QAN or
        # QAN.AX. Always canonicalise to the Yahoo/Chrímata ASX form before calling
        # the legacy adapter, otherwise `announcements()` falls through to SEC.
        asx_code=re.sub(r"[^A-Z0-9]", "", str(ticker or "").upper().replace(".AX", ""))[:3]
        asx_ticker=(asx_code+".AX") if asx_code else str(ticker or "")
        df,cov=announcements(asx_ticker,provider_url,provider_key,limit)
        if df is not None and not df.empty:
            return df,cov,ident
        ir=_issuer_ir_fallback(ticker,market,limit)
        if ir is not None and not ir.empty:
            return ir,"Issuer investor-relations fallback after ASX public search returned no parsed rows",ident
        return df,cov,ident
    if market in {"NASDAQ","NYSE"}:
        df=sec_archive(str(ticker).upper(),limit)
        return df,"SEC EDGAR submissions API",ident
    if market in {"LSE","HKEX","TSE","TSX"}:
        df=_generic_official_provider(ticker,market,limit)
        if df is not None and not df.empty:
            return df,f"{ident['authority']} configured feed",ident
        ir=_issuer_ir_fallback(ticker,market,limit)
        if ir is not None and not ir.empty:
            return ir,f"Issuer investor-relations fallback for {ident['authority']}",ident
        return pd.DataFrame(),f"{ident['authority']} — official portal available; no machine-readable feed or issuer fallback rows returned",ident
    return pd.DataFrame(),"Listing market could not be resolved",ident

def announcement_provenance_global(ticker, coverage="", exchange="", country=""):
    ident=resolve_announcement_market(ticker,exchange,country)
    return {"market":ident["market"],"country":ident["country"],"authority":ident["authority"],
            "coverage":coverage or ident["authority"],"portal":ident["portal"],
            "document_policy":"Open the original authoritative filing/disclosure document when a document URL is available. Chrímata does not fabricate missing filings."}

# ---------------------------------------------------------------------------
# V21.3.12 — Official Disclosure Provider Gateway
# One exchange-aware entry point for the production card/full disclosure page.
# ---------------------------------------------------------------------------

def _empty_disclosures(status, provider, ticker, diagnostics=None):
    cols=["Date","Time","Group","Type","Title","Price Sensitive","Source","PDFURL","ReadURL","IndexURL","URL","Has PDF","ID"]
    df=pd.DataFrame(columns=cols)
    df.attrs.update({"status":status,"provider":provider,"ticker":str(ticker or ""),"diagnostics":diagnostics or []})
    return df


def _sec_cik_from_company_atom(ticker, headers):
    """Official SEC fallback when ticker mapping JSON is unavailable/blocked."""
    symbol=str(ticker or "").upper().strip().split(".",1)[0]
    url="https://www.sec.gov/cgi-bin/browse-edgar?"+urllib.parse.urlencode({
        "action":"getcompany","CIK":symbol,"owner":"exclude","output":"atom","count":"10"
    })
    try:
        raw,_=_get(url,headers,30)
        txt=raw.decode("utf-8","ignore")
        # Atom company-info normally exposes CIK as a zero-padded integer.
        for pat in (r'<cik>(\d+)</cik>', r'CIK=(\d{6,10})', r'CIK\s*:?\s*(\d{6,10})'):
            m=re.search(pat,txt,re.I)
            if m: return int(m.group(1)), {"ticker":symbol,"source":"SEC company Atom"}, []
        return None,{},["atom:no_cik"]
    except Exception as e:
        return None,{},["atom:"+type(e).__name__+":"+str(e)[:120]]


def sec_archive_gateway(ticker, limit=250, include_regulatory=False):
    """SEC adapter with two independent official CIK-resolution routes."""
    headers=_sec_headers(); diagnostics=[]
    cik,match,errs=_sec_ticker_to_cik(ticker,headers); diagnostics.extend(errs)
    if not cik:
        cik,match2,errs2=_sec_cik_from_company_atom(ticker,headers); diagnostics.extend(errs2)
        if match2: match=match2
    if not cik:
        return _empty_disclosures("IDENTITY_FAILED","U.S. SEC EDGAR",ticker,diagnostics)
    try:
        endpoint=f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
        raw,ctype=_get(endpoint,headers,30)
        diagnostics.append({"endpoint":endpoint,"bytes":len(raw),"content_type":ctype})
        payload=json.loads(raw.decode("utf-8")); recent=((payload.get("filings") or {}).get("recent") or {})
    except Exception as e:
        diagnostics.append("submissions:"+type(e).__name__+":"+str(e)[:160])
        return _empty_disclosures("UPSTREAM_ERROR","U.S. SEC EDGAR",ticker,diagnostics)
    rows=[]; forms=recent.get("form") or []
    for i,form in enumerate(forms):
        if not include_regulatory and form not in INVESTOR_FORMS: continue
        try:
            accession=(recent.get("accessionNumber") or [])[i]
            primary=(recent.get("primaryDocument") or [])[i]
            filed=(recent.get("filingDate") or [])[i]
        except Exception: continue
        primary_url,index_url=_sec_primary_url(cik,accession,primary)
        rows.append({"Date":filed,"Time":"","Group":_sec_group(form),"Type":form,
                     "Title":_sec_label(form,primary),"Price Sensitive":False,"Source":"SEC EDGAR",
                     "PDFURL":"","ReadURL":primary_url,"IndexURL":index_url,"URL":primary_url,
                     "Has PDF":False,"ID":accession})
        if len(rows)>=limit: break
    if not rows:
        return _empty_disclosures("NO_DISCLOSURES","U.S. SEC EDGAR",ticker,diagnostics)
    df=pd.DataFrame(rows)
    df.attrs.update({"status":"SUCCESS","provider":"U.S. SEC EDGAR","ticker":str(ticker),"cik":int(cik),
                     "company":payload.get("name") or match.get("name") or match.get("title") or "",
                     "diagnostics":diagnostics,"source":"SEC submissions API"})
    return df


def official_disclosure_gateway(ticker, provider_url="", provider_key="", limit=250, exchange="", country=""):
    """Production disclosure gateway driven only by the currently selected listing.

    Returns (dataframe, coverage, identity).  Empty results retain a machine-readable
    status so the UI never confuses transport/identity failures with genuine no filings.
    """
    ident=resolve_announcement_market(ticker,exchange,country); market=ident.get("market","UNKNOWN")
    if market=="ASX":
        code=re.sub(r"[^A-Z0-9]","",str(ticker or "").upper().replace(".AX",""))[:3]
        if not code:
            return _empty_disclosures("IDENTITY_FAILED","ASX Market Announcements",ticker),"ASX Market Announcements",ident
        canonical=code+".AX"
        df,cov=announcements(canonical,provider_url,provider_key,limit)
        if df is not None and not df.empty:
            df.attrs["status"]="SUCCESS"; df.attrs["provider"]="ASX Market Announcements"; df.attrs["canonical_ticker"]=canonical
            return df,cov,ident
        # Preserve the deepest ASX diagnostics/status rather than flattening to "no rows".
        if df is None: df=_empty_disclosures("UPSTREAM_ERROR","ASX Market Announcements",canonical)
        elif not getattr(df,"attrs",{}).get("status"): df.attrs["status"]="UPSTREAM_ERROR"
        df.attrs["provider"]="ASX Market Announcements"; df.attrs["canonical_ticker"]=canonical
        return df,cov,ident
    if market in {"NASDAQ","NYSE"}:
        df=sec_archive_gateway(ticker,limit)
        return df,"SEC EDGAR submissions API",ident
    if market in {"LSE","HKEX","TSE","TSX"}:
        df=_generic_official_provider(ticker,market,limit)
        if df is not None and not df.empty:
            df.attrs.update({"status":"SUCCESS","provider":ident.get("authority",market)})
            return df,f"{ident['authority']} configured feed",ident
        ir=_issuer_ir_fallback(ticker,market,limit)
        if ir is not None and not ir.empty:
            ir.attrs.update({"status":"SUCCESS","provider":"Issuer investor relations"})
            return ir,f"Issuer investor-relations fallback for {ident['authority']}",ident
        return _empty_disclosures("UPSTREAM_ERROR",ident.get("authority",market),ticker),f"{ident['authority']} — no rows returned",ident
    return _empty_disclosures("IDENTITY_FAILED","Unresolved disclosure source",ticker),"Listing market could not be resolved",ident

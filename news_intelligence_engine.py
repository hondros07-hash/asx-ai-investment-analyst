from __future__ import annotations
import re
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf
from services.macro_mapper import get_exposure_matrix, primary_exposure_for_text

NEWS_COLUMNS=["Date","Published","Headline","Source","URL","Layer","Category","Relevance","Why it matters","Affected KPI","What to watch","Ticker","Macro Factor","Tracker","Transmission","Mapping"]

def _content(item):
    if not isinstance(item,dict): return {}
    return item.get('content') if isinstance(item.get('content'),dict) else item

def _url(c,item):
    for obj in (c,item):
        for k in ('canonicalUrl','clickThroughUrl'):
            v=obj.get(k) if isinstance(obj,dict) else None
            if isinstance(v,dict) and v.get('url'): return str(v['url'])
        for k in ('link','url'):
            if isinstance(obj,dict) and obj.get(k): return str(obj[k])
    return ''

def _row(item,ticker,layer='Company',ident=None):
    c=_content(item); title=str(c.get('title') or item.get('title') or '').strip()
    if not title:return None
    provider=c.get('provider') if isinstance(c.get('provider'),dict) else {}
    source=str(provider.get('displayName') or item.get('publisher') or 'Provider')
    raw=c.get('pubDate') or item.get('providerPublishTime') or ''
    dt=pd.NaT
    try:
        dt=pd.to_datetime(raw,unit='s',utc=True) if isinstance(raw,(int,float)) else pd.to_datetime(raw,utc=True)
    except Exception: pass
    text=title.lower(); category='General'; kpi='Business performance'; watch='Company updates and subsequent reporting'
    rules=[
      (('earnings','results','revenue','profit','ebit','margin'),'Earnings','Revenue / earnings / margins','Next result, guidance and estimate revisions'),
      (('guidance','outlook','forecast'),'Guidance','Forward earnings / valuation','Guidance changes and analyst revisions'),
      (('oil','fuel','crude','energy'),'Commodity / input costs','Input costs / margins','Commodity prices, hedging and pricing response'),
      (('rate','interest','bond yield'),'Rates','Financing cost / demand / valuation','Central-bank decisions and yield moves'),
      (('inflation','cpi'),'Inflation','Costs / pricing / margins','Inflation data, wages and pricing power'),
      (('currency','dollar','fx','aud','usd'),'FX','Revenue / costs / translation','Currency moves and hedging'),
      (('regulat','government','court','lawsuit'),'Regulatory / legal','Risk / costs / operations','Regulatory decisions and company response'),
      (('ceo','cfo','director','management'),'Management','Governance / execution','Leadership changes and strategy'),
      (('dividend','buyback','capital return'),'Capital management','Cash flow / shareholder returns','Cash generation and capital allocation'),
      (('strike','union','labour','labor','wage'),'Labour','Operating costs / operations','Industrial action, wages and disruption'),
    ]
    for keys,cat,k,w in rules:
        if any(x in text for x in keys): category,kpi,watch=cat,k,w; break
    ident=ident or {}
    exp=primary_exposure_for_text(title,ticker,ident.get('sector',''),ident.get('industry',''),ident.get('country',''))
    macro_factor=tracker=transmission=mapping='—'
    if exp:
        macro_factor=exp['factor']; tracker=exp['tracker']; transmission=exp['transmission']; mapping='Deterministic macro mapper'
        kpi=' / '.join(exp['affected_kpis'][:3])
        why=f"Structural exposure match: {macro_factor}. {transmission} Confirm magnitude against company disclosures, hedging and reported KPIs."
        watch=f"Watch {', '.join(exp['affected_kpis'][:3])}, company guidance and any mitigating hedges/pricing actions."
        relevance='High' if layer in ('Company','Macro') else 'Medium'
    else:
        why=(f"Potentially relevant to {ticker} through {kpi.lower()}. Confirm the magnitude against company disclosures and financial results.")
        relevance='High' if layer=='Company' else ('Medium' if layer=='Sector' else 'Context')
    return {'Date':('—' if pd.isna(dt) else dt.strftime('%d %b %Y')),'Published':dt,'Headline':title,'Source':source,'URL':_url(c,item),'Layer':layer,'Category':category,'Relevance':relevance,'Why it matters':why,'Affected KPI':kpi,'What to watch':watch,'Ticker':ticker,'Macro Factor':macro_factor,'Tracker':tracker,'Transmission':transmission,'Mapping':mapping}

def _search_news(query,count=12):
    try:
        s=yf.Search(query,max_results=1,news_count=count)
        return getattr(s,'news',None) or []
    except Exception:return []

def company_identity(ticker):
    out={'name':ticker,'sector':'','industry':''}
    try:
        info=yf.Ticker(ticker).info or {}
        out.update(name=str(info.get('longName') or info.get('shortName') or ticker),sector=str(info.get('sector') or ''),industry=str(info.get('industry') or ''))
    except Exception:pass
    return out

def news_intelligence(ticker, company_limit=30, sector_limit=15, macro_limit=15):
    ticker=str(ticker or '').strip().upper(); ident=company_identity(ticker); rows=[]
    try: items=getattr(yf.Ticker(ticker),'news',None) or []
    except Exception: items=[]
    if not items: items=_search_news(f"{ident['name']} {ticker}",company_limit)
    for x in items[:company_limit]:
        r=_row(x,ticker,'Company',ident)
        if r:rows.append(r)
    sq=' '.join(x for x in (ident['industry'],ident['sector']) if x).strip()
    if sq:
        for x in _search_news(sq,sector_limit):
            r=_row(x,ticker,'Sector',ident)
            if r:rows.append(r)
    matrix=get_exposure_matrix(ticker,ident.get('sector',''),ident.get('industry',''))
    _terms=[]
    for _exp in matrix['exposures']:
        _terms.extend(_exp.get('keywords',[])[:3])
    macro_q=' '.join(dict.fromkeys(_terms)) or 'interest rates inflation currency economy markets'
    for x in _search_news(macro_q,macro_limit):
        r=_row(x,ticker,'Macro',ident)
        if r:rows.append(r)
    df=pd.DataFrame(rows,columns=NEWS_COLUMNS)
    if df.empty:return df,ident
    df['_key']=df.Headline.astype(str).str.lower().str.replace(r'\W+',' ',regex=True).str.strip()
    df=df.drop_duplicates('_key').drop(columns='_key')
    df=df.sort_values('Published',ascending=False,na_position='last').reset_index(drop=True)
    return df,ident

def latest_company_news(ticker,limit=5):
    df,ident=news_intelligence(ticker,company_limit=max(limit*3,15),sector_limit=0,macro_limit=0)
    if df.empty:return df,ident
    return df[df.Layer.eq('Company')].head(limit).copy(),ident

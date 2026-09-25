
"""V22.1.0 standalone financial-engine adapters."""
from __future__ import annotations
from typing import Any, Dict, Optional
import math, pandas as pd, yfinance as yf
from services.thesis_engine import build_thesis_scorecard, ThesisThresholds
from services.valuation_engine import calculate_dcf_scenarios
from services.valuation_evidence import recover_financial_inputs
from services.technical_engine import calculate_technical_snapshot
from services.analyst_engine import build_analyst_payload
from services.forecast_engine import build_12m_forecast

def _finite(v: Any)->Optional[float]:
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:return None
def _frame(t,name):
    try:
        x=getattr(t,name); return x if isinstance(x,pd.DataFrame) else pd.DataFrame()
    except Exception:return pd.DataFrame()
def _series(df,names):
    if not isinstance(df,pd.DataFrame) or df.empty:return pd.Series(dtype=float)
    for n in names:
        if n in df.index:return pd.to_numeric(df.loc[n],errors="coerce").dropna()
    return pd.Series(dtype=float)
def _pair(s):
    if s is None or len(s)<1:return None,None
    a=list(s.iloc[:2]); return _finite(a[0]),(_finite(a[1]) if len(a)>1 else None)

def scorecard_for_ticker(ticker:str)->Dict[str,Any]:
    t=yf.Ticker(ticker); inc=_frame(t,"income_stmt"); cf=_frame(t,"cashflow")
    rev=_series(inc,["Total Revenue","Operating Revenue"]); op=_series(inc,["Operating Income"])
    fcf=_series(cf,["Free Cash Flow"])
    if fcf.empty:
        ocf=_series(cf,["Operating Cash Flow","Total Cash From Operating Activities"])
        capex=_series(cf,["Capital Expenditure","Capital Expenditures"])
        if not ocf.empty and not capex.empty: fcf=ocf.add(capex,fill_value=float("nan"))
    rc,rp=_pair(rev); oc,op=_pair(op); fc,fp=_pair(fcf)
    raw={"financials":[{"year":"prior","Revenue":rp,"Operating Income":op,"Free Cash Flow":fp},
                       {"year":"current","Revenue":rc,"Operating Income":oc,"Free Cash Flow":fc}]}
    x=build_thesis_scorecard(raw,ThesisThresholds()); x.update(security=ticker.upper(),provider="Yahoo Finance/yfinance",ai_calculated=False); return x

def valuation_for_ticker(ticker:str)->Dict[str,Any]:
    t=yf.Ticker(ticker)
    try:meta=t.info or {}
    except Exception:meta={}
    rec=recover_financial_inputs(meta,_frame(t,"cashflow"),_frame(t,"balance_sheet"),_frame(t,"income_stmt"))
    price=_finite(meta.get("currentPrice") or meta.get("regularMarketPrice"))
    fc,lc=rec.get("financial_currency"),rec.get("listing_currency")
    x=calculate_dcf_scenarios(rec.get("fcf"),rec.get("shares"),rec.get("cash"),rec.get("debt"),
        current_price=price,sector=rec.get("sector",""),industry=rec.get("industry",""),
        financial_currency=fc,listing_currency=lc,fx_rate_financial_to_listing=1.0 if fc and lc and fc==lc else None)
    x.update(audit=rec.get("audit",{}),security=ticker.upper(),ai_calculated=False); return x

def technicals_for_ticker(ticker:str)->Dict[str,Any]:
    h=yf.Ticker(ticker).history(period="1y",interval="1d",auto_adjust=False)
    x=calculate_technical_snapshot(h); x.update(security=ticker.upper(),provider="Yahoo Finance/yfinance",ai_calculated=False); return x

def consensus_for_ticker(ticker:str)->Dict[str,Any]:
    t=yf.Ticker(ticker)
    try:meta=t.info or {}
    except Exception:meta={}
    counts={}
    try:
        rec=getattr(t,"recommendations_summary",None)
        if rec is not None and len(rec):
            row=rec.iloc[0]; counts={k:row.get(k,0) for k in ("strongBuy","buy","hold","sell","strongSell")}
    except Exception:pass
    targets={}
    try:
        z=t.get_analyst_price_targets()
        if isinstance(z,dict):targets=z
    except Exception:pass
    x=build_analyst_payload(meta,counts,targets,_finite(meta.get("currentPrice") or meta.get("regularMarketPrice")),ticker,bridge=None)
    x["ai_calculated"]=False; return x

def forecast_for_ticker(ticker:str)->Dict[str,Any]:
    h=yf.Ticker(ticker).history(period="5y",interval="1d",auto_adjust=True); price=None
    if isinstance(h,pd.DataFrame) and not h.empty and "Close" in h:
        s=pd.to_numeric(h["Close"],errors="coerce").dropna(); price=_finite(s.iloc[-1]) if len(s) else None
    x=build_12m_forecast(h,current_price=price,security=ticker); x["ai_calculated"]=False; return x


# --- V23.1.0 Global Market Broadcast & Cache Engine ---------------------------
from services.market_registry import public_market_registry
from services.market_broadcast import broadcast_cache, serialize_record
from services.geo_router import resolve_market_layout

@app.get("/api/v1/markets/registry")
def chrimata_market_registry_v2310():
    return {"status":"ok","markets":public_market_registry()}

@app.get("/api/v1/markets/{market_code}/snapshot")
def chrimata_market_snapshot_v2310(market_code: str):
    code=market_code.upper()
    rec=broadcast_cache.get(code)
    if rec is None:
        return {"status":"unavailable","market":code,"data":None,
                "freshness":{"stale":True,"reason":"cache_not_warmed"}}
    return {"status":"ok",**serialize_record(code,rec)}

@app.get("/api/v1/markets/layout")
def chrimata_market_layout_v2310(country: str | None = None, tier: str = "free"):
    # Geo header resolution belongs at the trusted deployment edge; this endpoint accepts
    # the already-resolved country code and never trusts arbitrary X-Forwarded-For itself.
    return {"status":"ok",**resolve_market_layout(country,{"subscription_tier":tier})}


# --- V23.2.0 Supabase Identity, Profiles & Entitlement Foundation -------------
from fastapi import Depends
from utils.auth_gate import get_current_active_user
from services.profile_service import get_user_state
from services.geo_router import resolve_market_layout as _resolve_market_layout_v2320

@app.get("/api/v1/me")
def chrimata_me_v2320(user=Depends(get_current_active_user)):
    state=get_user_state(user)
    return {"status":"ok",**state}

@app.get("/api/v1/me/market-layout")
def chrimata_my_market_layout_v2320(user=Depends(get_current_active_user)):
    state=get_user_state(user)
    profile=state["profile"]; ent=state["entitlement"]
    layout=_resolve_market_layout_v2320(
        None,{"subscription_tier":ent["effective_plan"],
              "home_market":profile.get("home_market_override"),
              "custom_market_slots":profile.get("custom_market_slots") or []})
    return {"status":"ok",**layout}


# --- V23.2.1 Geo-Adaptive Global Index Header Ribbon contract ----------------
@app.get("/api/v1/header-markets")
def chrimata_header_markets_v2321(home_market: str = "AU"):
    from services.geo_router import resolve_market_layout
    from services.market_registry import MARKETS
    layout=resolve_market_layout(home_market,{"subscription_tier":"free"})
    ordered=[layout["home_market"]]+layout["secondary_markets"]
    items=[]
    for code in ordered[:5]:
        cfg=MARKETS.get(code)
        if not cfg: continue
        rec=broadcast_cache.get(code)
        items.append({"market":code,"country":cfg.country,"index":cfg.primary_index,"flag":cfg.flag,"snapshot":serialize_record(code,rec) if rec else None})
    return {"status":"ok","home_market":layout["home_market"],"items":items}

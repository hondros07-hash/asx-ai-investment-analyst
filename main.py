
from __future__ import annotations
# Local/VPS convenience only. Production platforms should inject secrets directly.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import math,os
from datetime import date,datetime
from typing import Any,Dict,Optional
import numpy as np,pandas as pd
from fastapi import FastAPI,HTTPException,Query
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,ConfigDict
from api_gateway import scorecard_for_ticker,valuation_for_ticker,valuation_summary_for_ticker,technicals_for_ticker,consensus_for_ticker,forecast_for_ticker,forecast_summary_for_ticker
from services.brief_engine import generate_research_brief
from services.dividend_api import dividend_calendar_payload

class APIResponse(BaseModel):
    model_config=ConfigDict(extra="forbid")
    status:str; ticker:str; data:Optional[Dict[str,Any]]=None; error:Optional[str]=None
class HealthResponse(BaseModel):
    status:str; engine_layer:str; version:str
class ResearchBriefData(BaseModel):
    status:str
    ticker:str
    brief_markdown_text:Optional[str]=None
    generated_timestamp:Optional[str]=None
    ai_calculated:bool=False
    ai_summarized:bool=False
    data_source:str
    evidence_coverage:str
    evidence_summary:Dict[str,Any]
    model:Optional[str]=None
def _origins():
    return [x.strip() for x in os.getenv("CHRIMATA_CORS_ORIGINS","http://localhost:3000").split(",") if x.strip()]
def _ticker(v:str)->str:
    x=(v or "").strip().upper()
    if not x or len(x)>32 or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.^=-_" for c in x):
        raise HTTPException(status_code=422,detail="Invalid ticker symbol")
    return x
def _native(v):
    if v is None or isinstance(v,(str,bool,int)):return v
    if isinstance(v,float):return v if math.isfinite(v) else None
    if isinstance(v,np.generic):return _native(v.item())
    if isinstance(v,(datetime,date,pd.Timestamp)):return v.isoformat()
    if isinstance(v,dict):return {str(k):_native(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,set)):return [_native(x) for x in v]
    if isinstance(v,pd.Series):return [_native(x) for x in v.tolist()]
    if isinstance(v,pd.DataFrame):return [_native(x) for x in v.to_dict(orient="records")]
    try:
        if pd.isna(v):return None
    except Exception:pass
    return str(v)

app=FastAPI(title="Chrímata Causal Economic Intelligence API",
 description="Decoupled gateway for deterministic Chrímata financial engines.",version="22.2.0")
_o=_origins()
app.add_middleware(CORSMiddleware,allow_origins=_o,allow_credentials="*" not in _o,
 allow_methods=["GET"],allow_headers=["Authorization","Content-Type"])

async def _run(ticker,fn,label):
    symbol=_ticker(ticker)
    try:return APIResponse(status="success",ticker=symbol,data=_native(await run_in_threadpool(fn,symbol)))
    except HTTPException:raise
    except Exception as exc:raise HTTPException(status_code=500,detail=f"{label} unavailable") from exc

@app.get("/api/v1/widget/scorecard",response_model=APIResponse)
async def scorecard(ticker:str=Query(...)):return await _run(ticker,scorecard_for_ticker,"Scorecard")
@app.get("/api/v1/widget/valuation",response_model=APIResponse)
async def valuation(ticker:str=Query(...)):return await _run(ticker,valuation_for_ticker,"Valuation")
@app.get("/api/v1/widget/valuation-summary",response_model=APIResponse)
async def valuation_summary(ticker:str=Query(...)):
    return await _run(ticker,valuation_summary_for_ticker,"Valuation summary")

@app.get("/api/v1/widget/technicals",response_model=APIResponse)
async def technicals(ticker:str=Query(...)):return await _run(ticker,technicals_for_ticker,"Technicals")
@app.get("/api/v1/widget/consensus",response_model=APIResponse)
async def consensus(ticker:str=Query(...)):return await _run(ticker,consensus_for_ticker,"Consensus")
@app.get("/api/v1/widget/forecast-summary",response_model=APIResponse)
async def forecast_summary(ticker:str=Query(...)):
    return await _run(ticker,forecast_summary_for_ticker,"Forecast summary")

@app.get("/api/v1/widget/forecast",response_model=APIResponse)
async def forecast(ticker:str=Query(...)):return await _run(ticker,forecast_for_ticker,"Forecast")
@app.get("/api/v1/widget/research-brief",response_model=ResearchBriefData)
async def research_brief(ticker:str=Query(...,description="Target ticker")):
    symbol=_ticker(ticker)
    try:
        return ResearchBriefData(**_native(await generate_research_brief(symbol)))
    except Exception as exc:
        raise HTTPException(status_code=503,detail="Research brief generation unavailable") from exc

@app.get("/health",response_model=HealthResponse)
async def health():return HealthResponse(status="operational",engine_layer="active",version="22.2.0")


# V23.4.4 — Responsive Global Dividend Intelligence Grid API
@app.get("/api/v1/corporate-actions/dividends")
async def dividend_calendar(market:str=Query("AU",min_length=2,max_length=2),horizon_days:int=Query(120,ge=1,le=365)):
    try:
        return _native(await run_in_threadpool(dividend_calendar_payload,market,horizon_days))
    except Exception as exc:
        raise HTTPException(status_code=503,detail="Dividend calendar unavailable") from exc

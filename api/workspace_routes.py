"""V24.2 read-only global research data. No personal portfolio or alert persistence."""
from datetime import datetime, timezone
from math import isfinite
from fastapi import APIRouter, HTTPException, Query
import yfinance as yf
from api.main import _provider, _ticker

router=APIRouter(prefix="/v1/workspace",tags=["global-workspace"])
MARKETS={
 "ASX":{"index":"^AXJO","currency":"AUD","exchange":"Australia"},
 "NASDAQ":{"index":"^IXIC","currency":"USD","exchange":"United States"},
 "NYSE":{"index":"^NYA","currency":"USD","exchange":"United States"},
 "LSE":{"index":"^FTSE","currency":"GBP","exchange":"United Kingdom"},
 "HKEX":{"index":"^HSI","currency":"HKD","exchange":"Hong Kong"},
 "TSE":{"index":"^N225","currency":"JPY","exchange":"Japan"},
 "TSX":{"index":"^GSPTSE","currency":"CAD","exchange":"Canada"},
}

def finite(value):
 try:
  v=float(value)
  return v if isfinite(v) else None
 except (TypeError,ValueError,OverflowError):return None

def quote(symbol):
 bars=yf.Ticker(symbol).history(period="5d",interval="1d",auto_adjust=True)
 if bars is None or bars.empty:return {"symbol":symbol,"price":None,"change_percent":None,"asof":None,"status":"unavailable"}
 close=bars["Close"].dropna()
 if close.empty:return {"symbol":symbol,"price":None,"change_percent":None,"asof":None,"status":"unavailable"}
 current=finite(close.iloc[-1]);prior=finite(close.iloc[-2]) if len(close)>1 else None
 return {"symbol":symbol,"price":current,"change_percent":(current/prior-1)*100 if current is not None and prior and prior>0 else None,
         "asof":bars.index[-1].isoformat(),"status":"provider_daily"}

@router.get("/markets")
def markets():
 def fetch():
  result=[]
  for code,meta in MARKETS.items():
   try:item=quote(meta["index"])
   except Exception:item={"symbol":meta["index"],"price":None,"change_percent":None,"asof":None,"status":"unavailable"}
   result.append({"market":code,"country":meta["exchange"],"currency":meta["currency"],**item})
  return result
 return {"markets":_provider(fetch),"source":"Yahoo Finance adjusted daily index history",
         "checked_at":datetime.now(timezone.utc).isoformat(),"live":False}

@router.get("/screen")
def screen(market: str=Query("ASX"),q: str=Query("",max_length=80),limit:int=Query(12,ge=1,le=20)):
 market=market.upper()
 if market not in MARKETS:raise HTTPException(422,"Unsupported market")
 if not q.strip():
  return {"market":market,"results":[],"status":"query_required","source":"Yahoo Finance search"}
 def fetch():
  found=yf.Search(q.strip(),max_results=limit*3,news_count=0).quotes or []
  results=[]
  suffix={"ASX":(".AX",),"NASDAQ":(),"NYSE":(),"LSE":(".L",),"HKEX":(".HK",),"TSE":(".T",),"TSX":(".TO",".V")}[market]
  for item in found:
   symbol=str(item.get("symbol") or "")
   exchange=str(item.get("exchange") or "").upper()
   matched=(symbol.upper().endswith(suffix) if suffix else exchange in (("NMS","NGM","NCM","NASDAQ") if market=="NASDAQ" else ("NYQ","NYSE","ASE","PCX")))
   if not matched:continue
   results.append({"symbol":symbol,"name":item.get("shortname") or item.get("longname") or symbol,"exchange":exchange})
   if len(results)>=limit:break
  return results
 return {"market":market,"results":_provider(fetch),"status":"provider_search","source":"Yahoo Finance search; not an exhaustive exchange screener",
         "checked_at":datetime.now(timezone.utc).isoformat()}

@router.get("/quote/{ticker}")
def workspace_quote(ticker:str):
 symbol=_ticker(ticker)
 return {"ticker":symbol,"quote":_provider(lambda:quote(symbol)),"source":"Yahoo Finance adjusted daily history",
         "live":False,"checked_at":datetime.now(timezone.utc).isoformat()}

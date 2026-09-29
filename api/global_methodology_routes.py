"""Deterministic global market methodology endpoints; no provider access."""
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from services.global_methodology_engine import MARKETS,market_identity,normalize_observation,compare_global
router=APIRouter(prefix="/v1/global-methodology",tags=["global-methodology"])
class ObservationIn(BaseModel):
 exchange:str; ticker:str; metric:str; value:str|int|float|None=None
 unit:str; currency:str|None=None; period:str; source_url:str; observed_at:str
@router.get("/markets")
def markets(): return {"markets":MARKETS,"status":"methodology_reference","live_prices":False}
@router.get("/identity/{exchange}/{ticker}")
def identity(exchange:str,ticker:str):
 try:return market_identity(exchange,ticker)
 except ValueError as exc:raise HTTPException(422,str(exc))
@router.post("/compare")
def compare(items:list[ObservationIn]=Field(min_length=2,max_length=2)):
 if len(items)!=2:raise HTTPException(422,"Exactly two observations required")
 try:
  left,right=[normalize_observation(item.model_dump()) for item in items]
  return {"left":left,"right":right,"comparison":compare_global(left,right)}
 except ValueError as exc:raise HTTPException(422,str(exc))

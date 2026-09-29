"""Stateless research model accountability endpoints. No claims of live track record."""
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from services.model_performance_engine import freeze_forecast,evaluate,aggregate
router=APIRouter(prefix="/v1/model-accountability",tags=["model-accountability"])
class ForecastIn(BaseModel):
 security_id:str=Field(min_length=1,max_length=40)
 model_id:str;model_version:str;issued_at:str;target_at:str;currency:str;horizon:str
 predicted_price:str;reference_price:str;assumptions_digest:str;source_digest:str
class OutcomeIn(BaseModel):
 security_id:str;currency:str;observed_at:str;price:str;source_url:str;verified:bool=False
class EvaluationIn(BaseModel):
 forecast:ForecastIn;outcome:OutcomeIn|None=None;as_of:str
@router.post("/freeze")
def freeze(body:ForecastIn):
 try:return freeze_forecast(body.model_dump())
 except ValueError as exc:raise HTTPException(422,str(exc))
@router.post("/evaluate")
def evaluation(body:EvaluationIn):
 try:return evaluate(freeze_forecast(body.forecast.model_dump()),body.outcome.model_dump() if body.outcome else None,as_of=body.as_of)
 except ValueError as exc:raise HTTPException(422,str(exc))

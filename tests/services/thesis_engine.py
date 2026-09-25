"""Deterministic financial thesis engine for Chrímata.

This module contains no AI/LLM calls. It accepts raw JSON/dict financial periods,
validates Revenue, Operating Income and Free Cash Flow, calculates YoY growth and
margins in Python/pandas, then evaluates explicit thresholds.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Mapping, Optional, Union
import json, math
import pandas as pd

@dataclass(frozen=True)
class ThesisThresholds:
    min_revenue_growth: float = 0.0
    min_operating_income_growth: float = 0.0
    min_fcf_growth: float = 0.0
    min_operating_margin: float = 0.0
    min_fcf_margin: float = 0.0

def _finite(v: Any) -> Optional[float]:
    try: x=float(v)
    except (TypeError,ValueError): return None
    return x if math.isfinite(x) else None

def _growth(cur: Optional[float], prior: Optional[float]) -> Optional[float]:
    if cur is None or prior is None or prior == 0: return None
    return (cur-prior)/abs(prior)

def _divide(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0: return None
    return a/b

def _pct(v: Optional[float]) -> Optional[float]:
    return None if v is None else round(v*100.0,2)

def _pick(row: Mapping[str,Any], *names: str) -> Any:
    for n in names:
        if n in row: return row[n]
    return None

def normalize_financials(raw: Union[str,Mapping[str,Any],List[Mapping[str,Any]]]) -> pd.DataFrame:
    if isinstance(raw,str):
        try: raw=json.loads(raw)
        except json.JSONDecodeError as exc: raise ValueError("Invalid financial JSON") from exc
    records=raw.get("financials") if isinstance(raw,Mapping) and "financials" in raw else ([raw] if isinstance(raw,Mapping) else raw)
    if not isinstance(records,list): raise TypeError("financials must be a list of periods")
    rows=[]
    for r in records:
        if not isinstance(r,Mapping): continue
        rows.append({
            "year": _pick(r,"year","fiscal_year","period"),
            "revenue": _finite(_pick(r,"revenue","Revenue","total_revenue","Total Revenue")),
            "operating_income": _finite(_pick(r,"operating_income","Operating Income","operatingIncome")),
            "free_cash_flow": _finite(_pick(r,"free_cash_flow","Free Cash Flow","freeCashFlow","FCF","fcf")),
        })
    if not rows: raise ValueError("No valid financial periods supplied")
    df=pd.DataFrame(rows)
    df["year"]=pd.to_numeric(df["year"],errors="coerce")
    if df["year"].isna().any(): raise ValueError("Every period requires a valid year")
    return df.assign(year=df["year"].astype(int)).sort_values("year").drop_duplicates("year",keep="last").reset_index(drop=True)

def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out=df.copy()
    for col,new in (("revenue","revenue_growth"),("operating_income","operating_income_growth"),("free_cash_flow","fcf_growth")):
        vals=out[col].tolist(); out[new]=[None if i==0 else _growth(_finite(vals[i]),_finite(vals[i-1])) for i in range(len(vals))]
    out["operating_margin"]=[_divide(_finite(a),_finite(b)) for a,b in zip(out.operating_income,out.revenue)]
    out["fcf_margin"]=[_divide(_finite(a),_finite(b)) for a,b in zip(out.free_cash_flow,out.revenue)]
    return out

def _rule(v: Any, threshold: float) -> Optional[bool]:
    x=_finite(v); return None if x is None else bool(x>=threshold)

def build_thesis_scorecard(raw: Union[str,Mapping[str,Any],List[Mapping[str,Any]]], thresholds: Optional[ThesisThresholds]=None) -> Dict[str,Any]:
    thresholds=thresholds or ThesisThresholds(); df=normalize_financials(raw)
    if len(df)<2: raise ValueError("At least two periods are required for YoY calculations")
    m=calculate_metrics(df); z=m.iloc[-1]; p=m.iloc[-2]
    score={
        "Revenue_Growth_On_Track":_rule(z.revenue_growth,thresholds.min_revenue_growth),
        "Operating_Income_Growth_On_Track":_rule(z.operating_income_growth,thresholds.min_operating_income_growth),
        "Free_Cash_Flow_Growth_On_Track":_rule(z.fcf_growth,thresholds.min_fcf_growth),
        "Operating_Margin_On_Track":_rule(z.operating_margin,thresholds.min_operating_margin),
        "Free_Cash_Flow_Margin_On_Track":_rule(z.fcf_margin,thresholds.min_fcf_margin),
    }
    metrics={
        "Revenue":_finite(z.revenue),"Revenue_YoY_Pct":_pct(_finite(z.revenue_growth)),
        "Operating_Income":_finite(z.operating_income),"Operating_Income_YoY_Pct":_pct(_finite(z.operating_income_growth)),"Operating_Margin_Pct":_pct(_finite(z.operating_margin)),
        "Free_Cash_Flow":_finite(z.free_cash_flow),"Free_Cash_Flow_YoY_Pct":_pct(_finite(z.fcf_growth)),"Free_Cash_Flow_Margin_Pct":_pct(_finite(z.fcf_margin)),
    }
    return {"latest_period":int(z.year),"previous_period":int(p.year),"metrics":metrics,"scorecard":score,"thresholds":asdict(thresholds),
            "verification":{"verified":True,"calculation_engine":"deterministic_python","ai_calculated_metrics":False,"periods_used":[int(p.year),int(z.year)]}}

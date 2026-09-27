"""AXÍA V23.8.0 — pure, portable contextual model routing.

Eligibility is not execution. Model implementations are registered in later
builds; missing inputs never become fabricated zeroes or valuation targets.
No Streamlit, provider/network or UI dependencies.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping, Any
import math

@dataclass(frozen=True)
class ModelSpec:
    key: str
    label: str
    required: tuple[str, ...]
    purpose: str

MODELS = {
    "fcff_dcf": ModelSpec("fcff_dcf","Free cash flow to firm DCF",("free_cash_flow","shares_outstanding","cash","debt","financial_currency","listing_currency"),"intrinsic_valuation"),
    "ddm": ModelSpec("ddm","Dividend discount model",("dividend_per_share","cost_of_equity","dividend_growth"),"intrinsic_valuation"),
    "multiples": ModelSpec("multiples","Comparable company multiples",("peer_set","valuation_metric","shares_outstanding"),"relative_valuation"),
    "residual_income": ModelSpec("residual_income","Residual income",("book_value_per_share","return_on_equity","cost_of_equity"),"intrinsic_valuation"),
    "nav": ModelSpec("nav","Net asset value",("asset_values","liabilities","shares_outstanding"),"asset_valuation"),
    "credit_unit_economics": ModelSpec("credit_unit_economics","Credit and transaction unit economics",("transaction_volume","revenue","credit_losses"),"operating_diagnostics"),
    "saas_unit_economics": ModelSpec("saas_unit_economics","SaaS unit economics",("annual_recurring_revenue","revenue_growth","operating_margin"),"operating_diagnostics"),
    "reit_affo": ModelSpec("reit_affo","REIT AFFO analysis",("funds_from_operations","maintenance_capex","shares_outstanding"),"operating_diagnostics"),
    "mine_nav": ModelSpec("mine_nav","Mine-level NAV",("reserve_schedule","commodity_price_assumptions","mine_cost_schedule"),"asset_valuation"),
}
ROUTES = {
    "bank": ("residual_income","ddm","multiples"),
    "insurance": ("residual_income","multiples"),
    "reit": ("nav","reit_affo","multiples"),
    "mining": ("mine_nav","fcff_dcf","multiples"),
    "bnpl": ("credit_unit_economics","fcff_dcf","multiples"),
    "saas": ("saas_unit_economics","fcff_dcf","multiples"),
    "high_growth": ("fcff_dcf","multiples"),
    "mature_dividend": ("fcff_dcf","ddm","multiples"),
    "general": ("fcff_dcf","multiples"),
}
def classify_company(profile: Mapping[str,Any]) -> str:
    sector=str(profile.get("sector") or "").lower()
    industry=str(profile.get("industry") or "").lower()
    description=str(profile.get("business_description") or "").lower()
    text=" ".join((sector,industry,description))
    if any(x in industry for x in ("reit","real estate investment trust")): return "reit"
    if any(x in industry for x in ("insurance","reinsurance")): return "insurance"
    if any(x in industry for x in ("bank","diversified financial")) and "bank" in industry: return "bank"
    if any(x in text for x in ("buy now pay later","bnpl","consumer lending","credit services")): return "bnpl"
    if any(x in industry for x in ("gold","copper","mining","metals","coal")): return "mining"
    if any(x in industry for x in ("software","saas")): return "saas"
    if profile.get("dividend_payer") is True and profile.get("mature_business") is True: return "mature_dividend"
    if profile.get("high_growth") is True: return "high_growth"
    return "general"

def _valid(value):
    if value is None or isinstance(value,bool): return False
    if isinstance(value,(int,float)): return math.isfinite(value)
    if isinstance(value,str): return bool(value.strip())
    return bool(value)

def select_models(profile: Mapping[str,Any], inputs: Mapping[str,Any]):
    category=classify_company(profile)
    results=[]
    for key in ROUTES[category]:
        spec=MODELS[key]
        missing=[field for field in spec.required if not _valid(inputs.get(field))]
        reason="Required inputs available" if not missing else "Missing verified inputs: "+", ".join(missing)
        if key=="ddm" and not (inputs.get("dividend_per_share") is not None and isinstance(inputs.get("dividend_per_share"),(int,float)) and inputs["dividend_per_share"]>0):
            missing=list(dict.fromkeys(missing+["positive_dividend_per_share"]))
            reason="Dividend model requires a positive, sustainable dividend"
        results.append({"key":key,"label":spec.label,"purpose":spec.purpose,
                        "status":"eligible" if not missing else "insufficient_data",
                        "missing_inputs":missing,"reason":reason})
    return {"classification":category,"selected_models":results,
            "executed_models":[],"model_results":{},
            "blended_fair_value":None,
            "valuation_status":"not_calculated",
            "methodology":"eligibility_only_v23.8.0"}

def research_manifest(ticker, profile, inputs, provenance=None):
    result=select_models(profile,inputs)
    result.update({"ticker":str(ticker).strip().upper(),
                   "input_provenance":dict(provenance or {}),
                   "model_library_version":"23.8.0"})
    return result

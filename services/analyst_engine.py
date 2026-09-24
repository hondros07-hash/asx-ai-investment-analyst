from __future__ import annotations
from typing import Any, Dict, Mapping, Optional
import math

RATING_KEYS=("strongBuy","buy","hold","sell","strongSell")
LABELS={"strong_buy":"Strong Buy","strongbuy":"Strong Buy","buy":"Buy","hold":"Hold",
        "underperform":"Underperform","sell":"Sell","strong_sell":"Strong Sell","strongsell":"Strong Sell"}

def _num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:return None

def normalize_consensus_label(value: Any) -> Optional[str]:
    if value is None:return None
    key=str(value).strip().lower().replace("-","_").replace(" ","_")
    return LABELS.get(key) or (str(value).strip().title() if str(value).strip() else None)

def deterministic_target_return(target_price: Any,current_price: Any) -> Optional[float]:
    t=_num(target_price); p=_num(current_price)
    return ((t/p)-1.0) if t is not None and p is not None and p>0 else None

def build_analyst_payload(provider_meta: Mapping[str,Any], recommendation_counts: Optional[Mapping[str,Any]],
                          price_targets: Optional[Mapping[str,Any]], current_price: Any,
                          selected_ticker: str, bridge: Optional[Mapping[str,Any]]=None,
                          fx_rate: Optional[float]=None, security_ratio: Optional[float]=None) -> Dict[str,Any]:
    """Deterministic analyst evidence. Provider consensus is preserved; no LLM arithmetic."""
    meta=dict(provider_meta or {}); counts=dict(recommendation_counts or {}); pt=dict(price_targets or {})
    provider_label=normalize_consensus_label(meta.get("recommendationKey"))
    clean_counts={k:int(_num(counts.get(k)) or 0) for k in RATING_KEYS}
    bucket_total=sum(clean_counts.values())
    provider_n=int(_num(meta.get("numberOfAnalystOpinions")) or 0)
    # Analyst count remains provider-reported when available. Bucket total is separately disclosed.
    analyst_count=provider_n or None
    target=_num(pt.get("mean")); target=target if target is not None else _num(meta.get("targetMeanPrice"))
    low=_num(pt.get("low")); low=low if low is not None else _num(meta.get("targetLowPrice"))
    median=_num(pt.get("median")); median=median if median is not None else _num(meta.get("targetMedianPrice"))
    high=_num(pt.get("high")); high=high if high is not None else _num(meta.get("targetHighPrice"))
    target_currency=meta.get("financialCurrency") or meta.get("currency")
    listing_currency=meta.get("currency")
    bridge=dict(bridge or {"status":"not_used","verified":False})
    normalized=False
    # A bridged target may only be transformed when issuer relationship, security ratio and FX are verified.
    if bridge.get("status")=="verified":
        ratio=_num(security_ratio); fx=_num(fx_rate)
        if ratio is None or ratio<=0:
            target=low=median=high=None
            bridge["target_bridge_status"]="blocked_missing_security_ratio"
        elif target_currency and listing_currency and str(target_currency).upper()!=str(listing_currency).upper() and (fx is None or fx<=0):
            target=low=median=high=None
            bridge["target_bridge_status"]="blocked_missing_fx"
        else:
            fx=fx or 1.0
            target=target*ratio*fx if target is not None else None
            low=low*ratio*fx if low is not None else None
            median=median*ratio*fx if median is not None else None
            high=high*ratio*fx if high is not None else None
            normalized=True; bridge["target_bridge_status"]="normalized"
    ret=deterministic_target_return(target,current_price)
    evidence={
        "security":selected_ticker,"identity_verified":bridge.get("status")!="rejected",
        "consensus_source":"provider_reported" if provider_label else "unavailable",
        "analyst_count_source":"provider_reported" if analyst_count else "unavailable",
        "target_source":"provider_reported" if target is not None else "unavailable",
        "target_return_source":"chrimata_deterministic" if ret is not None else "unavailable",
        "recommendation_bucket_total":bucket_total,"target_currency":target_currency,
        "listing_currency":listing_currency,"fx_rate":_num(fx_rate),
        "security_ratio":_num(security_ratio),"bridge":bridge,"normalized":normalized,
        "ai_calculated":False,
    }
    return {"status":"success" if provider_label or target is not None or bucket_total else "unavailable",
            "consensus_label":provider_label or "Unavailable","analyst_count":analyst_count,
            "target_price":target,"target_low":low,"target_median":median,"target_high":high,
            "percentage_return":ret,"recommendation_counts":clean_counts,
            "source":"Yahoo Finance via yfinance","evidence":evidence}

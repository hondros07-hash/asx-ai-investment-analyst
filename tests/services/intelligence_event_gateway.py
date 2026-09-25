"""Normalizes existing Chrímata evidence sources for the V23.4.1 integration engine."""
from __future__ import annotations
from typing import Any, Dict

ALLOWED_SOURCE_TYPES={"news","macro","company_report","announcement","fundamental","market_data"}

def normalize_event(payload:Dict[str,Any])->Dict[str,Any]:
    source_type=str(payload.get("source_type") or "").strip().lower()
    if source_type not in ALLOWED_SOURCE_TYPES:
        return {"status":"rejected","reason":"unsupported_source_type","source_type":source_type}
    event_key=str(payload.get("event_key") or "").strip()
    if not event_key:
        return {"status":"rejected","reason":"missing_event_key","source_type":source_type}
    return {
        "status":"accepted","source_type":source_type,"event_key":event_key,
        "direction":str(payload.get("direction") or "unknown").lower(),
        "what_changed":str(payload.get("what_changed") or ""),
        "why_it_matters":str(payload.get("why_it_matters") or ""),
        "time_horizon":str(payload.get("time_horizon") or "unknown"),
        "counteracting_factors":payload.get("counteracting_factors") or [],
    }

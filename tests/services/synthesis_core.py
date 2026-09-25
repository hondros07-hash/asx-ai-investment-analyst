"""Chrímata V23.4.0 — Causal Intelligence & Problem-Solving Core.

Contract:
Evidence -> Exposure -> KPI -> Impact Channel -> Thesis -> Monitoring.

This engine does not infer causation from correlation, calculate financial metrics, invent
exposures, or manufacture magnitude/confidence. Relationships must be supplied by verified
exposure rules and evidence packages.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Literal, Optional

Pressure = Literal["positive","negative","neutral","mixed","unknown"]
ThesisEffect = Literal["improving","deteriorating","watch","no_change","unknown"]

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_name: str
    source_type: str
    observed_at: str
    fact: str
    primary_source: bool = False
    verified: bool = False
    currency: Optional[str] = None
    url: Optional[str] = None

@dataclass(frozen=True)
class ExposureRule:
    exposure_key: str
    event_keys: List[str]
    affected_kpis: List[str]
    impact_channel: str
    positive_when: Optional[str] = None
    negative_when: Optional[str] = None
    thesis_conditions: List[str] = field(default_factory=list)
    valuation_variables: List[str] = field(default_factory=list)
    monitoring_items: List[str] = field(default_factory=list)

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _pressure(rule: ExposureRule, event_direction: str) -> Pressure:
    d=(event_direction or "").strip().lower()
    if d and rule.positive_when and d==rule.positive_when.lower(): return "positive"
    if d and rule.negative_when and d==rule.negative_when.lower(): return "negative"
    return "unknown"

def _evidence_quality(items: Iterable[Evidence]) -> Dict[str,Any]:
    xs=list(items)
    verified=sum(1 for x in xs if x.verified)
    primary=sum(1 for x in xs if x.verified and x.primary_source)
    # Evidence descriptors, not pseudo-probability scores.
    if not xs: level="insufficient"
    elif primary and verified==len(xs): level="strong"
    elif verified: level="supported"
    else: level="unverified"
    return {"level":level,"evidence_count":len(xs),"verified_count":verified,
            "verified_primary_count":primary}

class CausalSynthesisCore:
    def __init__(self, exposure_rules: Iterable[ExposureRule]):
        self.rules={r.exposure_key:r for r in exposure_rules}

    def synthesize(self, *, company: Dict[str,Any], event: Dict[str,Any],
                   company_exposure_keys: Iterable[str], evidence: Iterable[Evidence]) -> Dict[str,Any]:
        event_key=str(event.get("event_key") or "").strip()
        direction=str(event.get("direction") or "").strip().lower()
        ev=list(evidence)
        matches=[]
        for key in company_exposure_keys:
            rule=self.rules.get(key)
            if rule and event_key in rule.event_keys:
                matches.append(rule)

        if not matches:
            return {
                "status":"insufficient_mapping","company":company,"event":event,
                "relevance":{"mapped":False,"reason":"No verified company exposure rule maps this event to a corporate KPI."},
                "evidence_quality":_evidence_quality(ev),"evidence":[asdict(x) for x in ev],
                "missing_evidence":["verified_company_exposure_mapping"],
                "ai_calculated_math":False,"generated_at":_iso_now()
            }

        channels=[]
        all_kpis=[]; thesis=[]; valuation=[]; monitoring=[]
        pressures=set()
        for r in matches:
            p=_pressure(r,direction); pressures.add(p)
            channels.append({"exposure_key":r.exposure_key,"impact_channel_description":r.impact_channel,
                             "affected_kpis":r.affected_kpis,"directional_pressure":p})
            all_kpis.extend(r.affected_kpis); thesis.extend(r.thesis_conditions)
            valuation.extend(r.valuation_variables); monitoring.extend(r.monitoring_items)

        known={p for p in pressures if p!="unknown"}
        overall=(next(iter(known)) if len(known)==1 else ("mixed" if len(known)>1 else "unknown"))
        quality=_evidence_quality(ev)
        missing=[]
        if quality["verified_count"]==0: missing.append("verified_event_evidence")
        if overall=="unknown": missing.append("verified_directional_relationship")
        return {
            "status":"mapped","company":company,"event":event,
            "relevance":{"mapped":True,"matched_exposures":[r.exposure_key for r in matches]},
            "affected_kpis":list(dict.fromkeys(all_kpis)),
            "impact_channels":channels,
            "directional_pressure":overall,
            "magnitude":"unknown",
            "time_horizon":event.get("time_horizon") or "unknown",
            "evidence_quality":quality,
            "counteracting_factors":event.get("counteracting_factors") or [],
            "thesis_conditions_affected":list(dict.fromkeys(thesis)),
            "valuation_variables_affected":list(dict.fromkeys(valuation)),
            "evidence":[asdict(x) for x in ev],
            "missing_evidence":missing,
            "what_changed":event.get("what_changed") or "",
            "why_it_matters":event.get("why_it_matters") or "",
            "what_to_watch_next":list(dict.fromkeys(monitoring)),
            "thesis_change":self._thesis_effect(overall,quality),
            "provenance":{"currencies":sorted({x.currency for x in ev if x.currency}),
                          "sources":sorted({x.source_name for x in ev}),
                          "ai_calculated_math":False},
            "ai_calculated_math":False,"generated_at":_iso_now()
        }

    @staticmethod
    def _thesis_effect(pressure: Pressure, quality: Dict[str,Any]) -> ThesisEffect:
        if quality["level"] in {"insufficient","unverified"}: return "unknown"
        if pressure=="positive": return "improving"
        if pressure=="negative": return "deteriorating"
        if pressure=="mixed": return "watch"
        if pressure=="neutral": return "no_change"
        return "watch"

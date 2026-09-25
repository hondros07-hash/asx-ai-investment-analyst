"""Chrímata V23.4.1 — Evidence-to-Thesis Intelligence Integration Engine.

Orchestrates verified evidence from existing Chrímata engines into the V23.4.0 causal
contract. It does not scrape, calculate financial metrics, or invent company exposures.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional
from services.synthesis_core import CausalSynthesisCore, Evidence
from services.exposure_registry import DEFAULT_EXPOSURE_RULES

@dataclass(frozen=True)
class CompanyExposure:
    exposure_key: str
    verified: bool
    source_name: str
    evidence_id: str
    observed_at: str
    note: str = ""

def _dedupe(xs):
    return list(dict.fromkeys(x for x in xs if x))

class EvidenceToThesisEngine:
    def __init__(self, core: Optional[CausalSynthesisCore]=None):
        self.core=core or CausalSynthesisCore(DEFAULT_EXPOSURE_RULES)

    def resolve_verified_exposures(self, exposures: Iterable[CompanyExposure])->Dict[str,Any]:
        rows=list(exposures)
        verified=[x for x in rows if x.verified]
        return {
            "verified_keys":_dedupe([x.exposure_key for x in verified]),
            "verified_exposures":[asdict(x) for x in verified],
            "rejected_unverified_exposures":[asdict(x) for x in rows if not x.verified],
        }

    def integrate(self, *, company: Dict[str,Any], event: Dict[str,Any],
                  exposures: Iterable[CompanyExposure], evidence: Iterable[Evidence],
                  thesis_state: Optional[Dict[str,Any]]=None,
                  valuation_state: Optional[Dict[str,Any]]=None,
                  fundamentals_state: Optional[Dict[str,Any]]=None)->Dict[str,Any]:
        resolved=self.resolve_verified_exposures(exposures)
        result=self.core.synthesize(
            company=company,event=event,
            company_exposure_keys=resolved["verified_keys"],evidence=list(evidence)
        )
        result["exposure_resolution"]=resolved
        result["integration_inputs"]={
            "thesis_state_present":bool(thesis_state),
            "valuation_state_present":bool(valuation_state),
            "fundamentals_state_present":bool(fundamentals_state),
        }
        result["decision_package"]=self._decision_package(
            result, thesis_state or {}, valuation_state or {}, fundamentals_state or {}
        )
        return result

    def _decision_package(self, synthesis:Dict[str,Any], thesis:Dict[str,Any],
                          valuation:Dict[str,Any], fundamentals:Dict[str,Any])->Dict[str,Any]:
        if synthesis.get("status")!="mapped":
            return {
                "what_changed":synthesis.get("event",{}).get("what_changed") or "An event was detected.",
                "why_it_matters":"Chrímata cannot establish a verified company-specific transmission path.",
                "what_to_watch_next":synthesis.get("missing_evidence",[]),
                "what_would_change_the_thesis":["Obtain verified company exposure evidence before changing the thesis."],
                "thesis_status_change":"unknown",
                "valuation_link":{"status":"not_established"},
            }

        affected=set(synthesis.get("thesis_conditions_affected",[]))
        conditions=thesis.get("conditions",[]) if isinstance(thesis,dict) else []
        linked=[]
        for c in conditions if isinstance(conditions,list) else []:
            if isinstance(c,dict) and c.get("key") in affected:
                linked.append({"key":c.get("key"),"status":c.get("status"),"evidence":c.get("evidence")})

        variables=set(synthesis.get("valuation_variables_affected",[]))
        available_vars={}
        if isinstance(valuation,dict):
            for k,v in valuation.items():
                if k in variables and v is not None: available_vars[k]=v

        watch=_dedupe(synthesis.get("what_to_watch_next",[]))
        missing=_dedupe(synthesis.get("missing_evidence",[]))
        thesis_change=synthesis.get("thesis_change","unknown")
        change_items=[]
        if linked:
            change_items += [f"Reassess thesis condition '{x['key']}' when new verified evidence changes its status." for x in linked]
        else:
            change_items += [f"Obtain verified evidence for affected thesis condition '{x}'." for x in sorted(affected)]
        if missing: change_items += [f"Resolve missing evidence: {x}." for x in missing]

        return {
            "what_changed":synthesis.get("what_changed") or synthesis.get("event",{}).get("what_changed") or "",
            "why_it_matters":synthesis.get("why_it_matters") or (
                "Verified exposure maps this event to: "+", ".join(synthesis.get("affected_kpis",[]))
            ),
            "affected_kpis":synthesis.get("affected_kpis",[]),
            "linked_thesis_conditions":linked,
            "directional_pressure":synthesis.get("directional_pressure","unknown"),
            "magnitude":synthesis.get("magnitude","unknown"),
            "what_to_watch_next":watch,
            "what_would_change_the_thesis":_dedupe(change_items),
            "thesis_status_change":thesis_change,
            "valuation_link":{"status":"linked" if variables else "not_applicable",
                              "affected_variables":sorted(variables),
                              "verified_values_available":available_vars},
            "fundamentals_context_used":bool(fundamentals),
            "ai_calculated_math":False,
        }

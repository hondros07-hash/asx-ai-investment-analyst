from __future__ import annotations
from typing import Any, Dict, Iterable, Mapping, Optional

PASS={"met","on track","on_track","pass","passed","true","meeting"}
WATCH={"watch","warning","at risk","at_risk","attention","broken","fail","failed","false"}
PENDING={"pending","unknown","unavailable","insufficient evidence","insufficient_evidence",""}

def _norm(v: Any)->str:
    if v is True:return "on_track"
    if v is False:return "watch"
    if v is None:return "pending"
    return str(v).strip().lower()

def calculate_thesis_status(conditions: Any, expected_total: Optional[int]=None, source: str="Thesis Scorecard") -> Dict[str,Any]:
    """Aggregate verified thesis states only. Pending is unknown, never failure. No AI arithmetic."""
    rows=[]
    if hasattr(conditions,"to_dict"):
        try: rows=conditions.to_dict("records")
        except Exception: rows=[]
    elif isinstance(conditions,Mapping):
        rows=[{"metric":k,"status":v} if not isinstance(v,Mapping) else {"metric":k,**dict(v)} for k,v in conditions.items()]
    elif isinstance(conditions,Iterable) and not isinstance(conditions,(str,bytes)):
        rows=list(conditions)
    norm=[]
    for i,r in enumerate(rows):
        r=dict(r) if isinstance(r,Mapping) else {"status":r}
        st=_norm(r.get("status"))
        state="on_track" if st in PASS else ("watch" if st in WATCH else "pending")
        norm.append({"metric":r.get("metric") or r.get("condition") or f"condition_{i+1}",
                     "state":state,"evidence":r.get("evidence"),"source":r.get("source"),
                     "as_of":r.get("as_of") or r.get("updated_at"),"calculation_method":r.get("calculation_method")})
    configured=max(int(expected_total or 0),len(norm))
    if configured<=0: configured=6
    on_track=sum(x["state"]=="on_track" for x in norm)
    watch=sum(x["state"]=="watch" for x in norm)
    pending=max(0,configured-on_track-watch)
    evaluated=on_track+watch
    coverage=evaluated/configured if configured else 0.0
    # Evidence-aware state: do not call a thesis healthy from a tiny evidence sample.
    min_evidence=max(2,(configured+1)//2)  # at least half, rounded up, and never fewer than 2
    if evaluated<min_evidence:
        label="Insufficient Evidence"; ui_state="insufficient"
    elif watch>0:
        label="Watch"; ui_state="watch"
    elif on_track==configured and pending==0:
        label="All Conditions On Track"; ui_state="on_track"
    else:
        label="On Track"; ui_state="on_track"
    return {"status_label":label,"ui_state":ui_state,"total_conditions":configured,
            "on_track_count":on_track,"watch_count":watch,"pending_count":pending,
            "evaluated_count":evaluated,"evidence_coverage":coverage,
            "minimum_evidence_required":min_evidence,"conditions":norm,
            "provenance":{"source":source,"ai_calculated":False,"pending_is_failure":False}}

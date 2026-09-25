from typing import Any, Mapping, Optional
def _state(v:Any)->Optional[bool]:
    if v is True:return True
    if v is False:return False
    if v is None:return None
    if isinstance(v,str):
        x=v.strip().lower()
        if x in {"met","on track","on_track","pass","passed","true"}:return True
        if x in {"watch","warning","at risk","at_risk","attention","broken","fail","failed","false"}:return False
    return None
def calculate_research_score(thesis_results:Mapping[str,Any],weights:Optional[Mapping[str,float]]=None):
    thesis_results=thesis_results if isinstance(thesis_results,Mapping) else {};keys=list(thesis_results)
    if not keys:return {"research_score":None,"score_label":"Insufficient evidence","evidence_coverage":0,"maximum_score":100,"conditions":{},"calculation":"deterministic_python","ai_calculated":False}
    ws={}
    for k in keys:
        try:ws[k]=max(float((weights or {}).get(k,1)),0)
        except:ws[k]=1
    if sum(ws.values())<=0:ws={k:1 for k in keys}
    total=sum(ws.values());earned=evaluated=0;details={}
    for k in keys:
        state=_state(thesis_results[k]);w=ws[k]/total*100;points=w if state is True else (0 if state is False else None)
        if state is not None:evaluated+=w
        if state is True:earned+=w
        details[k]={"status":state,"weight":round(w,2),"points_earned":None if points is None else round(points,2)}
    score=round(earned);coverage=round(evaluated)
    label="Insufficient evidence" if coverage==0 else ("Weak evidence" if score<50 else ("Developing" if score<=75 else "Strong evidence"))
    return {"research_score":score,"score_label":label,"evidence_coverage":coverage,"maximum_score":100,"conditions":details,"calculation":"deterministic_python","ai_calculated":False}

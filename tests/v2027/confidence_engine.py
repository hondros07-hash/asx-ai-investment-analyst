
import numpy as np
import pandas as pd

def coverage_score(row, required_fields):
    if not required_fields:return 100.0
    present=sum(pd.notna(row.get(c)) for c in required_fields)
    return 100*present/len(required_fields)

def research_confidence(coverage, freshness=100, model_agreement=100,
                        provenance=100, sample_strength=100):
    vals=[coverage,freshness,model_agreement,provenance,sample_strength]
    vals=[float(v) for v in vals if v is not None and pd.notna(v)]
    return np.nan if not vals else float(np.clip(np.mean(vals),0,100))

def disagreement_confidence(disagreement):
    if disagreement is None or pd.isna(disagreement):return 50.0
    return float(np.clip(100*(1-min(float(disagreement)/.25,1)),0,100))

def freshness_score(age_days, stale_after=180):
    if age_days is None or pd.isna(age_days):return 0.0
    return float(np.clip(100*(1-float(age_days)/stale_after),0,100))

def data_health(frame, required):
    if frame is None or frame.empty:
        return {"status":"NO DATA","coverage":0}
    existing=[c for c in required if c in frame.columns]
    coverage=0 if not required else 100*len(existing)/len(required)
    null_rate=1.0 if not existing else float(frame[existing].isna().mean().mean())
    status="OK" if coverage>=90 and null_rate<.20 else "WARNING"
    return {"status":status,"schema_coverage":coverage,"null_rate":null_rate}

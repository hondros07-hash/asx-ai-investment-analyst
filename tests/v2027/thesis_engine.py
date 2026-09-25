
import operator
OPS={">":operator.gt,">=":operator.ge,"<":operator.lt,"<=":operator.le,"==":operator.eq}

def evaluate_rule(value,operator_symbol,threshold):
    if value is None or operator_symbol not in OPS:
        return "UNKNOWN"
    return "TRIGGERED" if OPS[operator_symbol](float(value),float(threshold)) else "OK"

def thesis_score(evidence_rows):
    weights={"high":3,"medium":2,"low":1}
    total=0; denom=0
    for r in evidence_rows:
        w=weights.get(str(r.get("materiality","low")).lower(),1)
        impact=str(r.get("thesis_impact","neutral")).lower()
        total += w if impact=="strengthens" else -w if impact=="weakens" else 0
        denom += w
    return 50 if denom==0 else max(0,min(100,50+50*total/denom))

def catalyst_calendar(evidence_df, days=90):
    if evidence_df is None or evidence_df.empty:return evidence_df
    # Expected-date events can be represented in notes as structured data in future adapters.
    return evidence_df[evidence_df["category"].isin(["catalyst","guidance","results","regulatory"])].copy()

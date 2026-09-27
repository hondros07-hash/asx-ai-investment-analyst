"""Conservative, explainable financial health indicator; not an investment rating."""
import math

WEIGHTS = {"Profitability":25, "Growth":20, "Balance sheet":20, "Cash flow":25, "Efficiency":10}

def _finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)

def _clamp(value):
    return max(0.0, min(100.0, float(value)))

def _scale(value, low, high):
    return _clamp(100 * (value - low) / (high - low))

def assess(data):
    """Return evidence-backed component scores and separate coverage/confidence."""
    periods = data.get("periods") or []
    sector = data.get("category") or "general"
    if not periods:
        return {"score":None,"confidence":0,"coverage":0,"components":[],"period":None,"sector":sector,
                "notes":["No usable financial statement period; assessment unavailable."]}
    period = periods[0]
    statements = data.get("statements") or {}
    income = statements.get("Income Statement") or {}
    balance = statements.get("Balance Sheet") or {}
    cash = statements.get("Cash Flow") or {}
    ratios = (data.get("ratios") or {}).get(period) or {}
    def field(table, name, p=period):
        return (table.get(name) or {}).get(p)
    revenue = field(income,"Revenue")
    net = field(income,"Net Income")
    operating = field(income,"Operating Income (EBIT)")
    ocf = field(cash,"Operating Cash Flow")
    fcf = field(cash,"Free Cash Flow")
    assets = field(balance,"Total Assets")
    debt = field(balance,"Total Debt")
    equity = field(balance,"Stockholders Equity")
    current = ratios.get("Current Ratio")
    margin = ratios.get("Operating Margin")
    net_margin = ratios.get("Net Margin")
    turnover = ratios.get("Asset Turnover")
    prev_revenue = field(income,"Revenue",periods[1]) if len(periods)>1 and data.get("frequency")!="TTM" else None
    growth = revenue/prev_revenue-1 if _finite(revenue) and _finite(prev_revenue) and prev_revenue>0 else None
    # Bank/credit models require regulatory and loan-book disclosures unavailable in generic statements.
    # Do not substitute conventional current ratios or debt/equity for bank capital adequacy.
    special = sector in ("bank","bnpl","resources","airline")
    evidence = {
      "Profitability":[("Operating margin",margin,lambda v:_scale(v,-.15,.25)),
                       ("Net margin",net_margin,lambda v:_scale(v,-.15,.20))],
      "Growth":[("Comparable revenue growth",growth,lambda v:_scale(v,-.20,.30))],
      "Balance sheet":([] if sector=="bank" else [
                       ("Current ratio",current,lambda v:_scale(v,.5,2.0)),
                       ("Debt / equity",ratios.get("Debt / Equity"),lambda v:100-_scale(v,0,3))]),
      "Cash flow":[("Operating cash flow / revenue",ocf/revenue if _finite(ocf) and _finite(revenue) and revenue>0 else None,lambda v:_scale(v,-.10,.25)),
                   ("Free cash flow / revenue",fcf/revenue if _finite(fcf) and _finite(revenue) and revenue>0 else None,lambda v:_scale(v,-.10,.20))],
      "Efficiency":[("Asset turnover",turnover,lambda v:_scale(v,0,2))],
    }
    components=[]
    earned=0.0
    covered=0.0
    total_possible=sum(len(items)*WEIGHTS[group]/len(items) for group,items in evidence.items() if items)
    for group,weight in WEIGHTS.items():
        items=evidence[group]
        observations=[]
        for label,value,transform in items:
            if _finite(value):
                observations.append({"metric":label,"value":value,"score":round(transform(value),1)})
        group_score=sum(item["score"] for item in observations)/len(observations) if observations else None
        # Missing inputs never count as zero; coverage tracks missing observations separately.
        group_coverage=len(observations)/len(items) if items else 0
        if group_score is not None:
            earned+=group_score*weight*group_coverage
        covered+=weight*group_coverage
        components.append({"name":group,"weight":weight,"score":round(group_score,1) if group_score is not None else None,
                           "coverage":round(group_coverage*100),"evidence":observations,
                           "missing":[label for label,value,_ in items if not _finite(value)] if items else ["Sector-specific verified metrics required"]})
    coverage=round(covered)
    notes=["Illustrative rule-based financial health model, not a valuation or buy/sell signal.",
           "Provider-transcribed statements are not independently reconciled to official filings.",
           "Thresholds are provisional; compare trends and source disclosures before relying on the indicator."]
    if special:
        notes.append("Sector-specific operating or regulatory metrics are not verified; generic ratios cannot establish complete sector financial health.")
    if data.get("frequency")=="TTM":
        notes.append("TTM flows and latest balance-sheet stocks use different measurement bases.")
    score=round(earned/covered) if covered>=60 and sector!="airline" else None
    if sector=="airline": notes.append("Airline composite withheld: sector-specific operating, fleet and financing evidence is not integrated; component ratios remain illustrative.")
    if score is None and sector!="airline": notes.append("Insufficient coverage (minimum 60%) to publish a composite score.")
    # Confidence reflects coverage and provenance; never equate provider coverage with audit verification.
    confidence=round(coverage*.65)
    return {"score":score,"confidence":confidence,"coverage":coverage,"components":components,
            "period":period,"sector":sector,"notes":notes}

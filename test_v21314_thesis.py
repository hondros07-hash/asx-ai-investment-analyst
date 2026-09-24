from services.thesis_engine import build_thesis_scorecard, ThesisThresholds

def test_deterministic_math_and_scorecard():
    raw={"financials":[{"year":2025,"Revenue":100,"Operating Income":10,"Free Cash Flow":5},{"year":2026,"Revenue":120,"Operating Income":15,"Free Cash Flow":8}]}
    r=build_thesis_scorecard(raw,ThesisThresholds(min_revenue_growth=.1,min_operating_margin=.1,min_fcf_growth=.1))
    assert r["metrics"]["Revenue_YoY_Pct"] == 20.0
    assert r["metrics"]["Operating_Margin_Pct"] == 12.5
    assert r["metrics"]["Free_Cash_Flow_YoY_Pct"] == 60.0
    assert r["scorecard"]["Revenue_Growth_On_Track"] is True
    assert r["verification"]["ai_calculated_metrics"] is False

def test_missing_is_pending_not_false():
    raw={"financials":[{"year":2025,"Revenue":100,"Operating Income":None,"Free Cash Flow":None},{"year":2026,"Revenue":110,"Operating Income":None,"Free Cash Flow":None}]}
    r=build_thesis_scorecard(raw)
    assert r["scorecard"]["Operating_Margin_On_Track"] is None
    assert r["scorecard"]["Free_Cash_Flow_Growth_On_Track"] is None

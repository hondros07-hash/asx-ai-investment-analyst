import pandas as pd
from services.valuation_evidence import recover_financial_inputs
def test_alias_and_newest_period():
    cf=pd.DataFrame({"2024-06-30":[100,-10],"2025-06-30":[150,-30]},index=["Total Cash From Operating Activities","Purchases Of PPE"])
    r=recover_financial_inputs({"sharesOutstanding":10},cf)
    assert r["fcf"]==120
def test_positive_capex_magnitude():
    cf=pd.DataFrame({"TTM":[200,50]},index=["Operating Cash Flow","Capital Expenditures"])
    assert recover_financial_inputs({"sharesOutstanding":10},cf)["fcf"]==150
def test_missing_is_explicit():
    r=recover_financial_inputs({"sharesOutstanding":10})
    assert r["audit"]["inputs"]["fcf"]["status"]=="missing"
def test_app_card_uses_audit_reason():
    s=open("app.py",encoding="utf-8").read()
    assert '"Missing: "+", ".join(_vmissing[:2])' in s
    assert '_ccauto_val=valuation_pipeline(ticker,price)' in s
def test_shares_history_fallback_wired():
    s=open("app.py",encoding="utf-8").read()
    assert 'shares_history(selected_ticker)' in s and 'provider_shares_history' in s

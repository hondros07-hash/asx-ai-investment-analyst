import pandas as pd
from services.valuation_evidence import recover_financial_inputs,verify_primary_listing_relationship
def test_metadata_first():
 r=recover_financial_inputs({"freeCashflow":100,"sharesOutstanding":10,"totalCash":3,"totalDebt":2,"financialCurrency":"USD","currency":"USD"})
 assert r["fcf"]==100 and r["audit"]["inputs"]["fcf"]["source"]=="provider_metadata"
def test_fcf_statement_derivation_negative_capex():
 cf=pd.DataFrame({"2025":[120,-20]},index=["Operating Cash Flow","Capital Expenditure"])
 r=recover_financial_inputs({"sharesOutstanding":10},cf)
 assert r["fcf"]==100 and r["audit"]["inputs"]["fcf"]["status"]=="derived"
def test_fcf_statement_derivation_positive_capex():
 cf=pd.DataFrame({"2025":[120,20]},index=["Operating Cash Flow","Capital Expenditure"])
 assert recover_financial_inputs({"sharesOutstanding":10},cf)["fcf"]==100
def test_balance_sheet_fallback():
 bs=pd.DataFrame({"2025":[50,30,10]},index=["Cash And Cash Equivalents","Total Debt","Ordinary Shares Number"])
 r=recover_financial_inputs({"freeCashflow":100},balance_sheet=bs)
 assert r["cash"]==50 and r["debt"]==30 and r["shares"]==10
def test_bridge_rejects_name_only():
 a={"longName":"NIKE, Inc.","sector":"Consumer Cyclical"};b={"longName":"NIKE, Inc.","sector":"Consumer Cyclical"}
 assert verify_primary_listing_relationship(a,b)["verified"] is False
def test_bridge_accepts_strong_identity():
 a={"longName":"NIKE, Inc.","website":"https://nike.com"};b={"longName":"NIKE, Inc.","website":"https://nike.com"}
 assert verify_primary_listing_relationship(a,b)["verified"] is True
def test_audit_marks_ai_false():
 assert recover_financial_inputs({})["audit"]["ai_calculated"] is False

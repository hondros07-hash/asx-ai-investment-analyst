import ast
from pathlib import Path
from services.valuation_summary_engine import summarize_valuation

def test_missing_input_diagnostic():
 r={"status":"unavailable","audit":{"inputs":{"fcf":{"status":"missing"}},"blocking_reasons":["Positive Free Cash Flow unavailable"]}}
 v=summarize_valuation(r,2.0,"TEST.AX")
 assert v["status"]=="insufficient_evidence" and "fcf" in v["missing_inputs"]
 assert v["reason"]=="Positive Free Cash Flow unavailable"
 assert v["bear_price"] is None

def test_reuse_canonical_scenarios():
 r={"status":"success","listing_currency":"AUD","scenarios":{n:{"value_per_share":p} for n,p in [("Bear",1),("Base",2),("Bull",3)]}}
 v=summarize_valuation(r,2,"TEST.AX")
 assert [v["scenarios"][n]["price"] for n in ("bear","base","bull")]==[1,2,3]
 assert v["base_delta_pct"]==0 and v["marker_positions_pct"]["base"]==50

def test_ui_spacing_and_message():
 s=Path("app.py").read_text();ast.parse(s)
 assert 'margin:2px 0 12px' in s and 'v23461-val-diagnostic' in s
 assert '{_vdiagnostic}</div>' in s
 assert 'def combine(quarterly, annual)' in s

def test_api_annual_quarterly_fallback():
 s=Path("api_gateway.py").read_text();ast.parse(s)
 assert '_merged(_frame(t,"quarterly_cashflow"),_frame(t,"cashflow"))' in s

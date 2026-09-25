import ast
def src(): return open("app.py",encoding="utf-8").read()
def test_single_source_used_by_overview_and_valuation():
 s=src(); assert '_ccauto_val=valuation_pipeline(ticker,price)' in s and '_vauto=valuation_pipeline(ticker,_vprice)' in s
def test_diagnostics_expose_required_chain():
 s=src()
 for x in ["Live Valuation Diagnostics","Selected security","DCF status","Positive FCF","Shares available","Currency aligned","Blocking reason","Provider statement rows received"]:
  assert x in s
def test_pipeline_records_blockers_and_rows():
 s=src()
 for x in ['audit["statement_rows"]','audit["eligibility_checks"]','audit["dcf_status"]','audit["blocking_reasons"]']:
  assert x in s
def test_compact_card_consumes_blocker():
 assert '_vblock=(_vaudit.get("blocking_reasons")' in src()
def test_app_parses(): ast.parse(src())

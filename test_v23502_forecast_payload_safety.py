import pandas as pd
from pathlib import Path
from services.forecast_widget_engine import summarize_forecast

def test_series_audit():
 x=summarize_forecast({"status":"unavailable","audit":pd.Series({"reason":"insufficient_history","diagnostics":pd.Series({"n":3})})},"ABC",100)
 assert x["status"]=="unavailable" and "insufficient_history" in x["missing_evidence"]
 assert x["validation"]["walk_forward_observations"]==3

def test_dataframe_audit():
 x=summarize_forecast({"status":"unavailable","audit":pd.DataFrame([{"reason":"no_model"}])},"ABC",100)
 assert "no_model" in x["missing_evidence"]

def test_empty_and_invalid_records():
 for a in (None, [], pd.Series(dtype=object),pd.DataFrame(),{"reason":pd.Series(["bad"])}):
  x=summarize_forecast({"status":"unavailable","audit":a},"ABC",None)
  assert x["status"]=="unavailable" and x["ai_calculated_math"] is False

def test_ready_preserved():
 x=summarize_forecast({"status":"ready","target_price":120,"forecast_return":.2,"audit":pd.Series({"diagnostics":pd.DataFrame([{"n":2}])})},"ABC",100)
 assert x["status"]=="ready" and x["target_price"]==120

def test_widget_error_boundary():
 assert 'forecast_summary_payload_error' in Path("app.py").read_text()

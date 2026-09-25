from services.forecast_widget_engine import summarize_forecast
def test_ready():
    x=summarize_forecast({"status":"ready","target_price":120,"forecast_return":.2,"audit":{"model_version":"test","diagnostics":{"n":30}}},100,"ABC")
    assert x["status"]=="ready" and len(x["sparkline_points"])==12
    assert abs(x["return_pct"]-20)<1e-8 and abs(x["sparkline_points"][-1]-120)<1e-8
    assert x["ai_calculated_math"] is False
    assert x["sparkline_kind"]=="endpoint_interpolation_not_monthly_forecast"
def test_missing_is_not_fabricated():
    x=summarize_forecast({"status":"unavailable","audit":{"reason":"history missing"}},100,"ABC")
    assert x["sparkline_points"]==[] and x["target_price"] is None
def test_invalid_reference():
    assert summarize_forecast({"status":"ready","target_price":10},0)["status"]=="unavailable"
def test_route():
    from pathlib import Path
    assert '@app.get("/api/v1/widget/forecast-summary"' in Path("main.py").read_text()
    assert "def forecast_summary_for_ticker" in Path("api_gateway.py").read_text()
def test_card():
    from pathlib import Path
    s=Path("app.py").read_text()
    assert '_fc_widget=_chr_forecast_summary(_fc12,price' in s
    assert '_fc_spark_html' in s

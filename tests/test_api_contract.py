"""API contract tests use local fixtures; never call Yahoo Finance."""
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
SNAPSHOT = {
    "ticker": "TEST", "currency": "AUD", "frequency": "Annual (5Y)",
    "periods": ["2026-06-30", "2025-06-30"], "provider_checked_at": "2026-09-28T00:00:00+00:00",
    "provider": "Yahoo Finance via yfinance", "meta": {},
    "statements": {"Income Statement": {
        "Revenue": {"2026-06-30": 110., "2025-06-30": 100.},
        "Operating Income (EBIT)": {"2026-06-30": 22., "2025-06-30": 20.},
        "Net Income": {"2026-06-30": 11., "2025-06-30": 10.}},
        "Cash Flow": {"Free Cash Flow": {"2026-06-30": 8., "2025-06-30": 7.}}},
    "ratios": {"2026-06-30": {"Operating Margin": .2},
               "2025-06-30": {"Operating Margin": .2}}}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_statements_and_kpis_share_snapshot():
    with patch("api.main._snapshot", return_value=SNAPSHOT):
        statement = client.get("/v1/companies/TEST/financial-statements")
        kpis = client.get("/v1/companies/TEST/kpis")
    assert statement.status_code == 200
    assert statement.json()["provenance"]["issuer_reconciled"] is False
    assert kpis.status_code == 200
    assert kpis.json()["metrics"]["Operating Income"]["value"] == 22
    assert len(kpis.json()["metrics"]) == 5


def test_invalid_ticker_and_period():
    assert client.get("/v1/companies/invalid!/kpis").status_code == 422
    assert client.get("/v1/companies/TEST/kpis?period=wrong").status_code == 422


def test_dcf_uses_existing_engine():
    response = client.post("/v1/valuations/dcf", json={
        "fcf": 1000000, "shares": 100000, "financial_currency": "AUD",
        "listing_currency": "AUD", "sector": "Technology"})
    assert response.status_code == 200
    assert response.json()["status"] in ("success", "unavailable")


def test_forecast_unavailable_for_insufficient_history():
    with patch("api.main._provider", return_value={
        "status": "unavailable", "forecast_return": None, "target_price": None}):
        response = client.post("/v1/forecasts/12m", json={"ticker": "TEST"})
    assert response.status_code == 200
    assert response.json()["forecast"]["status"] == "unavailable"


def test_json_safe_nonfinite():
    from api.main import _safe
    assert _safe({"value": float("nan"), "other": float("inf")}) == {"value": None, "other": None}

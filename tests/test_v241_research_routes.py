"""V24.1 read-only research endpoint contract tests; provider calls mocked."""
from unittest.mock import patch
import pandas as pd
from fastapi.testclient import TestClient
from api.main import app

client=TestClient(app)

def test_invalid_ticker_rejected():
    assert client.get("/v1/companies/INVALID!/technical").status_code == 422

def test_technical_empty_history_is_pending():
    with patch("api.research_routes._history",return_value=pd.DataFrame()):
        response=client.get("/v1/companies/ZIP.AX/technical")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "pending"

def test_quant_empty_history_has_no_invented_metrics():
    with patch("api.research_routes._history",return_value=pd.DataFrame()):
        response=client.get("/v1/companies/ZIP.AX/quant")
    assert response.status_code == 200
    assert response.json()["metrics"] == {}

def test_non_us_filings_do_not_claim_sec_coverage():
    response=client.get("/v1/companies/ZIP.AX/announcements")
    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert response.json()["filings"] == []

def test_report_intelligence_does_not_invent_ai_analysis():
    response=client.get("/v1/companies/ZIP.AX/report-intelligence")
    assert response.status_code == 200
    assert response.json()["analysis_status"] == "not_migrated"

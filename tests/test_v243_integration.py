"""Stage 4 integration and failure-boundary tests. No external provider calls."""
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from api.main import app, _CACHE, _snapshot
client=TestClient(app)

def test_health_contract():
 r=client.get("/health")
 assert r.status_code==200 and r.json()["version"]=="24.3.0"

def test_company_ticker_validation():
 assert client.get("/v1/companies/BAD!/kpis").status_code==422

def test_invalid_financial_snapshot_is_not_cached():
 with patch("api.main._provider",return_value={}):
  try:_snapshot("TEST.INVALID","Annual (5Y)")
  except HTTPException as error:assert error.status_code==503
  else:raise AssertionError("Empty provider result accepted")
 assert ("TEST.INVALID","Annual (5Y)") not in _CACHE

def test_market_validation_and_empty_screen():
 assert client.get("/v1/workspace/screen?market=UNKNOWN&q=abc").status_code==422
 r=client.get("/v1/workspace/screen?market=ASX")
 assert r.status_code==200 and r.json()["results"]==[]

def test_no_fabricated_non_us_filings():
 r=client.get("/v1/companies/ZIP.AX/announcements")
 assert r.status_code==200 and r.json()["filings"]==[] and r.json()["status"]=="unavailable"

def test_research_section_unknown_symbol_rejected():
 assert client.get("/v1/companies/BAD!/technical").status_code==422

def test_openapi_routes_are_registered():
 paths=client.get("/openapi.json").json()["paths"]
 for route in ("/v1/workspace/markets","/v1/workspace/screen","/v1/companies/{ticker}/technical",
               "/v1/companies/{ticker}/kpis","/v1/companies/{ticker}/financial-statements"):
  assert route in paths

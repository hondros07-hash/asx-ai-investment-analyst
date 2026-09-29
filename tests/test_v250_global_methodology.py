import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.global_methodology_engine import market_identity,normalize_observation,compare_global,MARKETS
from api.global_methodology_routes import router
def item(exchange="ASX",ticker="ZIP",currency="AUD",value="10",period="FY26"):
 return dict(exchange=exchange,ticker=ticker,metric="revenue",value=value,unit="currency",currency=currency,period=period,source_url="https://example.org/report",observed_at="2026-09-01T00:00:00Z")
def test_seven_markets_and_identity():
 assert len(MARKETS)==7 and market_identity("AX","ZIP")["security_id"]=="ASX:ZIP"
def test_no_silent_fx():
 a=normalize_observation(item());b=normalize_observation(item(exchange="NYSE",ticker="KO",currency="USD"))
 assert compare_global(a,b)["status"]=="not_comparable"
def test_missing_is_unavailable():
 a=normalize_observation(item());b=normalize_observation(item(value=None))
 assert compare_global(a,b)["status"]=="unavailable"
def test_period_guard():
 a=normalize_observation(item());b=normalize_observation(item(period="FY25"))
 assert compare_global(a,b)["status"]=="not_comparable"
def test_same_basis():
 a=normalize_observation(item());b=normalize_observation(item(ticker="BHP"))
 assert compare_global(a,b)["status"]=="comparable"
@pytest.mark.parametrize("field,value", [("source_url","http://example.org"),("observed_at","2026-01-01"),("value","NaN")])
def test_invalid_evidence(field,value):
 row=item();row[field]=value
 with pytest.raises(ValueError):normalize_observation(row)
def test_route():
 app=FastAPI();app.include_router(router);client=TestClient(app)
 assert len(client.get("/v1/global-methodology/markets").json()["markets"])==7
 assert client.post("/v1/global-methodology/compare",json=[item(),item()]).json()["comparison"]["status"]=="comparable"

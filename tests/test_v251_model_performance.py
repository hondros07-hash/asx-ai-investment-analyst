import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.model_performance_engine import freeze_forecast,evaluate,aggregate
from api.model_performance_routes import router
def forecast():
 return dict(security_id="ASX:ZIP",model_id="baseline",model_version="1.0",issued_at="2025-01-01T00:00:00Z",target_at="2025-04-01T00:00:00Z",currency="AUD",horizon="3M",predicted_price="3",reference_price="2",assumptions_digest="abc",source_digest="def")
def outcome():
 return dict(security_id="ASX:ZIP",currency="AUD",observed_at="2025-04-01T10:00:00Z",price="2.5",source_url="https://example.org/prices",verified=True)
def test_deterministic_record():
 assert freeze_forecast(forecast())["forecast_id"]==freeze_forecast(forecast())["forecast_id"]
def test_no_lookahead():
 assert evaluate(freeze_forecast(forecast()),outcome(),as_of="2025-03-31T00:00:00Z")["status"]=="pending"
def test_verified_outcome_required():
 o=outcome();o["verified"]=False
 assert evaluate(freeze_forecast(forecast()),o,as_of="2025-04-02T00:00:00Z")["status"]=="unavailable"
def test_error_and_direction():
 r=evaluate(freeze_forecast(forecast()),outcome(),as_of="2025-04-02T00:00:00Z")
 assert r["absolute_percentage_error"]=="20.0" and r["direction_correct"] is True
 assert aggregate([r])["sample_size"]==1
def test_no_sample_no_track_record():
 assert aggregate([])["status"]=="insufficient_evidence"
def test_bad_chronology():
 x=forecast();x["target_at"]=x["issued_at"]
 with pytest.raises(ValueError):freeze_forecast(x)
def test_endpoint():
 app=FastAPI();app.include_router(router);client=TestClient(app)
 assert client.post("/v1/model-accountability/freeze",json=forecast()).status_code==200

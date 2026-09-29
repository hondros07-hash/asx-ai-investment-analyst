import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.explainable_evidence_engine import observation, explain_calculation
from api.explainability_routes import router

def item(metric="revenue", value="10", **kw):
    row = dict(security_id="KO", metric=metric, value=value, unit="USD", period="FY25",
               source_name="Issuer filing", source_url="https://example.org/filing",
               observed_at="2025-12-31T00:00:00Z", verification="provider_transcribed",
               issuer_reconciled=False)
    row.update(kw)
    return row

def test_stable_fingerprint_and_provenance():
    assert observation(item())["evidence_id"] == observation(item())["evidence_id"]

def test_arithmetic_trace():
    result=explain_calculation("difference","subtract",[item(),item(value="7")],unit="USD",period="FY25")
    assert result["value"]=="3" and not result["issuer_verified"] and len(result["inputs"])==2

def test_missing_is_not_zero():
    assert explain_calculation("difference","subtract",[item(value=None,verification="unverified"),item()],unit="USD",period="FY25")["status"]=="unavailable"

@pytest.mark.parametrize("override", [{"period":"FY24"},{"security_id":"ZIP.AX"}])
def test_incompatible_identity(override):
    with pytest.raises(ValueError):
        explain_calculation("difference","subtract",[item(),item(**override)],unit="USD",period="FY25")

def test_cannot_claim_issuer_verification():
    with pytest.raises(ValueError):
        observation(item(verification="issuer_verified"))

def test_invalid_source_and_future_timestamp():
    with pytest.raises(ValueError): observation(item(source_url="http://example.org"))
    with pytest.raises(ValueError): observation(item(observed_at="2099-01-01T00:00:00Z"))

def test_division_by_zero():
    assert explain_calculation("ratio","divide",[item(),item(value="0")],unit="ratio",period="FY25")["status"]=="unavailable"

def test_endpoint():
    app=FastAPI();app.include_router(router);client=TestClient(app)
    payload={"metric":"difference","operator":"subtract","inputs":[item(),item(value="7")],"unit":"USD","period":"FY25"}
    assert client.post("/v1/explainability/calculate",json=payload).json()["value"]=="3"

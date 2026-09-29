import pytest
from services.research_memory_engine import compare_snapshots, evaluate_condition, evidence_digest

def evidence(**overrides):
    row = dict(security_id="ZIP.AX", metric="cash_ebitda", period="FY26",
               source_url="https://example.org/issuer-report.pdf",
               observed_at="2026-08-01T00:00:00Z", value=25, currency="AUD")
    row.update(overrides)
    return row

def condition(**overrides):
    row = dict(security_id="ZIP.AX", metric="cash_ebitda", period="FY26",
               operator=">=", threshold=20, currency="AUD")
    row.update(overrides)
    return row

def test_digest_is_deterministic():
    assert evidence_digest(evidence()) == evidence_digest(dict(reversed(list(evidence().items()))))

def test_rule_supported_and_contradicted():
    assert evaluate_condition(condition(), evidence())["state"] == "supported"
    assert evaluate_condition(condition(), evidence(value=10))["state"] == "contradicted"

@pytest.mark.parametrize("change", [{"security_id":"KO"}, {"period":"FY25"}, {"currency":"USD"}])
def test_identity_mismatch_is_unverified(change):
    assert evaluate_condition(condition(), evidence(**change))["state"] == "unverified"

def test_missing_evidence_not_invented():
    assert evaluate_condition(condition(), None)["state"] == "unverified"

def test_snapshot_diff_and_identity_guard():
    a = {"id":"a","security_id":"ZIP.AX","currency":"AUD","metrics":{"revenue":10}}
    b = {"id":"b","security_id":"ZIP.AX","currency":"AUD","metrics":{"revenue":12}}
    assert compare_snapshots(a,b)["changes"][0]["current"] == 12
    with pytest.raises(ValueError):
        compare_snapshots(a,dict(b,currency="USD"))

def test_bad_source_rejected():
    with pytest.raises(ValueError):
        evidence_digest(evidence(source_url="http://example.org"))

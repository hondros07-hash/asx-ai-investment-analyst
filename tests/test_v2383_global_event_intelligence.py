from services.global_event_intelligence_engine import normalize_global_event, attention_from_global_events

EVENT={"event_type":"central_bank","title":"Rate decision","source_url":"https://example.org/release",
       "published_at":"2026-09-27T01:00:00Z","jurisdictions":["AU"]}
PROFILE={"operating_countries":["AU"],"exposures":[{"channel":"funding_cost",
         "event_types":["central_bank"],"mechanism":"Review floating-rate funding exposure",
         "evidence_url":"https://example.org/company/filing"}]}
def test_sourced_exposure(): 
    out=attention_from_global_events("ZIP.AX",PROFILE,[EVENT])
    assert len(out)==1 and out[0]["assessment"]=="potential_exposure_not_quantified"
def test_unrelated_geography():
    assert attention_from_global_events("ZIP.AX",PROFILE,[dict(EVENT,jurisdictions=["JP"])])==[]
def test_missing_source_rejected():
    assert normalize_global_event(dict(EVENT,source_url="")) is None
def test_no_company_evidence_no_alert():
    assert attention_from_global_events("ZIP.AX",{"operating_countries":["AU"]},[EVENT])==[]
def test_proposed_policy_not_effective():
    p=dict(EVENT,event_type="government_policy",policy_status="proposed")
    assert normalize_global_event(p)["policy_status"]=="proposed"
def test_duplicate_event():
    assert len(attention_from_global_events("ZIP.AX",PROFILE,[EVENT,EVENT]))==1

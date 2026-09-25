from services.evidence_thesis_integration import EvidenceToThesisEngine,CompanyExposure
from services.synthesis_core import Evidence
from services.intelligence_event_gateway import normalize_event
from pathlib import Path

engine=EvidenceToThesisEngine()
E=Evidence("ev1","Official Company Report","company_filing","2026-09-25","Verified receivables exposure",True,True,"AUD")
X=CompanyExposure("consumer_credit_loss_sensitive",True,"Official Company Report","ev1","2026-09-25")
U=CompanyExposure("fuel_cost_sensitive",False,"Headline","u1","2026-09-25")

def test_verified_exposure_connects_event_to_thesis_and_valuation():
 r=engine.integrate(company={"ticker":"TEST"},
  event={"event_key":"consumer_delinquency","direction":"up","what_changed":"Delinquency rose","why_it_matters":"Potential credit-loss pressure"},
  exposures=[X],evidence=[E],
  thesis_state={"conditions":[{"key":"credit_losses_remain_controlled","status":"watch","evidence":"latest result"}]},
  valuation_state={"cash_ebitda":100,"free_cash_flow":50},fundamentals_state={"credit_losses":"verified"})
 d=r["decision_package"]
 assert r["status"]=="mapped" and d["directional_pressure"]=="negative"
 assert d["linked_thesis_conditions"][0]["key"]=="credit_losses_remain_controlled"
 assert d["valuation_link"]["status"]=="linked"
 assert d["ai_calculated_math"] is False

def test_unverified_exposure_is_rejected_not_used():
 r=engine.integrate(company={"ticker":"T"},event={"event_key":"crude_oil_price","direction":"up"},
  exposures=[U],evidence=[E])
 assert r["status"]=="insufficient_mapping"
 assert r["exposure_resolution"]["rejected_unverified_exposures"][0]["exposure_key"]=="fuel_cost_sensitive"

def test_missing_mapping_produces_problem_solving_next_step():
 r=engine.integrate(company={"ticker":"T"},event={"event_key":"policy_rate","direction":"up"},exposures=[],evidence=[E])
 d=r["decision_package"]
 assert "cannot establish" in d["why_it_matters"]
 assert d["what_would_change_the_thesis"]

def test_event_gateway_accepts_supported_sources_only():
 assert normalize_event({"source_type":"news","event_key":"policy_rate"})["status"]=="accepted"
 assert normalize_event({"source_type":"random_blog","event_key":"policy_rate"})["status"]=="rejected"
 assert normalize_event({"source_type":"macro"})["reason"]=="missing_event_key"

def test_api_route_present():
 s=Path("api_gateway.py").read_text()
 assert '@app.post("/api/v1/intelligence/evidence-to-thesis")' in s
 assert "normalize_event(body.event)" in s

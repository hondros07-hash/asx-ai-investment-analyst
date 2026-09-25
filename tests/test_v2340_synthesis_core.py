from services.synthesis_core import CausalSynthesisCore,Evidence
from services.exposure_registry import DEFAULT_EXPOSURE_RULES
from pathlib import Path

core=CausalSynthesisCore(DEFAULT_EXPOSURE_RULES)
E=Evidence("e1","Official Filing","company_filing","2026-09-25T00:00:00Z","Verified exposure evidence",True,True,"AUD")

def test_verified_credit_event_maps_to_kpi_thesis_and_monitoring():
 r=core.synthesize(company={"ticker":"TEST"},event={"event_key":"consumer_delinquency","direction":"up","what_changed":"Delinquency increased"},
                   company_exposure_keys=["consumer_credit_loss_sensitive"],evidence=[E])
 assert r["status"]=="mapped"
 assert r["directional_pressure"]=="negative"
 assert "credit_losses" in r["affected_kpis"]
 assert "credit_losses_remain_controlled" in r["thesis_conditions_affected"]
 assert "credit loss rate" in r["what_to_watch_next"]
 assert r["magnitude"]=="unknown"
 assert r["ai_calculated_math"] is False

def test_no_company_exposure_means_no_causal_claim():
 r=core.synthesize(company={"ticker":"TEST"},event={"event_key":"crude_oil_price","direction":"up"},
                   company_exposure_keys=[],evidence=[E])
 assert r["status"]=="insufficient_mapping"
 assert r["relevance"]["mapped"] is False

def test_unverified_evidence_cannot_create_confident_thesis_change():
 u=Evidence("e2","Unknown","headline","2026-09-25","claim",False,False)
 r=core.synthesize(company={"ticker":"T"},event={"event_key":"policy_rate","direction":"up"},
                   company_exposure_keys=["interest_rate_sensitive_funding"],evidence=[u])
 assert r["evidence_quality"]["level"]=="unverified"
 assert r["thesis_change"]=="unknown"

def test_unknown_direction_is_preserved_not_invented():
 r=core.synthesize(company={"ticker":"T"},event={"event_key":"jet_fuel_price","direction":"volatile"},
                   company_exposure_keys=["fuel_cost_sensitive"],evidence=[E])
 assert r["directional_pressure"]=="unknown"
 assert "verified_directional_relationship" in r["missing_evidence"]

def test_provenance_preserved():
 r=core.synthesize(company={"ticker":"T"},event={"event_key":"crude_oil_price","direction":"down"},
                   company_exposure_keys=["fuel_cost_sensitive"],evidence=[E])
 assert r["provenance"]["sources"]==["Official Filing"]
 assert r["provenance"]["currencies"]==["AUD"]
 assert r["provenance"]["ai_calculated_math"] is False

def test_api_route_present():
 s=Path("api_gateway.py").read_text()
 assert '@app.post("/api/v1/intelligence/synthesize")' in s
 assert "CausalSynthesisCore" in s

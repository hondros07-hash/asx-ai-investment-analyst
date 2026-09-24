import math
from services.analyst_engine import build_analyst_payload,deterministic_target_return
def test_provider_consensus_preserved_not_mode():
 p=build_analyst_payload({"recommendationKey":"buy","numberOfAnalystOpinions":12,"currency":"AUD"},
                         {"strongBuy":1,"buy":2,"hold":9,"sell":0,"strongSell":0},{"mean":11.53},9.0,"QAN.AX")
 assert p["consensus_label"]=="Buy"
def test_target_return_is_deterministic():
 assert abs(deterministic_target_return(11.53,9.0)-(11.53/9.0-1))<1e-12
def test_provider_count_not_bucket_sum():
 p=build_analyst_payload({"numberOfAnalystOpinions":17,"currency":"AUD"},{"buy":4,"hold":2},{"mean":10},8,"X")
 assert p["analyst_count"]==17 and p["evidence"]["recommendation_bucket_total"]==6
def test_no_ai_calculation():
 p=build_analyst_payload({}, {}, {}, 10,"X")
 assert p["evidence"]["ai_calculated"] is False
def test_verified_bridge_requires_ratio():
 p=build_analyst_payload({"recommendationKey":"buy","currency":"CAD","financialCurrency":"USD"},{},{"mean":100},50,"X",
                         {"status":"verified","verified":True},fx_rate=.75,security_ratio=None)
 assert p["target_price"] is None and p["evidence"]["bridge"]["target_bridge_status"]=="blocked_missing_security_ratio"
def test_verified_bridge_normalizes_ratio_and_fx():
 p=build_analyst_payload({"recommendationKey":"buy","currency":"CAD","financialCurrency":"USD"},{},{"mean":100},50,"X",
                         {"status":"verified","verified":True},fx_rate=1.3,security_ratio=.5)
 assert abs(p["target_price"]-65)<1e-12
def test_missing_target_stays_missing():
 p=build_analyst_payload({"recommendationKey":"hold","currency":"USD"},{},{},50,"X")
 assert p["target_price"] is None and p["percentage_return"] is None

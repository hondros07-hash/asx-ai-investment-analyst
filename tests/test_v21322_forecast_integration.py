from pathlib import Path
def src():return Path("app.py").read_text(encoding="utf-8")
def test_service_imported():assert "from services.forecast_engine import build_12m_forecast" in src()
def test_overview_uses_service():assert "_fc12=build_12m_forecast(_ccforecast_hist,current_price=price,security=ticker)" in src()
def test_forecast_page_evidence(): 
 s=src()
 for x in ["Forecast evidence ⓘ","Probability calibration observations","AI calculated: No","Model version:"]: assert x in s
def test_card_uses_same_payload():
 s=src(); assert '_fc_target=_mia_num(_fc12.get("target_price"))' in s and '_fc_prob=_mia_num(_fc12.get("probability_positive"))' in s

from services.valuation_engine import *
def test_bridge():
 r=dcf_value(100,10,50,20,DCFScenario(.05,.10,.02));assert r["status"]=="success" and abs(r["equity_value"]-r["enterprise_value"]-30)<1e-9
def test_scenarios():
 r=calculate_dcf_scenarios(100,10,20,10,100,sector="Technology",financial_currency="USD",listing_currency="USD");assert r["status"]=="success" and set(r["scenarios"])=={"Bear","Base","Bull"} and r["ai_calculated"] is False
def test_fx():
 a=calculate_dcf_scenarios(100,10,current_price=100,financial_currency="USD",listing_currency="USD");b=calculate_dcf_scenarios(100,10,current_price=200,financial_currency="USD",listing_currency="AUD",fx_rate_financial_to_listing=2);assert abs(b["base_case"]-2*a["base_case"])<1e-9
def test_missing_fx():assert calculate_dcf_scenarios(100,10,current_price=10,financial_currency="USD",listing_currency="AUD")["status"]=="unavailable"
def test_negative_fcf():assert calculate_dcf_scenarios(-100,10,current_price=10)["status"]=="unavailable"
def test_financials():assert calculate_dcf_scenarios(100,10,current_price=10,sector="Financial Services",industry="Banks")["status"]=="unsupported"

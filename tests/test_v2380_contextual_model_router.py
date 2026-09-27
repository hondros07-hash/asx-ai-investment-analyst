from services.contextual_model_router import classify_company, select_models, research_manifest
from services.research_data_foundation import normalize_fundamentals

def test_bank_avoids_industrial_dcf():
    result=select_models({"sector":"Financial Services","industry":"Banks - Diversified"},{})
    assert result["classification"]=="bank"
    assert "fcff_dcf" not in [m["key"] for m in result["selected_models"]]
    assert result["blended_fair_value"] is None

def test_bnpl_routes_credit_analysis():
    result=select_models({"industry":"Credit Services","business_description":"Buy now pay later"},{})
    assert result["classification"]=="bnpl"
    assert result["selected_models"][0]["key"]=="credit_unit_economics"

def test_missing_inputs_never_generate_valuation():
    result=research_manifest("ZIP.AX",{"industry":"Credit Services"},{})
    assert result["executed_models"]==[]
    assert result["valuation_status"]=="not_calculated"
    assert all(m["status"]=="insufficient_data" for m in result["selected_models"])

def test_provider_data_preserves_provenance_and_missing():
    result=normalize_fundamentals({"freeCashflow":123,"sharesOutstanding":100,"totalDebt":None},"Yahoo", "2026-06-30")
    assert result["inputs"]["free_cash_flow"]==123
    assert "debt" not in result["inputs"]
    assert result["provenance"]["free_cash_flow"]["as_of"]=="2026-06-30"
    assert result["provenance"]["free_cash_flow"]["verified"] is False

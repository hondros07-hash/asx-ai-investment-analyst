from pathlib import Path

def test_scorecard_does_not_call_missing_company_name_helper():
    s=Path("app.py").read_text(encoding="utf-8")
    assert "get_thesis_template(ticker,company_name(ticker),_ccsector,_ccindustry)" not in s
    assert "_thesis_company_name=str(" in s
    assert "get_thesis_template(ticker,_thesis_company_name,_ccsector,_ccindustry)" in s

def test_adaptive_template_engine_still_wired():
    s=Path("app.py").read_text(encoding="utf-8")
    assert "from services.thesis_template_engine import get_thesis_template, classify_thesis_template" in s
    assert "overview_dynamic_thesis(" in s

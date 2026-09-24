from pathlib import Path

def test_macro_chart_has_internal_technical_navigation():
    app = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")
    anchor = 'key=f"v21252_technical_{ticker}"'
    i = app.index(anchor)
    block = app[max(0, i-700):i+500]
    assert "View Technical Analysis" in block
    assert "on_click=_chr_set_cc_sub_v2111" in block
    assert 'args=("Technical",)' in block
    assert 'href=' not in block

def test_technical_route_exists():
    app = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")
    assert 'elif page=="Technical":' in app
    assert 'Technical Analysis Lab — {ticker}' in app

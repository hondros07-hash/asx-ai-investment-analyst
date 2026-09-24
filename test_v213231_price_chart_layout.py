from pathlib import Path
def src(): return Path("app.py").read_text(encoding="utf-8")
def test_price_card_has_independent_compact_height():
 s=src(); assert "_price_chart_widget_height=410" in s
 assert 'height=_price_chart_widget_height,key="v21243_price_card"' in s
def test_plotly_height_compacted_without_engine_rewrite():
 s=src(); assert "height=202,margin=dict(l=2,r=34,t=8,b=10)" in s
 assert "go.Candlestick" in s and "SMA20" in s and "SMA50" in s
def test_compact_macro_provenance():
 s=src(); assert "v213231-macro-note" in s and "v213232-macro-slot" in s
def test_technical_link_is_not_full_width():
 s=src(); assert '"View Technical Analysis →"' in s and "use_container_width=False" in s
def test_internal_navigation_preserved():
 s=src(); assert 'on_click=_chr_set_cc_sub_v2111' in s and 'args=("Technical",)' in s
def test_timeframes_preserved():
 s=src()
 for x in ['"1D"','"1W"','"1M"','"3M"','"6M"','"1Y"','"3Y"','"5Y"']: assert x in s

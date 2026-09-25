from pathlib import Path
import ast
s=Path("app.py").read_text()

def test_app_parses(): ast.parse(s)
def test_status_slot_always_rendered():
 assert "v23443-market-status-slot" in s
 assert "_feed_html='<div class=\"v2301-feed v2301-feed-empty\"" in s
 assert "st.markdown(f'<div class=\"v23443-market-status-slot\">{_feed_html}</div>'" in s
def test_1d_status_still_real():
 assert 'if _active_tf=="1D":' in s
 assert "exchange_session_state(ticker,_ccmeta)" in s
def test_plot_height_fixed_and_smaller():
 assert "height=184,margin=dict(l=2,r=34,t=6,b=8)" in s
 assert '[data-testid="stPlotlyChart"]{height:184px!important' in s
def test_footer_fixed_inside_geometry():
 assert 'min-height:22px!important;height:22px!important;max-height:22px!important' in s
 assert '.v213233-price-bottom-space{height:4px!important' in s
def test_failed_442_patch_removed():
 assert "V23.4.4.2 — Price Chart Footer Visibility Fix" not in s
def test_card_height_and_navigation_preserved():
 assert "_overview_widget_height=430" in s
 assert '"View Technical Analysis →"' in s
 assert 'args=("Technical",)' in s
def test_all_timeframes_preserved():
 assert '_tf_options=["1D","1W","1M","3M","6M","1Y","3Y","5Y"]' in s

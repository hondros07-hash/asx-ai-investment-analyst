from pathlib import Path
import ast
s=Path("app.py").read_text()
def test_app_parses(): ast.parse(s)
def test_footer_visibility_patch_present():
 assert "V23.4.4.2 — Price Chart Footer Visibility Fix" in s
 assert 'min-height:28px!important;height:28px!important' in s
 assert 'padding-bottom:8px!important' in s
def test_link_remains_internal_navigation():
 assert '"View Technical Analysis →"' in s
 assert 'on_click=_chr_set_cc_sub_v2111' in s
 assert 'args=("Technical",)' in s
def test_chart_height_unchanged():
 assert '_overview_widget_height=430' in s
 assert '_price_chart_widget_height=_overview_widget_height' in s
def test_chart_plot_logic_unchanged():
 assert 'st.plotly_chart(_fig,use_container_width=True' in s
def test_safe_bottom_space():
 assert '.v213233-price-bottom-space{height:10px;min-height:10px' in s

from pathlib import Path
import ast
s=Path("app.py").read_text()
def test_app_parses(): ast.parse(s)
def test_footer_navigation_still_present():
 assert '"View Technical Analysis →"' in s
 assert 'on_click=_chr_set_cc_sub_v2111' in s
 assert 'args=("Technical",)' in s
def test_card_height_preserved():
 assert '_overview_widget_height=430' in s
 assert '_price_chart_widget_height=_overview_widget_height' in s
def test_chart_plot_logic_preserved():
 assert 'st.plotly_chart(_fig,use_container_width=True' in s
def test_footer_has_reserved_bottom_space():
 assert '.v213233-price-bottom-space' in s

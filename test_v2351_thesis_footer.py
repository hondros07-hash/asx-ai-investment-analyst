from pathlib import Path
import ast
s=Path('app.py').read_text()
def test_parses(): ast.parse(s)
def test_footer_anchor():
 assert 'V23.5.1 — bottom-align the Thesis Scorecard navigation' in s
 assert 'margin-top:auto!important;flex-shrink:0!important' in s
 assert 'padding-bottom:8px!important;box-sizing:border-box!important' in s
def test_navigation_preserved():
 assert 'st.button("View Thesis Monitor  →",key=f"v21255_thesis_link_{ticker}"' in s
 assert 'args=("Thesis Scorecard",)' in s
def test_card_height_preserved():
 assert 'with st.container(border=True,height=_overview_widget_height,key="v21255_thesis_card"):' in s

from pathlib import Path
import ast
s=Path("app.py").read_text()
def test_parse(): ast.parse(s)
def test_bottom_anchor():
 assert "V23.5.1 — anchor the native Thesis Monitor navigation" in s
 assert "margin-top:auto!important;flex-shrink:0!important;padding-top:8px!important" in s
def test_navigation():
 assert 'st.button("View Thesis Monitor  →",key=f"v21255_thesis_link_{ticker}"' in s
 assert 'on_click=_chr_set_cc_sub_v2111,args=("Thesis Scorecard",)' in s
def test_height_and_rows_unchanged():
 assert "_overview_widget_height=430" in s
 assert 'with st.container(border=True,height=_overview_widget_height,key="v21255_thesis_card")' in s
 assert "_thesis_rows.iterrows()" in s

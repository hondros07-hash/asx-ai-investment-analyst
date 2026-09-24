from pathlib import Path
A=(Path(__file__).parent/"app.py").read_text(encoding="utf-8")
def test_timeframes(): assert "_active_tf=st.segmented_control" in A and "visible=(_opt==_active_tf)" in A and "updatemenus=[dict(type=\"buttons\"" not in A
def test_rebuild(): assert "v213171_chart_{ticker}_{_active_tf}" in A and "_tf_options.index(_active_tf)" in A
def test_link(): 
 i=A.index("v21243_price_card"); j=A.index("\"View Technical Analysis  →\"",i); k=A.index("with _w_thesis:",i); assert i<j<k and "on_click=_chr_set_cc_sub_v2111" in A[j:j+500]
def test_height(): assert "_overview_widget_height=430" in A

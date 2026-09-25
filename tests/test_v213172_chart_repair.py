from pathlib import Path
A=(Path(__file__).parent/'app.py').read_text()
def test_active_window():
 assert '_active_stock=_chart_sets.get(_active_tf)' in A and '_active_macro=_macro_sets.get(_active_tf)' in A
def test_rebase_common_window():
 assert '_common_start=_active_aligned.index.min()' in A and '_stock_rebased=_stock_common/float(_stock_common.iloc[0])*100.0' in A
def test_axis_mode():
 assert 'yaxis=("y" if _macro_normalized else "y3")' in A and 'visible=bool(_macro_on and not _macro_normalized and _macro_available)' in A
def test_unavailable_explicit():
 assert 'Macro overlay unavailable:' in A
def test_visual_restore():
 assert 'height=244,margin=dict(l=2,r=42,t=20,b=18)' in A
def test_footer():
 assert '_overview_widget_height=520' in A and 'key=f"v213172_technical_{ticker}"' in A

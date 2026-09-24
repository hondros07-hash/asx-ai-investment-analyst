from pathlib import Path
def src(): return Path("app.py").read_text(encoding="utf-8")
def test_active_timeframe_reference_style():
 s=src()
 assert 'st-key-v213171_timeframe_' in s
 assert 'button[aria-pressed="true"]' in s
 assert 'background:#086ee8!important' in s and 'color:#fff!important' in s
def test_timeframe_data_engine_preserved():
 s=src()
 assert 'st.segmented_control("Chart timeframe",_tf_options,key=_tf_key' in s
 for x in ("1D","1W","1M","3M","6M","1Y","3Y","5Y"): assert f'"{x}"' in s
def test_fixed_macro_slot_prevents_footer_displacement():
 s=src()
 assert '.v213232-macro-slot{height:16px;min-height:16px;max-height:16px' in s
 assert 'with st.expander("Macro overlay details"' not in s
 assert "_macro_note_html='&nbsp;'" in s
def test_technical_navigation_preserved():
 s=src()
 assert '"View Technical Analysis →"' in s
 assert 'on_click=_chr_set_cc_sub_v2111' in s and 'args=("Technical",)' in s
def test_chart_has_footer_headroom():
 assert 'height=202,margin=dict(l=2,r=34,t=8,b=10)' in src()

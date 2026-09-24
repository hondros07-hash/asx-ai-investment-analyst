from pathlib import Path
S=Path('app.py').read_text()
def test_card_has_bottom_breathing_room():
    assert '_price_chart_widget_height=432' in S
    assert 'v213233-price-bottom-space' in S and 'height:18px' in S
def test_active_segment_has_release_resilient_blue_state():
    assert '_tf_active_index=_tf_options.index(_active_tf)+1' in S
    assert 'background:#086ee8!important' in S
    assert '[aria-checked="true"]' in S and '[data-state="on"]' in S
def test_footer_navigation_preserved():
    assert '"View Technical Analysis →"' in S and 'args=("Technical",)' in S
def test_chart_engine_preserved():
    assert 'go.Candlestick' in S and 'SMA20' in S and 'SMA50' in S
    for x in ('1D','1W','1M','3M','6M','1Y','3Y','5Y'): assert f'"{x}"' in S

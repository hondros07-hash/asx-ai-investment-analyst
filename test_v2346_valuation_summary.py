from pathlib import Path
import ast
from services.valuation_summary_engine import summarize_valuation

def test_proportional():
    d={'status':'success','listing_currency':'AUD','scenarios':{'Bear':{'value_per_share':1},'Base':{'value_per_share':2},'Bull':{'value_per_share':5}}}
    r=summarize_valuation(d,2,'XYZ.AX')
    assert r['marker_positions_pct']=={'bear':0,'base':25,'bull':100}
    assert r['base_delta_pct']==0 and r['bull_delta_pct']==150
    assert r['ai_calculated_math'] is False

def test_missing_never_invented():
    r=summarize_valuation({'status':'unavailable'},None,'XYZ')
    assert r['status']=='insufficient_evidence' and r['bear_price'] is None
    assert r['marker_positions_pct']['base'] is None

def test_unsupported():
    assert summarize_valuation({'status':'unsupported'},3)['status']=='unsupported'

def test_routes_and_ui():
    assert '/api/v1/widget/valuation-summary' in Path('main.py').read_text()
    s=Path('app.py').read_text();ast.parse(s)
    assert '_chr_summarize_valuation(_ccauto_val,price,ticker)' in s
    assert 'View Full Valuation' in s

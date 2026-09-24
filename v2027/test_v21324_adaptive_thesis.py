from pathlib import Path
from services.thesis_template_engine import get_thesis_template, classify_thesis_template

def test_bank_template():
    p=get_thesis_template('CBA.AX','Commonwealth Bank','Financial Services','Banks - Diversified')
    assert p['template']=='bank'
    assert [x['label'] for x in p['criteria']][:2]==['Net interest margin','CET1 / capital strength']
    assert len(p['criteria'])==6 and p['ai_calculated'] is False

def test_airline_template():
    p=get_thesis_template('QAN.AX','Qantas Airways','Industrials','Airlines')
    assert p['template']=='airline'
    labels=[x['label'] for x in p['criteria']]
    assert 'Capacity / demand trend' in labels and 'Fuel cost discipline' in labels

def test_nike_consumer_template():
    p=get_thesis_template('NKE','NIKE, Inc.','Consumer Cyclical','Footwear & Accessories')
    assert p['template']=='consumer_brand'
    labels=[x['label'] for x in p['criteria']]
    assert 'Inventory health' in labels and 'Net interest margin' not in labels

def test_apple_technology_template():
    assert classify_thesis_template('AAPL','Apple Inc.','Technology','Consumer Electronics')=='technology'

def test_zip_payments_template():
    assert classify_thesis_template('ZIP.AX','Zip Co Limited','Financial Services','Credit Services / BNPL')=='payments'

def test_generic_corporate_fallback():
    assert get_thesis_template('XYZ','Example Co','Industrials','Conglomerates')['template']=='corporate'

def test_app_wires_template_and_content_sized_card():
    s=Path('app.py').read_text(encoding='utf-8')
    assert 'get_thesis_template(ticker,name,sector,industry)' in s
    assert 'height=_overview_widget_height,key="v21255_thesis_card"' not in s
    assert 'with st.container(border=True,key="v21255_thesis_card")' in s
    assert 'v21324-thesis-template' in s

def test_progress_remains_deterministic():
    s=Path('app.py').read_text(encoding='utf-8')
    assert '_ratio=(_display_met/max(_display_total,1))' in s
    assert '_pct=int(round(_ratio*100))' in s

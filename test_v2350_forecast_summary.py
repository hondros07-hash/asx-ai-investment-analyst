from pathlib import Path
import ast
from services.forecast_widget_engine import summarize_forecast

def test_no_fabricated_path():
    x=summarize_forecast({'status':'ready','target_price':120,'forecast_return':.2,'audit':{'model_version':'test','diagnostics':{'n':12}}},100,'TEST')
    assert x['status']=='ready' and abs(x['return_pct']-20)<1e-8 and x['sparkline_points']==[]
    assert x['validation']['walk_forward_observations']==12 and x['ai_calculated_math'] is False

def test_unavailable_not_fabricated():
    x=summarize_forecast({'status':'unavailable','target_price':None,'audit':{'reason':'Insufficient history'}},100,'TEST')
    assert x['target_price'] is None and x['return_label'] is None and x['reason']=='Insufficient history'

def test_changed_spot_recalculates_delta():
    x=summarize_forecast({'status':'ready','target_price':120,'forecast_return':.2},110,'TEST')
    assert abs(x['return_pct']-100*(120/110-1))<1e-8

def test_route_and_ui():
    main=Path('main.py').read_text();app=Path('app.py').read_text()
    assert '/api/v1/widget/forecast-summary' in main
    assert 'summarize_forecast(_fc12,price,ticker)' in app
    assert '_sparkpts="10,36' not in app
    ast.parse(app)

from services.forecast_widget_engine import summarize_forecast
from pathlib import Path

def sample():
 return {'status':'ready','target_price':120,'forecast_return':.2,'probability_positive':None,'audit':{'model_version':'test','diagnostics':{'n':0},'bridge':{'status':'not_used'}}}

def test_reuses_target_and_return():
 x=summarize_forecast(sample(),'ABC',100,'AUD');assert x['status']=='ready' and x['target_price']==120 and x['return_label']=='+20.0%'
 assert x['sparkline_points'] is None and x['ai_calculated_math'] is False

def test_no_fabricated_path():
 x=summarize_forecast(sample(),'ABC',100);assert x['sparkline_kind']=='unavailable'
 assert 'monthly_forward_path_not_produced_by_model' in x['missing_evidence']

def test_inconsistent_price_withheld():
 x=summarize_forecast(sample(),'ABC',90);assert x['status']=='unavailable' and x['target_price'] is None

def test_valid_explicit_model_path():
 x=summarize_forecast(sample(),'ABC',100,forward_path=[101+i for i in range(11)]+[120]);assert len(x['sparkline_points'])==12

def test_no_history_unavailable():
 x=summarize_forecast({'status':'unavailable','audit':{'reason':'history missing'}},'ABC',100)
 assert x['status']=='unavailable' and 'history missing' in x['missing_evidence']

def test_endpoint_and_ui():
 assert '/api/v1/widget/forecast-summary' in Path('main.py').read_text()
 s=Path('app.py').read_text();assert 'Observed history · not forecast path' in s
 assert '10,36 35,31 60,32' not in s

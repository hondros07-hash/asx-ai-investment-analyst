import ast
from pathlib import Path
import pandas as pd
from services.forecast_widget_engine import summarize_forecast

def test_reuses_canonical_result():
    model={'status':'ready','target_price':120,'forecast_return':.2,'probability_positive':None,'audit':{'model_version':'x','diagnostics':{'n':4}}}
    h=pd.DataFrame({'Close':[100+i for i in range(400)]},index=pd.date_range('2024-01-01',periods=400))
    x=summarize_forecast(model,h,100,'TEST')
    assert x['target_price']==120 and abs(x['return_pct']-20)<1e-8
    assert x['forward_path'] is None and len(x['sparkline'])<=12
    assert x['sparkline_type']=='observed_trailing_12_monthly_closes'
    assert x['ai_calculated_math'] is False

def test_missing_and_inconsistent_targets():
    assert summarize_forecast({},None,100)['status']=='unavailable'
    assert summarize_forecast({'status':'ready','target_price':120,'forecast_return':.1},None,100)['status']=='unavailable'

def test_integration():
    a=Path('app.py').read_text();ast.parse(a)
    assert 'summarize_forecast as _chr_forecast_summary' in a
    assert 'Historical trend unavailable' in a
    assert '10,36 35,31 60,32' not in a
    assert '/api/v1/widget/forecast-summary' in Path('main.py').read_text()

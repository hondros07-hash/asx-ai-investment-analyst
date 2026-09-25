import pandas as pd
from services.forecast_widget_engine import build_forecast_summary,summarize_forecast

def test_same_target_and_return():
 h=pd.Series([10.,11.,12.],index=pd.date_range('2026-01-01',periods=3,freq='ME'))
 m={'status':'ready','target_price':15.,'forecast_return':.25,'audit':{'model_version':'test','diagnostics':{'n':0}}}
 x=summarize_forecast(m,h,12.,'TEST')
 assert x['target_price']==15. and x['forecast_return']==.25 and x['delta_pct']==25.
 assert x['forward_monthly_path'] is None and x['sparkline_type']=='observed_historical_month_end'
 assert len(x['sparkline'])==3 and x['ai_calculated_math'] is False

def test_missing_model_no_fabrication():
 x=summarize_forecast({'status':'unavailable','audit':{'reason':'insufficient history'}},pd.Series(dtype=float),None,'X')
 assert x['target_price'] is None and x['sparkline']==[] and x['reason']=='insufficient history'

def test_no_fake_forward_sparkline():
 from pathlib import Path
 s=Path('app.py').read_text()
 assert '_sparkpts="10,36' not in s
 assert 'Historical prices · not a forecast path' in s
 assert '/api/v1/widget/forecast-summary' in Path('main.py').read_text()

import ast
from pathlib import Path
import pandas as pd
from services.forecast_widget_engine import summarize_forecast

def history():
    return pd.DataFrame({'Close':[10+i/100 for i in range(60)]},index=pd.bdate_range('2026-01-01',periods=60))
def test_model_target_and_return_same_payload():
    m={'status':'ready','target_price':12,'forecast_return':.2,'audit':{'model_version':'test','diagnostics':{'n':12}}}
    x=summarize_forecast(m,history(),'ZIP.AX',10,'AUD')
    assert x['target_price']==12 and abs(x['return_pct']-20)<1e-9 and x['ai_calculated_math'] is False
    assert x['forward_path'] is None and x['sparkline_kind']=='observed_historical_monthly_closes'
    assert len(x['sparkline_points'])<=12

def test_unavailable_never_invents_target_or_path():
    x=summarize_forecast({'status':'unavailable','audit':{'reason':'Insufficient completed 12M outcomes'}},history(),'ZIP.AX',10)
    assert x['status']=='unavailable' and x['target_price'] is None and x['return_pct'] is None
    assert x['reason']=='Insufficient completed 12M outcomes' and x['forward_path'] is None

def test_invalid_spot_never_returns_ready():
    x=summarize_forecast({'status':'ready','target_price':12},history(),'ZIP.AX',0)
    assert x['status']=='unavailable' and x['return_pct'] is None

def test_route_and_live_card():
    assert '/api/v1/widget/forecast-summary' in Path('main.py').read_text()
    s=Path('app.py').read_text()
    assert 'summarize_forecast(_fc12,_ccforecast_hist,ticker,price)' in s
    assert 'Observed historical monthly closes (not a projected price path)' in s
    assert '10,36 35,31 60,32' not in s
    ast.parse(s)

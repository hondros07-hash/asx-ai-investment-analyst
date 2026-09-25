from services.forecast_widget_engine import summarize_forecast

def test_no_fabricated_path():
    x=summarize_forecast({'status':'unavailable','audit':{'reason':'Insufficient history'}},10,'ZIP.AX')
    assert x['monthly_path']==[] and x['target_price'] is None

def test_same_canonical_target_and_return():
    x=summarize_forecast({'status':'ready','target_price':12,'forecast_return':.2,'audit':{'model_version':'test'}},10,'ZIP.AX','AUD')
    assert x['target_price']==12 and round(x['return_pct'],6)==20 and len(x['monthly_path'])==12
    assert x['monthly_path'][-1]==12 and not x['path_is_independent_forecast']

def test_no_invented_invalid_values():
    assert summarize_forecast({'status':'ready','target_price':float('nan')},10,'X')['status']=='unavailable'

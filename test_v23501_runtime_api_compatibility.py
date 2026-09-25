from unittest.mock import patch
import pandas as pd
from services.forecast_widget_engine import summarize_forecast
import pytest
api_gateway=pytest.importorskip("api_gateway")

def test_api_uses_single_canonical_model_and_history():
    h=pd.DataFrame({'Close':[100.0,101.0]})
    with patch.object(api_gateway.yf,'Ticker') as factory, patch.object(api_gateway,'build_12m_forecast') as model:
        factory.return_value.history.return_value=h
        factory.return_value.info={'currency':'AUD'}
        model.return_value={'status':'ready','target_price':121.2,'forecast_return':.2,'audit':{}}
        result=api_gateway.forecast_summary_for_ticker('ABC.AX')
        assert result['status']=='ready' and result['target_price']==121.2
        assert result['reference_price']==101.0 and result['currency']=='AUD'
        factory.return_value.history.assert_called_once()
        model.assert_called_once()

def test_invalid_provider_audit_is_safe():
    r=summarize_forecast({'status':'unavailable','audit':'bad'},'ABC',100)
    assert r['status']=='unavailable'

def test_missing_reference_is_explicit():
    r=summarize_forecast({'status':'ready','target_price':120,'forecast_return':.2},'ABC',None)
    assert r['status']=='unavailable' and 'reference_price_unavailable' in r['missing_evidence']

def test_api_route_contract():
    from main import app
    assert any(getattr(route,'path',None)=='/api/v1/widget/forecast-summary' and 'GET' in route.methods for route in app.routes)

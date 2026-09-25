"""V23.5.0 — display adapter for the existing 12-month forecast model.

The underlying model only predicts a terminal 12-month return. It does NOT predict
12 monthly intermediate prices. The sparkline is therefore labelled historical,
never represented as a forecast trajectory.
"""
from __future__ import annotations
from datetime import datetime,timezone
import math
import pandas as pd
from services.forecast_engine import build_12m_forecast,price_series,MODEL_VERSION

def _number(x):
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except (ValueError,TypeError,OverflowError):return None

def historical_sparkline(history):
    """Up to 12 observed month-end adjusted closes; no synthetic future points."""
    px=price_series(history)
    if px.empty or not isinstance(px.index,pd.DatetimeIndex):return []
    monthly=px.sort_index().resample('ME').last().dropna().tail(12)
    return [{'date':idx.date().isoformat(),'price':float(value)} for idx,value in monthly.items() if _number(value) is not None]

def summarize_forecast(model,history,reference_price=None,ticker='',currency=None):
    model=model if isinstance(model,dict) else {}
    audit=model.get('audit') or {}
    target=_number(model.get('target_price'))
    spot=_number(reference_price)
    if spot is None:
        px=price_series(history)
        spot=_number(px.iloc[-1]) if len(px) else None
    ready=model.get('status')=='ready' and target is not None and target>0 and spot is not None and spot>0
    diag=audit.get('diagnostics') or {}
    path=historical_sparkline(history)
    return {'status':'ready' if ready else 'unavailable','ticker':ticker,'currency':currency,
      'reference_price':spot,'target_price':target if ready else None,
      'forecast_return':target/spot-1 if ready else None,
      'delta_pct':(target/spot-1)*100 if ready else None,
      'probability_positive':_number(model.get('probability_positive')) if ready else None,
      'sparkline':path,'sparkline_type':'observed_historical_month_end','forward_monthly_path':None,
      'forward_path_status':'not_produced_by_underlying_model',
      'validation':{'label':model.get('validation_label') or audit.get('validation_label'),
        'walk_forward_observations':int(audit.get('walk_forward_observations') or 0),
        'mae':_number(diag.get('mae')),'rmse':_number(diag.get('rmse')),
        'direction_accuracy':_number(diag.get('direction_accuracy'))},
      'model_version':audit.get('model_version',MODEL_VERSION),'method':audit.get('method'),
      'reason':None if ready else audit.get('reason','Forecast inputs or validation unavailable'),
      'missing_inputs':[] if ready else [audit.get('reason','verified forecast output')],
      'provenance':{'source':'Existing deterministic forecast engine; observed adjusted price history',
        'history_observations':audit.get('history_observations'),
        'forecast_origin':audit.get('forecast_origin'),'generated_at':datetime.now(timezone.utc).isoformat(),
        'ai_calculated_math':False},'ai_calculated_math':False}

def build_forecast_summary(history,reference_price=None,ticker='',currency=None,model=None):
    result=model if model is not None else build_12m_forecast(history,current_price=reference_price,security=ticker)
    return summarize_forecast(result,history,reference_price,ticker,currency)

"""V23.5.0: display-only accountability adapter for the canonical 12-month model.
No new target or synthetic forward price path is calculated here.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math
import pandas as pd
from services.forecast_engine import build_12m_forecast, price_series

def finite(value):
    try:
        n=float(value)
        return n if math.isfinite(n) else None
    except (TypeError,ValueError,OverflowError):
        return None

def summarize_forecast(model, history=None, reference_price=None, ticker='', currency=None):
    model=model if isinstance(model,dict) else {}
    audit=model.get('audit') if isinstance(model.get('audit'),dict) else {}
    spot=finite(reference_price)
    target=finite(model.get('target_price'))
    result_return=finite(model.get('forecast_return'))
    valid=model.get('status')=='ready' and spot is not None and spot>0 and target is not None and target>0 and result_return is not None
    if valid and not math.isclose(target/spot-1,result_return,rel_tol=1e-7,abs_tol=1e-7):
        valid=False
        reason='Target and reference price do not reconcile with canonical forecast return.'
    else:
        reason=audit.get('reason') or 'Canonical forecast inputs unavailable.'
    px=price_series(history)
    # Observed trailing monthly closes, NOT a simulated or model-generated future path.
    trailing=px.resample('ME').last().dropna().tail(12) if isinstance(px.index,pd.DatetimeIndex) else pd.Series(dtype=float)
    observed=[{'date':idx.date().isoformat(),'price':float(v)} for idx,v in trailing.items() if finite(v) is not None and v>0]
    diag=audit.get('diagnostics') if isinstance(audit.get('diagnostics'),dict) else {}
    return {'status':'ready' if valid else 'unavailable','ticker':ticker,'currency':currency,
      'reference_price':spot,'target_price':target if valid else None,
      'return_pct':100*(target/spot-1) if valid else None,
      'forecast_return':result_return if valid else None,
      'probability_positive':finite(model.get('probability_positive')) if valid else None,
      'sparkline':observed,'sparkline_type':'observed_trailing_12_monthly_closes' if observed else 'unavailable',
      'forward_path':None,'forward_path_status':'not_provided_by_canonical_model',
      'model_version':audit.get('model_version'),'validation_label':model.get('validation_label') or audit.get('validation_label'),
      'validation':{'completed_walk_forward_observations':diag.get('n',0),'mae':finite(diag.get('mae')),
        'rmse':finite(diag.get('rmse')),'direction_accuracy':finite(diag.get('direction_accuracy')),
        'probability_calibration_observations':audit.get('probability_calibration_observations',0)},
      'method':audit.get('method'),'history_observations':audit.get('history_observations'),
      'forecast_origin':audit.get('forecast_origin'),'reason':None if valid else reason,
      'missing_inputs':[] if valid else [str(reason)],'source':'canonical services.forecast_engine.build_12m_forecast',
      'generated_at':datetime.now(timezone.utc).isoformat(),'ai_calculated_math':False}

def forecast_summary_from_history(history,reference_price=None,ticker='',currency=None,model=None):
    canonical=model if model is not None else build_12m_forecast(history,current_price=reference_price,security=ticker)
    return summarize_forecast(canonical,history,reference_price,ticker,currency)

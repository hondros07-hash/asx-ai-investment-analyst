"""V23.5.0 — forecast presentation of the canonical deterministic model.

No second predictor is fitted here. The canonical model supplies a 12-month
endpoint, not twelve monthly predictions. Never imply interpolation is a model
forecast: the UI renders the verified endpoint without a fabricated path.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math
from typing import Any, Mapping
from services.forecast_engine import MODEL_VERSION

def finite(value: Any):
    try:
        number=float(value)
        return number if math.isfinite(number) else None
    except (ValueError,TypeError,OverflowError):
        return None

def summarize_forecast(model: Mapping[str,Any], reference_price: Any, ticker: str, *, currency: str|None=None, source: str='Yahoo Finance/yfinance adjusted daily history') -> dict:
    """Summarize one existing build_12m_forecast result without reforecasting."""
    audit=dict(model.get('audit') or {})
    spot=finite(reference_price); target=finite(model.get('target_price'))
    prediction=finite(model.get('forecast_return'))
    ready=(model.get('status')=='ready' and spot is not None and spot>0 and target is not None and target>0 and prediction is not None)
    # The canonical engine already calculates the target and return from the same spot.
    # A mismatched reference quote is not silently used to report the old return.
    delta=(target/spot-1) if ready else None
    diag=dict(audit.get('diagnostics') or {})
    missing=[]
    if spot is None or spot<=0: missing.append('verified_reference_price')
    if target is None: missing.append('canonical_model_target')
    if prediction is None: missing.append('canonical_model_return')
    if not ready and not missing: missing.append('canonical_model_ready_status')
    probability=finite(model.get('probability_positive')) if ready else None
    if probability is not None and not (0<=probability<=1): probability=None
    return {'status':'ready' if ready else 'unavailable','ticker':ticker.upper(),
        'target_price':target if ready else None,'reference_price':spot,'return_pct':delta*100 if ready else None,
        'return_label':f'{delta:+.1%}' if ready else None,'currency':currency,
        'sparkline_points':[], 'sparkline_status':'unavailable_model_does_not_supply_monthly_path',
        'sparkline_reason':'The 12-month model supplies an endpoint, not a monthly forecast path.',
        'probability_positive':probability,'validation':{
            'label':model.get('validation_label') or audit.get('validation_label') or 'Unavailable',
            'walk_forward_observations':int(diag.get('n') or 0),
            'mae':finite(diag.get('mae')),'rmse':finite(diag.get('rmse')),
            'direction_accuracy':finite(diag.get('direction_accuracy')),
            'calibration_observations':int(audit.get('probability_calibration_observations') or 0)},
        'model_version':audit.get('model_version') or MODEL_VERSION,
        'method':audit.get('method'), 'forecast_origin':audit.get('forecast_origin'),
        'history_observations':audit.get('history_observations'),
        'reason':None if ready else audit.get('reason') or 'Canonical forecast unavailable',
        'missing_inputs':missing,'provenance':{'source':source,'reference_price_basis':'selected listing quote',
            'bridge':audit.get('bridge'),'ai_calculated_math':False},
        'ai_calculated_math':False,'generated_at':datetime.now(timezone.utc).isoformat()}

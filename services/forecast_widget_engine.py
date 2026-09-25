"""V23.5.0: presentation adapter for the canonical deterministic 12-month model.

The 12 monthly points are a *constant compounded-return interpolation* between
spot and the model's annual target, NOT twelve separately predicted prices.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict
import math
from services.forecast_engine import MODEL_VERSION


def finite(value):
    try:
        v=float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError, OverflowError):
        return None


def summarize_forecast(full: Dict[str,Any], reference_price: Any, ticker: str, currency: str = 'UNKNOWN') -> Dict[str,Any]:
    """Summarize an existing build_12m_forecast result without refitting its model."""
    full=full if isinstance(full,dict) else {}
    audit=full.get('audit') or {}
    spot=finite(reference_price)
    target=finite(full.get('target_price'))
    reason=audit.get('reason') or 'Canonical forecast unavailable'
    result={'status':'unavailable','ticker':str(ticker).upper(),'currency':currency,
            'reference_price':spot,'target_price':None,'return_pct':None,
            'monthly_path':[],'path_type':'none','path_is_independent_forecast':False,
            'model_version':audit.get('model_version',MODEL_VERSION),
            'method':audit.get('method'),'validation':audit.get('diagnostics') or {},
            'validation_label':full.get('validation_label') or audit.get('validation_label'),
            'probability_positive':finite(full.get('probability_positive')),
            'probability_calibration_observations':audit.get('probability_calibration_observations',0),
            'history_observations':audit.get('history_observations'),
            'source':'existing deterministic forecast engine',
            'forecast_origin':audit.get('forecast_origin'),
            'generated_at':datetime.now(timezone.utc).isoformat(),
            'reason':reason,'ai_calculated_math':False}
    if full.get('status')!='ready' or spot is None or spot<=0 or target is None or target<=0:
        return result
    # Same target as the Full Forecasts page; no independent prediction.
    annual_return=target/spot-1
    path=[round(spot*(target/spot)**(month/12),8) for month in range(1,13)]
    result.update(status='ready',target_price=target,return_pct=annual_return*100,
                  monthly_path=path,path_type='constant_compounded_return_interpolation',
                  reason=None)
    return result

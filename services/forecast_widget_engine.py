"""V23.5.0: evidence-preserving summary of the existing 12-month model.

The underlying model publishes a 12-month endpoint, NOT monthly forecasts. Consequently
this adapter never manufactures a twelve-point forward trajectory. A chart is emitted
only when a separately validated, model-produced forward path is supplied.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math
from typing import Any, Mapping


def finite(value: Any):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError, OverflowError):
        return None


def summarize_forecast(full: Mapping[str, Any], ticker: str, reference_price: Any = None,
                       currency: str | None = None, forward_path: Any = None) -> dict:
    """Do not rerun or change the forecast; use the same payload as Full Forecasts."""
    audit=full.get('audit') or {}
    spot=finite(reference_price)
    target=finite(full.get('target_price'))
    reported_return=finite(full.get('forecast_return'))
    reasons=[]
    if full.get('status')!='ready': reasons.append(str(audit.get('reason') or 'forecast_model_unavailable'))
    if spot is None or spot<=0: reasons.append('reference_price_unavailable')
    if target is None or target<=0: reasons.append('model_target_unavailable')
    if audit.get('bridge',{}).get('status')=='verified' and (spot is None or target is None):
        reasons.append('verified_listing_conversion_incomplete')
    ready=not reasons
    ret=(target/spot-1) if ready else None
    if ready and reported_return is not None and not math.isclose(ret,reported_return,rel_tol=1e-7,abs_tol=1e-7):
        reasons.append('target_return_inconsistent');ready=False;ret=None
    path=None
    if ready and isinstance(forward_path,(list,tuple)) and len(forward_path)==12:
        values=[finite(v) for v in forward_path]
        if all(v is not None and v>0 for v in values) and math.isclose(values[-1],target,rel_tol=1e-7):
            path=values
        else: reasons.append('forward_path_invalid')
    elif ready: reasons.append('monthly_forward_path_not_produced_by_model')
    diag=audit.get('diagnostics') or {}
    return {
        'status':'ready' if ready else 'unavailable', 'target_ticker':ticker.upper(),
        'target_price':target if ready else None,'reference_price':spot if ready else None,
        'forecast_return':ret,'return_pct':ret*100 if ret is not None else None,
        'return_label':f'{ret:+.1%}' if ret is not None else '—',
        'currency':currency,'horizon_months':12,
        'sparkline_points':path,'sparkline_kind':'model_forward_path' if path else 'unavailable',
        'sparkline_reason':None if path else 'The existing model publishes a 12-month endpoint, not a monthly forward trajectory.',
        'probability_positive':finite(full.get('probability_positive')) if ready else None,
        'validation':{'label':full.get('validation_label') or audit.get('validation_label') or 'Validation limited',
                      'walk_forward_observations':int(diag.get('n') or 0),
                      'mae':finite(diag.get('mae')),'rmse':finite(diag.get('rmse')),
                      'direction_accuracy':finite(diag.get('direction_accuracy'))},
        'model_version':audit.get('model_version'),'method':audit.get('method'),
        'history_observations':audit.get('history_observations'),
        'forecast_origin':audit.get('forecast_origin'),
        'missing_evidence':list(dict.fromkeys(reasons)),
        'provenance':{'model':'services.forecast_engine.build_12m_forecast',
                      'market_data':'Yahoo Finance/yfinance (API adapter); dashboard uses existing history service',
                      'ai_calculated_math':False},
        'ai_calculated_math':False,'generated_at':datetime.now(timezone.utc).isoformat(),
    }


def observed_history_sparkline(history, count=12):
    """Exactly 12 observed historical close samples; NEVER a forward forecast path."""
    import pandas as pd
    if isinstance(history, pd.DataFrame):
        if 'Close' not in history: return None
        x=history['Close']
        if isinstance(x,pd.DataFrame): x=x.iloc[:,0]
    elif isinstance(history,pd.Series): x=history
    else: return None
    x=pd.to_numeric(x,errors='coerce').replace([float('inf'),-float('inf')],float('nan')).dropna()
    x=x[x>0]
    if len(x)<count:return None
    import numpy as np
    indices=np.linspace(0,len(x)-1,count).round().astype(int)
    return [float(x.iloc[i]) for i in indices]

def svg_points_from_observed(values):
    """Presentation-only mapping of actual historical samples into a 270x48 SVG."""
    if not values or len(values)!=12:return None
    lo=min(values); hi=max(values); span=hi-lo
    return ' '.join(f'{10+i*250/11:.2f},{24 if span==0 else 40-(v-lo)/span*32:.2f}' for i,v in enumerate(values))

"""V23.5.0: evidence-preserving summary of the existing 12-month model.

The underlying model publishes a 12-month endpoint, NOT monthly forecasts. Consequently
this adapter never manufactures a twelve-point forward trajectory. A chart is emitted
only when a separately validated, model-produced forward path is supplied.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math
from typing import Any, Mapping
import pandas as pd


def finite(value: Any):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError, OverflowError):
        return None


def _record(value: Any) -> dict:
    """Normalize records without evaluating pandas objects as booleans."""
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, pd.DataFrame):
        return value.iloc[0].to_dict() if not value.empty else {}
    return {}


def _scalar(value: Any, default=None):
    """Return a JSON-safe scalar; reject vector-valued fields."""
    if isinstance(value, (pd.Series, pd.DataFrame, list, tuple, dict)):
        return default
    try:
        if value is None or pd.isna(value):
            return default
    except (TypeError, ValueError):
        return default
    return value


def _reason(value: Any, fallback: str) -> str:
    value = _scalar(value)
    return str(value) if value is not None and str(value).strip() else fallback


def summarize_forecast(full: Mapping[str, Any], ticker: str, reference_price: Any = None,
                       currency: str | None = None, forward_path: Any = None) -> dict:
    """Do not rerun or change the forecast; use the same payload as Full Forecasts."""
    full=_record(full)
    audit=_record(full.get('audit'))
    spot=finite(reference_price)
    target=finite(full.get('target_price'))
    reported_return=finite(full.get('forecast_return'))
    reasons=[]
    if full.get('status')!='ready': reasons.append(_reason(audit.get('reason'), 'forecast_model_unavailable'))
    if spot is None or spot<=0: reasons.append('reference_price_unavailable')
    if target is None or target<=0: reasons.append('model_target_unavailable')
    if _record(audit.get('bridge')).get('status')=='verified' and (spot is None or target is None):
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
    diag=_record(audit.get('diagnostics'))
    return {
        'status':'ready' if ready else 'unavailable', 'target_ticker':str(ticker).upper(),
        'target_price':target if ready else None,'reference_price':spot if ready else None,
        'forecast_return':ret,'return_pct':ret*100 if ret is not None else None,
        'return_label':f'{ret:+.1%}' if ret is not None else '—',
        'currency':_scalar(currency),'horizon_months':12,
        'sparkline_points':path,'sparkline_kind':'model_forward_path' if path else 'unavailable',
        'sparkline_reason':None if path else 'The existing model publishes a 12-month endpoint, not a monthly forward trajectory.',
        'probability_positive':finite(full.get('probability_positive')) if ready else None,
        'validation':{'label':_scalar(full.get('validation_label')) or _scalar(audit.get('validation_label')) or 'Validation limited',
                      'walk_forward_observations':int(finite(diag.get('n')) or 0),
                      'mae':finite(diag.get('mae')),'rmse':finite(diag.get('rmse')),
                      'direction_accuracy':finite(diag.get('direction_accuracy'))},
        'model_version':_scalar(audit.get('model_version')),'method':_scalar(audit.get('method')),
        'history_observations':_scalar(audit.get('history_observations')),
        'forecast_origin':_scalar(audit.get('forecast_origin')),
        'missing_evidence':list(dict.fromkeys(reasons)),
        'provenance':{'model':'services.forecast_engine.build_12m_forecast',
                      'market_data':'Yahoo Finance/yfinance (API adapter); dashboard uses existing history service',
                      'ai_calculated_math':False},
        'ai_calculated_math':False,'generated_at':datetime.now(timezone.utc).isoformat(),
    }

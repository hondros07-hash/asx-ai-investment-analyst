"""V23.5.0: accountable presentation adapter for the existing deterministic forecast.

The twelve-point chart is *observed historical monthly closes*, not an invented
forward path. The existing model supplies the only 12-month target.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math
from typing import Any
import pandas as pd
from services.forecast_engine import build_12m_forecast, price_series


def _finite(value: Any):
    try:
        n=float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError, OverflowError):
        return None


def summarize_forecast(model: dict, history: Any, ticker: str, reference_price: Any = None, currency: str | None = None) -> dict:
    """Never synthesize a target or prospective path when the model has none."""
    model=model if isinstance(model,dict) else {}
    audit=model.get('audit') if isinstance(model.get('audit'),dict) else {}
    px=price_series(history)
    spot=_finite(reference_price)
    target=_finite(model.get('target_price')) if model.get('status')=='ready' else None
    result={
        'status':'ready' if target is not None and spot is not None and spot>0 else 'unavailable',
        'ticker':ticker.upper(), 'target_price':target, 'reference_price':spot,
        'currency':currency, 'return_pct':(target/spot-1)*100 if target is not None and spot is not None and spot>0 else None,
        'horizon_months':12, 'model_version':audit.get('model_version'),
        'method':audit.get('method'), 'validation':audit.get('diagnostics') or {},
        'validation_label':model.get('validation_label') or audit.get('validation_label'),
        'probability_positive':_finite(model.get('probability_positive')),
        'probability_calibration_observations':audit.get('probability_calibration_observations',0),
        'sparkline_kind':'observed_historical_monthly_closes', 'sparkline_points':[],
        'forward_path':None, 'forward_path_status':'not_generated_by_underlying_model',
        'source':'Yahoo Finance/yfinance historical adjusted close; existing Chrímata deterministic forecast engine',
        'history_observations':len(px), 'history_last_observed_at':str(px.index[-1]) if len(px) else None,
        'calculated_at':datetime.now(timezone.utc).isoformat(),
        'reason':None, 'ai_calculated_math':False,
    }
    if len(px):
        # Calendar month-end observations; no interpolation or artificial projection.
        monthly=px.groupby(px.index.to_period('M')).last().tail(12) if isinstance(px.index,pd.DatetimeIndex) else px.tail(12)
        result['sparkline_points']=[float(v) for v in monthly if _finite(v) is not None]
    if result['status']!='ready':
        result['reason']=audit.get('reason') or ('Verified reference price unavailable' if spot is None or spot<=0 else 'Model target unavailable')
    return result


def forecast_summary_from_history(history: Any, ticker: str, reference_price: Any = None, currency: str | None = None, **model_kwargs) -> dict:
    px=price_series(history)
    spot=_finite(reference_price) or (_finite(px.iloc[-1]) if len(px) else None)
    model=build_12m_forecast(history,current_price=spot,security=ticker,**model_kwargs)
    return summarize_forecast(model,history,ticker,spot,currency)

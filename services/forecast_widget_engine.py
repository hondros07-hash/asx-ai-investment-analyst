"""V23.5.0: presentation adapter for the canonical deterministic 12-month model.

The existing model produces an endpoint, not twelve independently forecast monthly
prices. The optional 12-point curve is explicitly an endpoint interpolation, never
presented as twelve independently estimated forecasts.
"""
from __future__ import annotations
from datetime import datetime, timezone
import math

def finite(value):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError, OverflowError):
        return None

def summarize_forecast(model, reference_price, ticker="", currency=None):
    model=model if isinstance(model,dict) else {}
    audit=model.get("audit") if isinstance(model.get("audit"),dict) else {}
    spot=finite(reference_price)
    target=finite(model.get("target_price"))
    diagnostics=audit.get("diagnostics") if isinstance(audit.get("diagnostics"),dict) else {}
    result={
        "status":"unavailable","ticker":ticker,"currency":currency,
        "reference_price":spot,"target_price":None,"return_pct":None,
        "sparkline_points":[],"sparkline_kind":"endpoint_interpolation_not_monthly_forecast",
        "probability_positive":None,"validation":diagnostics,
        "validation_label":model.get("validation_label") or audit.get("validation_label"),
        "model_version":audit.get("model_version"),"history_observations":audit.get("history_observations"),
        "forecast_origin":audit.get("forecast_origin"),"source":"canonical_forecast_engine",
        "method":audit.get("method"),"reason":audit.get("reason"),
        "ai_calculated_math":False,"generated_at":datetime.now(timezone.utc).isoformat(),
    }
    if model.get("status")!="ready" or spot is None or spot<=0 or target is None or target<=0:
        result["reason"]=result["reason"] or "Verified model target and positive reference price required"
        return result
    result.update(status="ready",target_price=target,return_pct=(target/spot-1)*100,
                  probability_positive=finite(model.get("probability_positive")),reason=None)
    # Mathematical display interpolation only; the model does not predict monthly milestones.
    ratio=target/spot
    result["sparkline_points"]=[float(spot*ratio**(i/12)) for i in range(1,13)]
    return result

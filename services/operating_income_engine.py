"""Operating Income intelligence: pure, provider-neutral and independently testable.

Consumes the existing cached Fundamentals snapshot; never fetches provider data.
No synthetic financial observations or unsupported fiscal-period comparisons.
"""
from datetime import date
from math import isfinite

SOURCE = "Yahoo Finance financial statements"


def _valid(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def _period(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _comparison(current, previous):
    if previous is None or not _valid(previous):
        return None, "comparison_unavailable"
    if previous < 0 and current > 0:
        return "Turnaround", "turnaround"
    if previous > 0 and current < 0:
        return "Turned negative", "turned_negative"
    if previous == 0:
        if current == 0:
            return "+0.0% YoY", "flat"
        return None, "zero_baseline"
    if current == 0 and previous < 0:
        return "Break-even", "break_even"
    growth = (current - previous) / abs(previous) * 100
    return f"{growth:+.1f}% YoY", ("improving" if growth > 0 else "declining" if growth < 0 else "flat")


def calculate(data, currency):
    """Return the same card contract as the shared independent KPI runner."""
    periods = data.get("periods") or []
    mode = "ttm" if data.get("frequency") == "TTM" else ("quarterly" if "Quarterly" in str(data.get("frequency")) else "annual")
    raw = ((data.get("statements") or {}).get("Income Statement") or {}).get("Operating Income (EBIT)") or {}
    history = sorted(((str(p), float(raw[p])) for p in periods if p in raw and _period(p) and _valid(raw[p])),
                     key=lambda row: _period(row[0]))
    current_period = str(periods[0]) if periods else ""
    current = next((v for p, v in history if p == current_period), None)
    result = {"metric": "Operating Income", "value": current, "history": history,
              "delta": None, "period": current_period, "percent": False,
              "status": "ok" if current is not None else "unavailable",
              "comparison_status": "comparison_unavailable", "currency": currency,
              "source": SOURCE, "period_mode": mode}
    if current is None:
        return result
    if mode == "ttm":
        # A single TTM snapshot is not a prior-year TTM comparison.
        result["comparison_status"] = "ttm_comparison_unavailable"
        return result
    current_date = _period(current_period)
    if current_date is None:
        return result
    if mode == "annual":
        # Fiscal year-end can shift by a few days, e.g. 52/53-week reporting.
        candidates = [(p, v) for p, v in history if 330 <= (current_date - _period(p)).days <= 400]
    else:
        # Quarterly YOY requires the corresponding quarter one year earlier.
        candidates = [(p, v) for p, v in history if 330 <= (current_date - _period(p)).days <= 400]
    if len(candidates) != 1:
        result["comparison_status"] = "comparison_unavailable"
        return result
    previous = candidates[0][1]
    result["previous"] = previous
    result["comparison_period"] = candidates[0][0]
    result["delta"], result["comparison_status"] = _comparison(current, previous)
    return result

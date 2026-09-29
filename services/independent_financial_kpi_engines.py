"""Independent, fault-isolated KPI calculations over one shared financial snapshot.

No provider calls here. Each metric has its own entry point; an exception in one
metric becomes a local unavailable result, never a Fundamentals page failure.
"""
from datetime import date
from math import isfinite
from services.financial_kpi_engine import Observation, build_kpi

SOURCE = "Yahoo Finance financial statements"
METRICS = ("Revenue", "Operating Income", "Net Income", "Free Cash Flow", "Operating Margin")


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def _series(data, metric):
    statements = data.get("statements") or {}
    inc = statements.get("Income Statement") or {}
    cash = statements.get("Cash Flow") or {}
    periods = data.get("periods") or []
    if metric == "Operating Margin":
        return [(p, (data.get("ratios") or {}).get(p, {}).get("Operating Margin")) for p in reversed(periods)]
    group = cash if metric == "Free Cash Flow" else inc
    key = "Operating Income (EBIT)" if metric == "Operating Income" else metric
    return [(p, (group.get(key) or {}).get(p)) for p in reversed(periods)]


def _calculate(data, metric, currency):
    periods = data.get("periods") or []
    mode = "ttm" if data.get("frequency") == "TTM" else ("quarterly" if "Quarterly" in str(data.get("frequency")) else "annual")
    history = _series(data, metric)
    current_period = str(periods[0]) if periods else ""
    current = history[-1][1] if history and str(history[-1][0]) == current_period else None
    delta = None
    prior_value = None
    prior_period = None
    comparison_status = "unavailable"
    if metric == "Operating Margin":
        if len(history) > 1 and _number(current) and _number(history[-2][1]) and mode != "ttm":
            delta = f"{(current-history[-2][1])*100:+.1f} pp vs previous period"
    elif mode != "ttm":
        observations = []
        for period, value in history:
            if _number(value) and currency and currency != "Unconfirmed":
                try:
                    observations.append(Observation(str(period), date.fromisoformat(str(period)),
                                                    float(value), str(currency), mode, SOURCE))
                except (ValueError, TypeError):
                    continue
        result = build_kpi(observations, mode)
        current = result.value if observations and observations[-1].period == current_period else None
        if current is not None and result.previous is not None:
            prior_value = result.previous
            lag = 1 if mode == "annual" else 4
            if len(result.history) > lag:
                prior_period = result.history[-1-lag].period
        if metric == "Operating Income" and current is not None and prior_value is not None:
            if prior_value < 0 and current >= 0:
                comparison_status = "turnaround"
                delta = "Turned profitable YoY"
            elif prior_value >= 0 and current < 0:
                comparison_status = "turned_negative"
                delta = "Turned loss-making YoY"
            elif prior_value < 0 and current < 0:
                comparison_status = "improving" if current > prior_value else "declining" if current < prior_value else "unchanged"
                delta = "Loss narrowed YoY" if current > prior_value else "Loss widened YoY" if current < prior_value else "Loss unchanged YoY"
            else:
                comparison_status = "improving" if current > prior_value else "declining" if current < prior_value else "unchanged"
        if current is not None and result.growth_pct is not None:
            delta = f"{result.growth_pct:+.1f}% {result.comparison}"
    return {"metric": metric, "value": current if _number(current) else None,
            "history": history, "delta": delta, "period": current_period,
            "percent": metric == "Operating Margin", "status": "ok" if _number(current) else "unavailable",
            "previous_value": prior_value, "previous_period": prior_period,
            "comparison_status": comparison_status, "source": SOURCE,
            "provider_checked_at": data.get("provider_checked_at"), "currency": currency}


def revenue(data, currency): return _calculate(data, "Revenue", currency)
def operating_income(data, currency): return _calculate(data, "Operating Income", currency)
def net_income(data, currency): return _calculate(data, "Net Income", currency)
def free_cash_flow(data, currency): return _calculate(data, "Free Cash Flow", currency)
def operating_margin(data, currency): return _calculate(data, "Operating Margin", currency)

ENGINES = {"Revenue": revenue, "Operating Income": operating_income,
           "Net Income": net_income, "Free Cash Flow": free_cash_flow,
           "Operating Margin": operating_margin}


def run_independently(data, currency):
    """Never allow one card's calculation to prevent the others from loading."""
    results = {}
    for name, engine in ENGINES.items():
        try:
            results[name] = engine(data, currency)
        except Exception:
            results[name] = {"metric": name, "value": None, "history": [],
                             "delta": None, "period": str((data.get("periods") or [""])[0]),
                             "percent": name == "Operating Margin", "status": "error",
                             "previous_value": None, "previous_period": None,
                             "comparison_status": "unavailable", "source": SOURCE,
                             "provider_checked_at": data.get("provider_checked_at"), "currency": currency}
    return results

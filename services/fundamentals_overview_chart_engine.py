"""Independent, source-grounded series for the two Financial Overview charts.

Consumes normalized statement snapshots; never calls a provider or fills missing values.
"""
import math

def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def _value(table, field, period):
    value = (table.get(field) or {}).get(period)
    return float(value) if _finite(value) else None

def _periods(data, count):
    return list(reversed((data.get("periods") or [])[:count]))

def performance_series(data, count=5):
    income = ((data.get("statements") or {}).get("Income Statement") or {})
    cash = ((data.get("statements") or {}).get("Cash Flow") or {})
    rows = []
    for period in _periods(data, count):
        rows.append({
            "Period": period,
            "Revenue": _value(income, "Revenue", period),
            "Operating Income": _value(income, "Operating Income (EBIT)", period),
            "Net Income": _value(income, "Net Income", period),
            "Free Cash Flow": _value(cash, "Free Cash Flow", period),
        })
    return rows

def margin_series(data, count=8):
    income = ((data.get("statements") or {}).get("Income Statement") or {})
    rows = []
    for period in _periods(data, count):
        revenue = _value(income, "Revenue", period)
        operating = _value(income, "Operating Income (EBIT)", period)
        net = _value(income, "Net Income", period)
        rows.append({
            "Period": period,
            "Operating Margin": 100 * operating / revenue if revenue is not None and revenue > 0 and operating is not None else None,
            "Net Income Margin": 100 * net / revenue if revenue is not None and revenue > 0 and net is not None else None,
        })
    return rows

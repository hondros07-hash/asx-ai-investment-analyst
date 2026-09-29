"""Presentation-only Financial Overview table models from normalized provider statements."""
import math

def valid(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def statements(data):
    tables = data.get("statements") or {}
    income = tables.get("Income Statement") or {}
    cash = tables.get("Cash Flow") or {}
    mapping = (("Revenue", income, "Revenue"), ("Gross Profit", income, "Gross Profit"),
               ("Operating Income", income, "Operating Income (EBIT)"),
               ("Net Income", income, "Net Income"), ("EPS", income, "Diluted EPS"),
               ("Free Cash Flow", cash, "Free Cash Flow"))
    return [{"Period": period, **{name: ((table.get(key) or {}).get(period) if valid((table.get(key) or {}).get(period)) else None)
                                 for name, table, key in mapping}}
            for period in (data.get("periods") or [])]

def ratio_rows(data):
    periods = list(reversed(data.get("periods") or []))
    ratios = data.get("ratios") or {}
    income = ((data.get("statements") or {}).get("Income Statement") or {})
    cash = ((data.get("statements") or {}).get("Cash Flow") or {})
    balance = ((data.get("statements") or {}).get("Balance Sheet") or {})
    def field(table, name, period):
        v = (table.get(name) or {}).get(period)
        return v if valid(v) else None
    result = []
    for name in ("Gross Margin", "Operating Margin", "Net Margin", "ROE", "ROIC", "EPS", "Free Cash Flow Margin"):
        values = []
        for period in periods:
            if name == "EPS":
                value = field(income, "Diluted EPS", period)
            elif name == "Free Cash Flow Margin":
                revenue, fcf = field(income, "Revenue", period), field(cash, "Free Cash Flow", period)
                value = fcf / revenue if revenue is not None and revenue > 0 and fcf is not None else None
            elif name == "ROIC":
                # No estimated invested-capital denominator or tax rate.
                value = None
            else:
                value = (ratios.get(period) or {}).get(name)
            values.append(value if valid(value) else None)
        result.append({"Metric": name, "Periods": periods, "Values": values})
    return result

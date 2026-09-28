"""AXÍA V23.7.8: deterministic financial KPI calculations.

Values are raw reported currency units. No synthetic history, inferred currency,
or interpolation. The caller must supply validated, comparable fiscal periods.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Optional, Sequence


@dataclass(frozen=True)
class Observation:
    period: str
    end_date: date
    value: float
    currency: str
    fiscal_type: str  # annual | quarterly
    source: str = ""

    def __post_init__(self):
        if self.fiscal_type not in ("annual", "quarterly"):
            raise ValueError("Unsupported fiscal type")
        if not self.currency or not self.period or not isfinite(self.value):
            raise ValueError("Invalid observation")


@dataclass(frozen=True)
class KPIResult:
    value: Optional[float]
    previous: Optional[float]
    growth_pct: Optional[float]
    currency: Optional[str]
    label: str
    comparison: str
    history: tuple[Observation, ...]
    status: str
    source: str


def format_financial_value(value: Optional[float], currency: str = "", decimals: int = 2) -> str:
    if value is None or not isfinite(value):
        return "N/A"
    if decimals < 0 or decimals > 6:
        raise ValueError("Invalid precision")
    magnitude = abs(value)
    suffix, divisor = next(((s, d) for s, d in (("T", 1e12), ("B", 1e9),
                         ("M", 1e6), ("K", 1e3)) if magnitude >= d), ("", 1))
    prefix = "-" if value < 0 else ""
    symbol = "$" if currency.upper() in ("USD", "AUD", "CAD", "NZD") else ""
    return f"{prefix}{symbol}{magnitude / divisor:,.{decimals}f}{suffix}"


def calculate_growth(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None or previous <= 0:
        return None
    if not isfinite(current) or not isfinite(previous):
        return None
    return (current - previous) / previous * 100


def delta_state(growth: Optional[float], reverse_scale: bool = False) -> str:
    if growth is None or abs(growth) < 1e-10:
        return "neutral"
    return "positive" if (growth < 0 if reverse_scale else growth > 0) else "negative"


def build_kpi(history: Sequence[Observation], mode: str = "annual",
              comparison: str = "yoy", reverse_scale: bool = False) -> KPIResult:
    if mode not in ("annual", "quarterly", "ttm") or comparison not in ("yoy", "qoq"):
        raise ValueError("Invalid mode or comparison")
    expected = "annual" if mode == "annual" else "quarterly"
    rows = sorted((o for o in history if o.fiscal_type == expected), key=lambda o: o.end_date)
    if not rows:
        return KPIResult(None, None, None, None, mode.upper(), comparison.upper(), (), "missing", "")
    if len({o.end_date for o in rows}) != len(rows):
        return KPIResult(None, None, None, None, mode.upper(), comparison.upper(), (), "duplicate_period", "")
    if len({o.currency for o in rows}) != 1:
        return KPIResult(None, None, None, None, mode.upper(), comparison.upper(), (), "currency_mismatch", "")
    currency = rows[-1].currency
    source = rows[-1].source
    if mode == "ttm":
        if len(rows) < 4 or not _consecutive_quarters(rows[-4:]):
            return KPIResult(None, None, None, currency, "TTM", "YoY", tuple(rows), "incomplete_ttm", source)
        current = sum(o.value for o in rows[-4:])
        prior = (sum(o.value for o in rows[-8:-4])
                 if len(rows) >= 8 and _consecutive_quarters(rows[-8:-4])
                 and _consecutive_quarters(rows[-8:]) else None)
        label = "TTM"
        comparison = "yoy"
    else:
        current = rows[-1].value
        lag = 1 if mode == "annual" or comparison == "qoq" else 4
        prior = None
        if len(rows) > lag and _comparable(rows[-1], rows[-1-lag], mode, comparison):
            prior = rows[-1-lag].value
        label = rows[-1].period
    growth = calculate_growth(current, prior)
    status = "ok" if growth is not None else "comparison_unavailable"
    return KPIResult(current, prior, growth, currency, label,
                     comparison.upper(), tuple(rows[-8:]), status, source)


def _quarter(o: Observation) -> int:
    return (o.end_date.month - 1) // 3


def _consecutive_quarters(rows: Sequence[Observation]) -> bool:
    return all((b.end_date.year * 4 + _quarter(b)) -
               (a.end_date.year * 4 + _quarter(a)) == 1
               for a, b in zip(rows, rows[1:]))


def _comparable(a: Observation, b: Observation, mode: str, comparison: str) -> bool:
    if mode == "annual":
        return a.end_date.year - b.end_date.year == 1
    distance = (a.end_date.year * 4 + _quarter(a)) - (b.end_date.year * 4 + _quarter(b))
    return distance == (1 if comparison == "qoq" else 4)


def chart_points(result: KPIResult) -> tuple[dict, ...]:
    """UI-neutral data for lightweight HTML bars and exact-value tooltips."""
    if not result.history:
        return ()
    maximum = max(abs(o.value) for o in result.history) or 1
    return tuple({"period": o.period, "date": o.end_date.isoformat(),
                  "value": o.value, "currency": o.currency,
                  "height_pct": round(abs(o.value) / maximum * 100, 2),
                  "negative": o.value < 0, "source": o.source}
                 for o in result.history)

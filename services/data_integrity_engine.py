"""V23.9: deterministic, Streamlit-free financial data integrity boundary.

Never substitute a currency, ticker, ratio or missing provider value by guesswork.
Flags are machine-readable; the original provider observations remain available.
"""
from __future__ import annotations
import math
import re

EXCHANGES = {"AX": ("ASX", "AU"), "L": ("LSE", "GB"), "TO": ("TSX", "CA"),
             "V": ("TSXV", "CA"), "HK": ("HKEX", "HK"), "T": ("TSE", "JP")}
CURRENCIES = {"USD", "AUD", "CAD", "NZD", "GBP", "EUR", "JPY", "HKD", "CHF",
              "CNY", "SGD", "SEK", "NOK", "DKK", "INR", "KRW", "TWD", "ZAR"}
PERCENT_RATIOS = {"Gross Margin", "Operating Margin", "Net Margin", "ROE", "ROA", "Du Pont ROE"}
NONNEGATIVE_RATIOS = {"Current Ratio", "Quick Ratio", "Debt / Equity", "Asset Turnover", "Equity Multiplier"}

def identity(ticker, meta=None):
    meta = meta or {}
    symbol = str(ticker or "").strip().upper()
    suffix = symbol.rsplit(".", 1)[-1] if "." in symbol else ""
    exchange, country = EXCHANGES.get(suffix, (None, None))
    # Bare symbols such as ZIP are ambiguous: never silently relabel them ASX.
    provider_exchange = str(meta.get("exchange") or "").strip().upper()
    name = str(meta.get("longName") or meta.get("shortName") or "").strip()
    return {"ticker": symbol, "name": name or symbol or "Unknown company",
            "exchange": exchange or provider_exchange or "Unconfirmed",
            "country": country or "Unconfirmed",
            "exchange_confirmed": bool(exchange or provider_exchange),
            "explicit_suffix": bool(exchange)}

def currency_code(meta):
    raw = str((meta or {}).get("financialCurrency") or "").strip().upper()
    return raw if raw in CURRENCIES else "Unconfirmed"

def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def audit_snapshot(data):
    issues = []
    def issue(code, severity, detail, period=None):
        issues.append({"code": code, "severity": severity, "detail": detail, "period": period})
    ident = identity(data.get("ticker"), data.get("meta"))
    currency = currency_code(data.get("meta"))
    if not ident["exchange_confirmed"]:
        issue("exchange_unconfirmed", "warning", "Provider exchange not confirmed; retain explicit ticker suffix.")
    if currency == "Unconfirmed":
        issue("financial_currency_unconfirmed", "warning", "Do not infer statement currency from listing country or quote currency.")
    periods = data.get("periods") or []
    if len(periods) != len(set(periods)):
        issue("duplicate_periods", "error", "Duplicate reporting period labels.")
    statements = data.get("statements") or {}
    for group, table in statements.items():
        for key, values in table.items():
            for period, value in values.items():
                if value is not None and not _finite(value):
                    issue("invalid_statement_value", "error", f"{group}: {key} is non-finite or non-numeric.", period)
    ratios = data.get("ratios") or {}
    sanitized = {}
    for period, values in ratios.items():
        cleaned = {}
        for key, value in values.items():
            if value is None:
                cleaned[key] = None
            elif not _finite(value):
                cleaned[key] = None
                issue("invalid_ratio", "error", f"{key} is non-finite or non-numeric.", period)
            elif key in NONNEGATIVE_RATIOS and value < 0:
                cleaned[key] = None
                issue("invalid_ratio", "error", f"{key} cannot be negative under this definition.", period)
            elif key in PERCENT_RATIOS and abs(value) > 100:
                # 100 is 10,000% in fractional storage: flag extreme values for review,
                # not ordinary negative margins or growth above 100%.
                cleaned[key] = None
                issue("ratio_outlier", "warning", f"{key} exceeds the conservative 10,000% review threshold.", period)
            else:
                cleaned[key] = value
        sanitized[period] = cleaned
    return {"identity": ident, "currency": currency, "ratios": sanitized,
            "issues": issues, "status": "error" if any(i["severity"] == "error" for i in issues)
            else "warning" if issues else "ok"}

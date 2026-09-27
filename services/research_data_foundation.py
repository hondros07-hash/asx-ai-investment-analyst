"""Point-in-time input normalisation. No network calls and no silent currency conversions."""
from __future__ import annotations
from datetime import datetime, timezone
from math import isfinite

FIELD_MAP={
    "free_cash_flow":("freeCashflow","freeCashFlow"),
    "shares_outstanding":("sharesOutstanding","impliedSharesOutstanding"),
    "cash":("totalCash",),
    "debt":("totalDebt",),
    "financial_currency":("financialCurrency",),
    "listing_currency":("currency",),
    "dividend_per_share":("dividendRate",),
    "book_value_per_share":("bookValue",),
    "return_on_equity":("returnOnEquity",),
}
def normalize_fundamentals(meta, source="provider", as_of=None):
    meta=meta or {}
    values={}; provenance={}
    for field, aliases in FIELD_MAP.items():
        for key in aliases:
            value=meta.get(key)
            if value is None or value=="": continue
            if isinstance(value,(int,float)) and (isinstance(value,bool) or not isfinite(value)): continue
            values[field]=value
            provenance[field]={"source":source,"source_field":key,"as_of":as_of,
                               "verified":False}
            break
    return {"inputs":values,"provenance":provenance,
            "retrieved_at":datetime.now(timezone.utc).isoformat(),
            "note":"Provider fields are unverified until reconciled to dated filings; missing values remain missing."}

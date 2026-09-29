"""Global research identity and comparability contract. No inferred FX or fabricated data."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

MARKETS = {
 "ASX": {"country":"AU","currency":"AUD","timezone":"Australia/Sydney","regulator":"ASX"},
 "NASDAQ":{"country":"US","currency":"USD","timezone":"America/New_York","regulator":"SEC EDGAR"},
 "NYSE":{"country":"US","currency":"USD","timezone":"America/New_York","regulator":"SEC EDGAR"},
 "LSE":{"country":"GB","currency":"GBP","timezone":"Europe/London","regulator":"RNS"},
 "HKEX":{"country":"HK","currency":"HKD","timezone":"Asia/Hong_Kong","regulator":"HKEXnews"},
 "TSE":{"country":"JP","currency":"JPY","timezone":"Asia/Tokyo","regulator":"TDnet"},
 "TSX":{"country":"CA","currency":"CAD","timezone":"America/Toronto","regulator":"SEDAR+"},
}
ALIASES={"AX":"ASX","LON":"LSE","HK":"HKEX","TYO":"TSE","TO":"TSX"}
def market_identity(exchange, ticker):
    exchange=ALIASES.get(str(exchange).upper().strip(),str(exchange).upper().strip())
    ticker=str(ticker).upper().strip()
    if exchange not in MARKETS or not ticker or len(ticker)>32 or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.^=_-" for c in ticker):
        raise ValueError("Unsupported exchange or ticker")
    return {"security_id":exchange+":"+ticker,"exchange":exchange,"ticker":ticker,**MARKETS[exchange]}

def normalize_observation(row):
    """Preserve original unit, currency, fiscal period, source and verification status."""
    identity=market_identity(row.get("exchange"),row.get("ticker"))
    metric=row.get("metric")
    if not isinstance(metric,str) or not metric.strip(): raise ValueError("Metric required")
    unit=row.get("unit")
    if unit not in ("currency","shares","ratio","percent","count","price"): raise ValueError("Explicit unit required")
    currency=row.get("currency")
    if unit in ("currency","price") and (not isinstance(currency,str) or len(currency)!=3):
        raise ValueError("Currency required")
    if currency is not None and (not isinstance(currency,str) or len(currency)!=3 or not currency.isalpha()):
        raise ValueError("Invalid currency")
    period=row.get("period")
    if not isinstance(period,str) or not period.strip(): raise ValueError("Reporting period required")
    url=row.get("source_url")
    if not isinstance(url,str) or urlsplit(url).scheme!="https" or not urlsplit(url).hostname:
        raise ValueError("HTTPS source required")
    stamp=row.get("observed_at")
    try: dt=datetime.fromisoformat(stamp.replace("Z","+00:00"))
    except (ValueError,AttributeError): raise ValueError("Timezone-aware observed_at required")
    if dt.tzinfo is None: raise ValueError("Timezone-aware observed_at required")
    value=row.get("value")
    if value is not None:
        if isinstance(value,bool): raise ValueError("Invalid numeric value")
        try: value=Decimal(str(value))
        except InvalidOperation: raise ValueError("Invalid numeric value")
        if not value.is_finite(): raise ValueError("Non-finite value")
    return {**identity,"metric":metric.strip(),"value":str(value) if value is not None else None,
      "unit":unit,"currency":currency.upper() if currency else None,"period":period.strip(),
      "source_url":url,"observed_at":dt.isoformat(),"status":"available" if value is not None else "unavailable"}

def compare_global(a,b,*,verified_fx=None):
    """Compare only like-for-like units/periods, never silently convert currency."""
    if a["metric"]!=b["metric"] or a["unit"]!=b["unit"] or a["period"]!=b["period"]:
        return {"status":"not_comparable","reason":"Metric, unit or reporting period mismatch"}
    if a["value"] is None or b["value"] is None:
        return {"status":"unavailable","reason":"At least one value is missing"}
    if a["currency"]!=b["currency"]:
        return {"status":"not_comparable","reason":"Different currencies; verified conversion required"}
    return {"status":"comparable","left":a["value"],"right":b["value"],"unit":a["unit"],"currency":a["currency"],"period":a["period"]}

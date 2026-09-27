"""Bounded autocomplete discovery; never validate seven Yahoo symbols per keystroke."""
from __future__ import annotations
from functools import lru_cache
import json
import urllib.parse
import urllib.request
from security_search import ALIASES, _country_from_exchange

@lru_cache(maxsize=2048)
def _discover(query: str, key: str):
    # Remote discovery is only a fallback for a local alias miss. No quote/history/info calls.
    from security_search import yahoo_search
    rows = yahoo_search(query, 10)
    if not rows and key:
        try:
            from security_search import _json
            payload = _json("/symbol_search", {"symbol": query, "apikey": key, "outputsize": 10})
            for item in payload.get("data", []):
                rows.append({"Symbol": item.get("symbol", ""), "Company": item.get("instrument_name") or item.get("name") or "", "Exchange": item.get("exchange", ""), "Country": item.get("country", "")})
        except Exception:
            pass
    return rows

def fast_security_suggestions(query: str, key: str = "", limit: int = 10):
    query = str(query or "").strip()
    if len(query) < 2:
        return []
    needle = query.casefold()
    rows = []
    for alias, listings in ALIASES.items():
        if needle in alias:
            for symbol, name, exchange in listings:
                rows.append({"Symbol": symbol, "Company": name, "Exchange": exchange, "Country": _country_from_exchange(exchange, symbol)})
    # Preserve global discovery for securities absent from the small local alias list.
    rows.extend(_discover(query, key or ""))
    seen = set()
    def score(row):
        symbol = str(row.get("Symbol") or "").upper()
        root = symbol.split(".")[0]
        name = str(row.get("Company") or "").casefold()
        upper = query.upper()
        return (0 if symbol == upper or root == upper else 1 if symbol.startswith(upper) or root.startswith(upper) else 2 if name.startswith(needle) else 3, symbol)
    labels = []
    for row in sorted(rows, key=score):
        symbol = str(row.get("Symbol") or "").strip()
        name = str(row.get("Company") or symbol).strip()
        exchange = str(row.get("Exchange") or "").strip()
        country = str(row.get("Country") or _country_from_exchange(exchange, symbol) or "Global").strip()
        if not symbol:
            continue
        identity = (symbol.upper(), exchange.upper())
        if identity in seen:
            continue
        seen.add(identity)
        labels.append(" · ".join((symbol, name, exchange, country)))
        if len(labels) >= max(1, min(int(limit), 10)):
            break
    return labels

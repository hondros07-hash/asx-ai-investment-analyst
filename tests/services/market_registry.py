"""Chrímata global market registry — deterministic configuration, no data fetching."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Tuple

@dataclass(frozen=True)
class MarketConfig:
    code: str
    country: str
    exchange: str
    timezone: str
    primary_index: str
    currency: str
    flag: str
    open_refresh_seconds: int = 60
    closed_refresh_seconds: int = 900

MARKETS: Dict[str, MarketConfig] = {
    "AU": MarketConfig("AU","Australia","ASX","Australia/Sydney","^AXJO","AUD","🇦🇺"),
    "US": MarketConfig("US","United States","NYSE/NASDAQ","America/New_York","^GSPC","USD","🇺🇸"),
    "GB": MarketConfig("GB","United Kingdom","LSE","Europe/London","^FTSE","GBP","🇬🇧"),
    "JP": MarketConfig("JP","Japan","TSE","Asia/Tokyo","^N225","JPY","🇯🇵"),
    "HK": MarketConfig("HK","Hong Kong","HKEX","Asia/Hong_Kong","^HSI","HKD","🇭🇰"),
    "CA": MarketConfig("CA","Canada","TSX","America/Toronto","^GSPTSE","CAD","🇨🇦"),
    "GR": MarketConfig("GR","Greece","ATHEX","Europe/Athens","GD.AT","EUR","🇬🇷"),
}
# Product defaults, not a claim that these are objectively the five largest markets.
DEFAULT_GLOBAL_MARKETS: Tuple[str,...] = ("US","GB","JP","HK","CA")

def get_market(code: str) -> MarketConfig:
    key=(code or "").upper()
    if key not in MARKETS: raise KeyError(f"Unsupported market: {key}")
    return MARKETS[key]

def public_market_registry():
    return {k: asdict(v) for k,v in MARKETS.items()}

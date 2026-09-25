"""Geo-adaptive market layout rules.

Geo is only a default. A saved home-market preference always wins. Client-supplied
forwarding headers must not be trusted unless the deployment marks its edge proxy trusted.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, Optional
from services.market_registry import MARKETS, DEFAULT_GLOBAL_MARKETS

def normalize_country(code: Optional[str]) -> Optional[str]:
    c=(code or "").strip().upper()
    aliases={"UK":"GB","EL":"GR"}
    c=aliases.get(c,c)
    return c if c in MARKETS else None

def resolve_market_layout(
    detected_country: Optional[str]=None,
    user_profile: Optional[Dict[str,Any]]=None,
    *,
    neutral_fallback: str="US",
):
    profile=user_profile or {}
    saved=normalize_country(profile.get("home_market"))
    detected=normalize_country(detected_country)
    home=saved or detected or normalize_country(neutral_fallback) or "US"
    tier=str(profile.get("subscription_tier","free")).lower()
    requested=profile.get("custom_market_slots") or []
    source=requested if tier=="pro" else DEFAULT_GLOBAL_MARKETS
    secondary=[]
    for raw in source:
        code=normalize_country(raw)
        if code and code!=home and code not in secondary:
            secondary.append(code)
        if len(secondary)==5: break
    # Fill any empty slots deterministically without duplicating home.
    for code in DEFAULT_GLOBAL_MARKETS + tuple(MARKETS):
        if code!=home and code not in secondary:
            secondary.append(code)
        if len(secondary)==5: break
    return {"home_market":home,"secondary_markets":secondary[:5],"subscription_tier":tier,
            "geo_source":"saved_preference" if saved else ("detected" if detected else "fallback")}

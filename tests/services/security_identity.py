from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Optional

# Verified primary-listing overrides are deliberately small. They are identity
# rules, not price rules; never infer a primary listing from the magnitude of price.
PRIMARY_BY_COMPANY = {
    "nike": {"ticker":"NKE", "exchange":"NYSE", "country":"United States", "currency":"USD"},
}

CACHE_TTL = {"fast": 60, "medium": 600, "slow": 21600}

def _norm_name(v: str) -> str:
    s=re.sub(r"[^a-z0-9 ]+"," ",str(v or "").lower())
    s=re.sub(r"\b(incorporated|inc|corp|corporation|limited|ltd|plc|company|co|class [ab])\b"," ",s)
    return " ".join(s.split())

def names_compatible(expected: str, actual: str) -> bool:
    a,b=_norm_name(expected),_norm_name(actual)
    if not a or not b:return True
    return a==b or a in b or b in a

def verified_primary_listing(company_name: str) -> Optional[dict]:
    return PRIMARY_BY_COMPANY.get(_norm_name(company_name))

def canonicalize_security(ticker: str, expected_company_name: str = "") -> dict:
    """Return a deterministic canonical identity decision.

    A verified company-name override may move a search selection to its known
    primary listing. Otherwise the supplied ticker is preserved. Price level is
    never used as an identity heuristic.
    """
    supplied=str(ticker or "").upper().strip()
    primary=verified_primary_listing(expected_company_name)
    if primary and supplied != primary["ticker"]:
        return {"ticker":primary["ticker"],"supplied_ticker":supplied,"changed":True,
                "reason":"verified_primary_listing","expected_company":expected_company_name,**primary}
    return {"ticker":supplied,"supplied_ticker":supplied,"changed":False,
            "reason":"selected_listing_preserved","expected_company":expected_company_name}

def safe_classification(info: dict | None, resolved_profile: dict | None = None) -> dict:
    """International-safe metadata cascade. Missing fields remain unavailable."""
    info=info or {}; resolved_profile=resolved_profile or {}
    sector=(info.get("sector") or info.get("sectorDisp") or info.get("category")
            or resolved_profile.get("sector") or resolved_profile.get("Sector"))
    industry=(info.get("industry") or info.get("industryDisp")
              or resolved_profile.get("industry") or resolved_profile.get("Industry"))
    return {"sector":sector or "Sector unavailable", "industry":industry or "Industry unavailable"}

def validate_identity(ticker: str, expected_name: str, provider_info: dict | None) -> dict:
    info=provider_info or {}
    actual=info.get("longName") or info.get("shortName") or ""
    ok=names_compatible(expected_name,actual)
    return {"valid":bool(ok),"ticker":str(ticker or "").upper(),"expected_name":expected_name,
            "provider_name":actual,"exchange":info.get("fullExchangeName") or info.get("exchange"),
            "currency":info.get("currency"),"quote_type":info.get("quoteType"),
            "reason":"identity_match" if ok else "company_name_mismatch"}

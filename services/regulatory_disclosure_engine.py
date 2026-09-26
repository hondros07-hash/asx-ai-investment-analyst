"""AXÍA regulatory disclosure service. Official records are never replaced by news."""
import pandas as pd
from announcement_engine import (
    official_disclosure_gateway, resolve_announcement_market,
    sec_archive, _issuer_ir_fallback, _empty_disclosures,
)

def get_regulatory_announcements(ticker, provider_url="", provider_key="", limit=25,
                                 exchange="", country=""):
    """Return (records, coverage, identity) with explicit source/failure metadata.

    Official SEC legacy adapter is an independent official fallback. Issuer IR is
    clearly marked issuer-sourced, never described as exchange-confirmed.
    """
    identity=resolve_announcement_market(ticker, exchange, country)
    market=identity.get("market", "UNKNOWN")
    try:
        df, coverage, identity=official_disclosure_gateway(
            ticker, provider_url, provider_key, limit, exchange=exchange, country=country)
    except Exception as exc:
        df=_empty_disclosures("UPSTREAM_ERROR", identity.get("authority",market),
                              ticker, [type(exc).__name__])
        coverage=identity.get("authority", market)
    if df is not None and not df.empty:
        df.attrs.setdefault("source_tier", "official")
        return df.head(limit), coverage, identity
    status=str(getattr(df, "attrs", {}).get("status", "UPSTREAM_ERROR"))
    # Missing credentials and mismatched identities must remain visible.
    if status in {"SEC_USER_AGENT_REQUIRED", "IDENTITY_MISMATCH", "IDENTITY_FAILED"}:
        return df, coverage, identity
    if market in {"NYSE", "NASDAQ"}:
        try:
            alt=sec_archive(ticker, limit)
            if alt is not None and not alt.empty:
                alt.attrs.update({"status":"SUCCESS", "source_tier":"official",
                                  "fallback":"SEC EDGAR alternate official adapter"})
                return alt.head(limit), "SEC EDGAR alternate official adapter", identity
        except Exception:
            pass
    if market=="ASX":
        try:
            alt=_issuer_ir_fallback(ticker, market, limit)
            if alt is not None and not alt.empty:
                alt.attrs.update({"status":"ISSUER_FALLBACK", "source_tier":"issuer",
                                  "fallback":"Issuer investor relations; not exchange-verified"})
                return alt.head(limit), "Issuer investor relations (not exchange-verified)", identity
        except Exception:
            pass
    return df, coverage, identity

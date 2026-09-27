"""AXÍA regulatory disclosure service. Official records are never replaced by news."""
import pandas as pd
from announcement_engine import (
    official_disclosure_gateway, resolve_announcement_market,
    sec_archive, _issuer_ir_fallback, _empty_disclosures,
)

import time
import streamlit as st

@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def _cached_regulatory(ticker, provider_url, provider_key, limit, exchange, country, refresh_token):
    """Cache successful and failed retrieval briefly; refresh token permits explicit retry."""
    return _retrieve_regulatory(ticker, provider_url, provider_key, limit, exchange, country)

def _retrieve_regulatory(ticker, provider_url="", provider_key="", limit=25, exchange="", country=""):
    identity=resolve_announcement_market(ticker, exchange, country)
    market=identity.get("market", "UNKNOWN")
    started=time.monotonic()
    diagnostics=[]
    try:
        df, coverage, identity=official_disclosure_gateway(
            ticker, provider_url, provider_key, limit, exchange=exchange, country=country)
    except Exception as exc:
        df=_empty_disclosures("UPSTREAM_ERROR", identity.get("authority",market),
                              ticker, [type(exc).__name__])
        coverage=identity.get("authority",market)
    status=str(getattr(df,"attrs",{}).get("status","UPSTREAM_ERROR"))
    if df is not None and not df.empty:
        df.attrs.update({"source_tier":"official","retrieval_ms":round((time.monotonic()-started)*1000)})
        return df.head(limit), coverage, identity
    if status in {"SEC_USER_AGENT_REQUIRED","IDENTITY_MISMATCH","IDENTITY_FAILED"}:
        return df,coverage,identity
    if market in {"NYSE","NASDAQ"}:
        try:
            alt=sec_archive(ticker,limit)
            if alt is not None and not alt.empty:
                alt.attrs.update({"status":"SUCCESS","source_tier":"official",
                                  "fallback":"SEC EDGAR alternate official adapter",
                                  "retrieval_ms":round((time.monotonic()-started)*1000)})
                return alt.head(limit),"SEC EDGAR alternate official adapter",identity
        except Exception as exc:
            diagnostics.append(type(exc).__name__)
    if market=="ASX":
        try:
            alt=_issuer_ir_fallback(ticker,market,limit)
            if alt is not None and not alt.empty:
                alt.attrs.update({"status":"ISSUER_FALLBACK","source_tier":"issuer",
                                  "fallback":"Issuer investor relations; not exchange-verified",
                                  "retrieval_ms":round((time.monotonic()-started)*1000)})
                return alt.head(limit),"Issuer investor relations (not exchange-verified)",identity
        except Exception as exc:
            diagnostics.append(type(exc).__name__)
    if df is None:
        df=_empty_disclosures("UPSTREAM_ERROR",identity.get("authority",market),ticker,diagnostics)
    df.attrs["retrieval_ms"]=round((time.monotonic()-started)*1000)
    df.attrs["diagnostics"]=list(df.attrs.get("diagnostics") or [])+diagnostics
    return df,coverage,identity

def get_regulatory_announcements(ticker, provider_url="", provider_key="", limit=25,
                                 exchange="", country="", refresh_token=0):
    return _cached_regulatory(ticker,provider_url,provider_key,limit,exchange,country,refresh_token)

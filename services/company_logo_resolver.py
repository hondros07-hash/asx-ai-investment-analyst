"""AXÍA global company logo resolution.

Logo metadata is presentation data only. Resolution must fail closed:
if a usable provider logo cannot be established, return None and allow
the frontend to render its deterministic initials fallback.
"""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

import yfinance as yf


_ALLOWED_SCHEMES = {"http", "https"}


def _valid_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    try:
        parsed = urlparse(value)
    except Exception:
        return None

    if parsed.scheme.lower() not in _ALLOWED_SCHEMES or not parsed.netloc:
        return None

    return value


@lru_cache(maxsize=512)
def resolve_company_logo(ticker: str) -> str | None:
    """Return a provider-supplied company logo URL when available.

    No synthetic logo is produced here. Any provider/network failure
    returns None so callers can use a deterministic visual fallback.
    """
    symbol = ticker.strip().upper()
    if not symbol:
        return None

    try:
        company = yf.Ticker(symbol)

        try:
            fast_info = getattr(company, "fast_info", None)
            if fast_info:
                for key in ("logo_url", "logoUrl"):
                    try:
                        logo = _valid_url(fast_info.get(key))
                    except Exception:
                        logo = None
                    if logo:
                        return logo
        except Exception:
            pass

        try:
            info = company.get_info() or {}
        except Exception:
            info = {}

        for key in ("logo_url", "logoUrl"):
            logo = _valid_url(info.get(key))
            if logo:
                return logo

    except Exception:
        return None

    return None


def _domain_from_url(value: object) -> str | None:
    """Return a normalized corporate domain from a validated website URL."""
    website = _valid_url(value)
    if not website:
        return None

    try:
        hostname = urlparse(website).hostname
    except Exception:
        return None

    if not hostname:
        return None

    domain = hostname.lower().strip(".")
    if domain.startswith("www."):
        domain = domain[4:]

    return domain or None


@lru_cache(maxsize=512)
def resolve_company_domain(ticker: str) -> str | None:
    """Resolve the provider-reported corporate website to a domain.

    Yahoo Finance is used only to establish the company's reported website.
    Provider/network failures return None rather than inventing an identity.
    """
    symbol = ticker.strip().upper()
    if not symbol:
        return None

    try:
        info = yf.Ticker(symbol).get_info() or {}
    except Exception:
        return None

    return _domain_from_url(info.get("website"))

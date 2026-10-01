"""AXÍA SEC regulatory filing connector.

FastAPI-safe official-source connector for U.S. listed companies.
No Streamlit dependency. Issuer identity must reconcile before filings
are returned.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any
from urllib.request import Request, urlopen


SEC_TICKER_DIRECTORY = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions"

INVESTOR_FORMS = {
    "10-K",
    "10-K/A",
    "10-Q",
    "10-Q/A",
    "8-K",
    "8-K/A",
    "20-F",
    "20-F/A",
    "40-F",
    "40-F/A",
    "6-K",
    "6-K/A",
}


def _headers() -> dict[str, str]:
    user_agent = os.getenv("AXIA_SEC_USER_AGENT", "").strip()
    if not user_agent:
        raise RuntimeError("AXIA_SEC_USER_AGENT is not configured.")

    return {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }


def _get_json(url: str, timeout: int = 12) -> dict[str, Any]:
    req = Request(url, headers=_headers())
    with urlopen(req, timeout=timeout) as response:
        payload = json.load(response)

    if not isinstance(payload, dict):
        raise ValueError("SEC response was not a JSON object.")

    return payload


def resolve_sec_issuer(ticker: str) -> dict[str, Any]:
    """Resolve a ticker through the official SEC ticker directory."""
    symbol = str(ticker or "").strip().upper()

    if not symbol:
        return {
            "status": "unavailable",
            "message": "Ticker is required.",
        }

    directory = _get_json(SEC_TICKER_DIRECTORY)

    matches = [
        row
        for row in directory.values()
        if isinstance(row, dict)
        and str(row.get("ticker") or "").strip().upper() == symbol
    ]

    if len(matches) != 1:
        return {
            "status": "unavailable",
            "ticker": symbol,
            "message": (
                "Issuer identity could not be uniquely verified "
                "through the SEC ticker directory."
            ),
        }

    row = matches[0]

    try:
        cik = int(row.get("cik_str"))
    except (TypeError, ValueError):
        return {
            "status": "unavailable",
            "ticker": symbol,
            "message": "Issuer CIK could not be verified.",
        }

    return {
        "status": "available",
        "ticker": symbol,
        "cik": cik,
        "issuer": row.get("title"),
        "source": "SEC company ticker directory",
    }


def _filing_rows(
    recent: dict[str, Any],
    *,
    cik: int,
    investor_only: bool,
    limit: int,
) -> list[dict[str, Any]]:
    fields = (
        "accessionNumber",
        "form",
        "filingDate",
        "primaryDocument",
        "primaryDocDescription",
    )

    columns = [recent.get(field) or [] for field in fields]
    rows: list[dict[str, Any]] = []

    for values in zip(*columns):
        row = dict(zip(fields, values))
        form = str(row.get("form") or "").strip().upper()

        if investor_only and form not in INVESTOR_FORMS:
            continue

        accession = str(row.get("accessionNumber") or "").strip()
        document = str(row.get("primaryDocument") or "").strip()

        if not accession or not document:
            continue

        accession_compact = accession.replace("-", "")
        document_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik}/{accession_compact}/{document}"
        )

        rows.append(
            {
                "form": form,
                "date": row.get("filingDate"),
                "description": row.get("primaryDocDescription") or form,
                "url": document_url,
                "accession_number": accession,
                "source": "SEC EDGAR",
            }
        )

        if len(rows) >= limit:
            break

    return rows


def get_sec_investor_filings(
    ticker: str,
    *,
    limit: int = 250,
) -> dict[str, Any]:
    """Return verified investor-relevant SEC filings for Report Intelligence."""
    symbol = str(ticker or "").strip().upper()

    try:
        identity = resolve_sec_issuer(symbol)
    except Exception as exc:
        return {
            "ticker": symbol,
            "status": "source_unavailable",
            "filings": [],
            "source": "SEC EDGAR",
            "message": f"SEC issuer resolution failed: {type(exc).__name__}",
        }

    if identity.get("status") != "available":
        return {
            **identity,
            "filings": [],
            "source": "SEC EDGAR",
        }

    cik = int(identity["cik"])

    try:
        submissions = _get_json(
            f"{SEC_SUBMISSIONS}/CIK{cik:010d}.json"
        )
    except Exception as exc:
        return {
            "ticker": symbol,
            "issuer": identity.get("issuer"),
            "cik": cik,
            "status": "source_unavailable",
            "filings": [],
            "source": "SEC EDGAR",
            "message": f"SEC submissions retrieval failed: {type(exc).__name__}",
        }

    try:
        returned_cik = int(submissions.get("cik"))
    except (TypeError, ValueError):
        returned_cik = None

    returned_tickers = {
        str(value).strip().upper()
        for value in (submissions.get("tickers") or [])
    }

    if returned_cik != cik or symbol not in returned_tickers:
        return {
            "ticker": symbol,
            "status": "unavailable",
            "filings": [],
            "source": "SEC EDGAR",
            "message": (
                "SEC submissions identity did not reconcile "
                "with the verified issuer."
            ),
        }

    recent = (submissions.get("filings") or {}).get("recent") or {}

    filings = _filing_rows(
        recent,
        cik=cik,
        investor_only=True,
        limit=max(1, min(int(limit), 500)),
    )

    return {
        "ticker": symbol,
        "issuer": submissions.get("name") or identity.get("issuer"),
        "cik": cik,
        "status": "available" if filings else "unavailable",
        "filings": filings,
        "filing_count": len(filings),
        "source": "SEC EDGAR submissions",
        "issuer_verified": True,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "message": None if filings else "No investor-relevant SEC filings found.",
    }

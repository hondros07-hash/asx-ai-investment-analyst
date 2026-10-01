"""AXÍA Report Intelligence Engine.

Market-agnostic normalization and evidence layer for official company filings.

Exchange-specific connectors are responsible for retrieving and verifying
documents. This engine consumes verified filing records and produces a common
Report Intelligence contract without inventing unsupported analysis.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SUPPORTED_REPORT_FORMS = {
    "10-K": "annual_report",
    "10-Q": "quarterly_report",
    "8-K": "current_report",
    "20-F": "annual_report",
    "40-F": "annual_report",
    "6-K": "foreign_issuer_report",
}


def classify_filing(form: str | None) -> str:
    """Map an exchange-specific filing form to an AXÍA report category."""
    normalized = str(form or "").strip().upper()
    return SUPPORTED_REPORT_FORMS.get(normalized, "other_filing")


def normalize_filing(
    filing: dict[str, Any],
    *,
    ticker: str,
    issuer: str | None,
    issuer_verified: bool = False,
    exchange: str | None = None,
    market: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Convert a verified provider filing into AXÍA's common filing schema."""
    form = str(filing.get("form") or "").strip()

    return {
        "ticker": ticker.strip().upper(),
        "issuer": issuer,
        "exchange": exchange,
        "market": market,
        "form": form or None,
        "report_type": classify_filing(form),
        "filing_date": filing.get("date"),
        "description": filing.get("description"),
        "document_url": filing.get("url"),
        "source": source,
        "issuer_verified": bool(issuer_verified),
        "document_verified": False,
        "official_document_url": filing.get("url"),
    }


def prioritize_filings(
    filings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Prioritize decision-useful reports without deleting official filings.

    All filings remain available. Annual, quarterly, current-event and
    foreign-issuer reports are simply presented before lower-priority forms.
    """
    priority = {
        "annual_report": 0,
        "quarterly_report": 1,
        "current_report": 2,
        "foreign_issuer_report": 3,
        "other_filing": 4,
    }

    # Stable two-pass sort: newest first within each report category,
    # then decision-useful report categories before lower-priority filings.
    by_date = sorted(
        filings,
        key=lambda row: str(row.get("filing_date") or ""),
        reverse=True,
    )

    return sorted(
        by_date,
        key=lambda row: priority.get(str(row.get("report_type")), 99),
    )


def build_report_intelligence(
    *,
    ticker: str,
    issuer: str | None,
    issuer_verified: bool = False,
    filings: list[dict[str, Any]],
    source: str | None,
    exchange: str | None = None,
    market: str | None = None,
) -> dict[str, Any]:
    """Build the deterministic Report Intelligence foundation.

    This stage intentionally does not claim document extraction, financial
    interpretation, KPI analysis or AI-generated conclusions. Those layers
    must only become available when backed by retrieved source evidence.
    """
    normalized = [
        normalize_filing(
            filing,
            ticker=ticker,
            issuer=issuer,
            issuer_verified=issuer_verified,
            exchange=exchange,
            market=market,
            source=source,
        )
        for filing in filings
        if isinstance(filing, dict)
    ]

    prioritized = prioritize_filings(normalized)

    decision_reports = [
        row
        for row in prioritized
        if row["report_type"] != "other_filing"
    ]

    return {
        "ticker": ticker.strip().upper(),
        "issuer": issuer,
        "exchange": exchange,
        "market": market,
        "status": "available" if prioritized else "unavailable",
        "source": source,
        "issuer_verified": bool(issuer_verified),
        "filing_count": len(prioritized),
        "decision_report_count": len(decision_reports),
        "filings": prioritized,
        "decision_reports": decision_reports,
        "intelligence": {
            "document_extraction": "not_connected",
            "financial_analysis": "not_connected",
            "kpi_analysis": "not_connected",
            "risk_analysis": "not_connected",
            "guidance_analysis": "not_connected",
            "period_comparison": "not_connected",
        },
        "evidence_policy": {
            "official_source_required": True,
            "issuer_reconciliation_required": True,
            "unsupported_values_allowed": False,
            "unsupported_conclusions_allowed": False,
        },
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def select_core_reports(
    filings: list[dict[str, Any]],
    *,
    annual_limit: int = 2,
    quarterly_limit: int = 4,
    current_limit: int = 8,
    foreign_limit: int = 8,
) -> dict[str, list[dict[str, Any]]]:
    """Select the core reports required for investment research.

    Selection operates on AXÍA-normalized filings. It does not remove or
    rewrite the complete regulatory filing history.
    """
    ordered = prioritize_filings(filings)

    annual = [
        row for row in ordered
        if row.get("report_type") == "annual_report"
    ][:annual_limit]

    quarterly = [
        row for row in ordered
        if row.get("report_type") == "quarterly_report"
    ][:quarterly_limit]

    current = [
        row for row in ordered
        if row.get("report_type") == "current_report"
    ][:current_limit]

    foreign = [
        row for row in ordered
        if row.get("report_type") == "foreign_issuer_report"
    ][:foreign_limit]

    return {
        "annual": annual,
        "quarterly": quarterly,
        "current": current,
        "foreign": foreign,
    }

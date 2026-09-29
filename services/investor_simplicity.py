"""AXÍA investor-focused simplicity: evidence-preserving research brief.

Pure presentation adapter: no provider calls, fabricated metrics, trading signals,
or mutation of upstream research records.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

SECTIONS = (
    ("business", "What does the company do?"),
    ("performance", "What has changed in performance?"),
    ("valuation", "What does the valuation assume?"),
    ("risks", "What could challenge the thesis?"),
    ("catalysts", "What should I monitor next?"),
)
VALID_STATES = {"verified", "model", "interpretation", "unavailable"}


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def build_investor_brief(company: Mapping[str, Any], research: Mapping[str, Any]) -> dict[str, Any]:
    """Create a five-question brief from explicitly supplied, attributed evidence.

    research keys are the five section IDs. Each value may contain summary,
    status, source, as_of, and detail_url. Missing attribution never becomes
    verified evidence; missing sections remain visibly unavailable.
    """
    if not isinstance(company, Mapping) or not isinstance(research, Mapping):
        raise TypeError("company and research must be mappings")
    identity = _clean(company.get("name")) or _clean(company.get("ticker")) or "Company"
    ticker = _clean(company.get("ticker"))
    sections = []
    for key, question in SECTIONS:
        raw = research.get(key)
        entry = raw if isinstance(raw, Mapping) else {}
        summary = _clean(entry.get("summary"))
        source = _clean(entry.get("source"))
        as_of = _clean(entry.get("as_of"))
        status = _clean(entry.get("status")).lower()
        if status not in VALID_STATES:
            status = "unavailable"
        if not summary or (status == "verified" and (not source or not as_of)):
            status = "unavailable"
            summary = "Evidence unavailable. Open the detailed research page for source diagnostics."
        elif status == "unavailable":
            summary = "Evidence unavailable. Open the detailed research page for source diagnostics."
        sections.append({
            "id": key, "question": question, "summary": summary,
            "evidence_status": status, "source": source if status != "unavailable" else "",
            "as_of": as_of if status != "unavailable" else "",
            "detail_url": _clean(entry.get("detail_url")),
        })
    return {
        "schema_version": "1.0",
        "company": identity, "ticker": ticker,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
        "available_count": sum(s["evidence_status"] != "unavailable" for s in sections),
        "total_count": len(sections),
        "notice": "Research context, not a buy/sell/hold recommendation. Verify sources and dates.",
    }

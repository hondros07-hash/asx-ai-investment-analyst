"""V23.11: validation for user-authored research evidence (no UI dependencies)."""
from __future__ import annotations
import math
from urllib.parse import urlparse


def validate_research_condition(metric, threshold, current, source):
    """Return (valid, message). Missing values must never be interpreted as zero."""
    if not str(metric or "").strip():
        return False, "Enter the metric or thesis condition."
    if not str(source or "").strip():
        return False, "Add a report, filing, provider, or evidence reference before evaluating a condition."
    if current is None:
        return False, "Enter a reported value; missing evidence must remain Pending."
    try:
        if not math.isfinite(float(current)) or not math.isfinite(float(threshold)):
            return False, "Values must be finite numbers."
    except (TypeError, ValueError):
        return False, "Enter valid numeric values."
    return True, ""


def evidence_reference(source):
    """Only expose safe HTTP(S) URLs as links; other references remain readable text."""
    value = str(source or "").strip()
    try:
        parsed = urlparse(value)
        if parsed.scheme in ("http", "https") and parsed.netloc and not parsed.username and not parsed.password:
            return {"label": value, "url": value}
    except ValueError:
        pass
    return {"label": value, "url": None}

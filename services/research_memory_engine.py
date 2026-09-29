"""Deterministic, provider-independent research evidence and thesis change detection.

No network calls, account access, automated trading, or fabricated investment verdicts.
Persistence belongs to the authenticated storage layer; this module only compares records.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from typing import Any

ALLOWED_STATES = {"supported", "contradicted", "unverified", "not_applicable"}

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def evidence_digest(evidence: dict) -> str:
    required = ("security_id", "metric", "period", "source_url", "observed_at", "value")
    if any(k not in evidence for k in required):
        raise ValueError("Evidence must contain identity, metric, period, source, time and value")
    if not isinstance(evidence["source_url"], str) or not evidence["source_url"].startswith("https://"):
        raise ValueError("Evidence requires an HTTPS source URL")
    if not isinstance(evidence["security_id"], str) or not evidence["security_id"].strip():
        raise ValueError("Evidence requires a security identity")
    value = evidence["value"]
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("Non-finite evidence value")
    return sha256(canonical_json({k: evidence[k] for k in required}).encode("utf-8")).hexdigest()

def compare_snapshots(previous: dict, current: dict) -> dict:
    """Compare immutable metric snapshots; never infer direction or investment merit."""
    if previous.get("security_id") != current.get("security_id"):
        raise ValueError("Cannot compare different securities")
    if previous.get("currency") != current.get("currency"):
        raise ValueError("Cannot compare different currencies without verified conversion")
    before, after = previous.get("metrics", {}), current.get("metrics", {})
    changes = []
    for metric in sorted(set(before) | set(after)):
        old, new = before.get(metric), after.get(metric)
        if old == new:
            continue
        changes.append({"metric": metric, "previous": old, "current": new,
                        "change_type": "added" if metric not in before else "removed" if metric not in after else "changed"})
    return {"security_id": current["security_id"], "currency": current.get("currency"),
            "previous_snapshot_id": previous.get("id"), "current_snapshot_id": current.get("id"),
            "changes": changes, "changed_count": len(changes)}

def evaluate_condition(condition: dict, evidence: dict | None) -> dict:
    """A rule is unverified unless a matching sourced observation is available."""
    metric = condition.get("metric")
    op = condition.get("operator")
    threshold = condition.get("threshold")
    if op not in {">", ">=", "<", "<=", "=="} or not isinstance(threshold, (int, float)) or not isfinite(threshold):
        raise ValueError("Invalid measurable thesis condition")
    if evidence is None or evidence.get("metric") != metric or evidence.get("value") is None:
        return {"state": "unverified", "reason": "Matching observation unavailable"}
    evidence_digest(evidence)
    value = evidence["value"]
    if not isinstance(value, (int, float)) or not isfinite(value):
        return {"state": "unverified", "reason": "Observation is not a finite number"}
    if condition.get("period") != evidence.get("period") or condition.get("security_id") != evidence.get("security_id"):
        return {"state": "unverified", "reason": "Security or reporting period mismatch"}
    if condition.get("currency") != evidence.get("currency"):
        return {"state": "unverified", "reason": "Currency mismatch"}
    operations = {">": value > threshold, ">=": value >= threshold, "<": value < threshold,
                  "<=": value <= threshold, "==": value == threshold}
    return {"state": "supported" if operations[op] else "contradicted",
            "reason": "Measured rule comparison; not an investment recommendation",
            "evidence_digest": evidence_digest(evidence), "observed_at": evidence["observed_at"]}

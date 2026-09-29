"""Explainability contracts for AXÍA research, independent of provider and UI.

A provider-transcribed observation is not issuer-verified. Missing evidence never
becomes a calculated or verified value. No AI narrative is generated here.
"""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json

OPERATORS = {"add", "subtract", "multiply", "divide"}
STATUS = {"provider_transcribed", "issuer_verified", "model_estimate", "unverified"}

def _decimal(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("Numeric observation required")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid number") from exc
    if not number.is_finite():
        raise ValueError("Non-finite number")
    return number

def _time(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must contain timezone")
    if parsed > datetime.now(timezone.utc):
        raise ValueError("Observation cannot be in the future")
    return parsed.isoformat()

def observation(row):
    """Return a source-aware observation; never elevate a provider to issuer verified."""
    required = ("security_id", "metric", "value", "unit", "period", "source_name", "source_url", "observed_at", "verification")
    missing = [field for field in required if field not in row]
    if missing:
        raise ValueError("Missing evidence fields: " + ", ".join(missing))
    if row["verification"] not in STATUS:
        raise ValueError("Unknown verification status")
    if not isinstance(row["source_url"], str) or not row["source_url"].startswith("https://"):
        raise ValueError("HTTPS source required")
    for field in ("security_id", "metric", "unit", "period", "source_name"):
        if not isinstance(row[field], str) or not row[field].strip():
            raise ValueError("Invalid " + field)
    stamp = _time(row["observed_at"])
    value = None if row["value"] is None else _decimal(row["value"])
    if value is None and row["verification"] != "unverified":
        raise ValueError("Missing value must be unverified")
    if row["verification"] == "issuer_verified" and not row.get("issuer_reconciled", False):
        raise ValueError("Issuer verification requires explicit reconciliation")
    normalized = {key: row[key] for key in required}
    normalized["observed_at"] = stamp
    normalized["value"] = str(value) if value is not None else None
    normalized["issuer_reconciled"] = bool(row.get("issuer_reconciled", False))
    digest = sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**normalized, "evidence_id": digest}

def explain_calculation(metric, operator, inputs, *, unit, period, assumptions=None):
    """Produce an auditable arithmetic trace from compatible observations."""
    if operator not in OPERATORS or not isinstance(inputs, list) or len(inputs) != 2:
        raise ValueError("Two inputs and a supported operation are required")
    items = [observation(item) for item in inputs]
    if items[0]["security_id"] != items[1]["security_id"] or any(x["period"] != period for x in items):
        raise ValueError("Security or reporting period mismatch")
    if operator in ("add", "subtract") and (items[0]["unit"] != items[1]["unit"] or items[0]["unit"] != unit):
        raise ValueError("Incompatible units")
    assumptions = assumptions or {}
    if not isinstance(assumptions, dict) or len(assumptions) > 12:
        raise ValueError("Invalid assumptions")
    if any(x["value"] is None or x["verification"] == "unverified" for x in items):
        return {"status": "unavailable", "value": None, "reason": "Input evidence missing or unverified", "inputs": items}
    a, b = (_decimal(x["value"]) for x in items)
    if operator == "divide" and b == 0:
        return {"status": "unavailable", "value": None, "reason": "Division by zero", "inputs": items}
    result = {"add": lambda: a+b, "subtract": lambda: a-b, "multiply": lambda: a*b, "divide": lambda: a/b}[operator]()
    if not result.is_finite():
        raise ValueError("Non-finite result")
    return {"status": "calculated", "value": str(result), "metric": metric, "unit": unit, "period": period,
            "security_id": items[0]["security_id"], "method": operator, "inputs": items,
            "assumptions": assumptions, "issuer_verified": all(x["verification"] == "issuer_verified" for x in items),
            "interpretation": "Arithmetic calculation only; no investment conclusion"}

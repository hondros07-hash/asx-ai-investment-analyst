"""Evidence-gated models for the capital bridge and data confidence cards.

A cash-flow bridge is not a claim that all free cash flow has been allocated.
Only provider-backed operating cash flow, capex and free cash flow are displayed.
"""
import math
from services.fundamentals_integrity_engine import validate, summary

def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def capital_bridge(data):
    periods = data.get("periods") or []
    period = periods[0] if periods else None
    cf = ((data.get("statements") or {}).get("Cash Flow") or {})
    def read(name):
        value = (cf.get(name) or {}).get(period)
        return value if finite(value) else None
    ocf, capex, fcf = read("Operating Cash Flow"), read("Capital Expenditure"), read("Free Cash Flow")
    derived = ("Free Cash Flow", period) in (data.get("derived") or {})
    comparable = all(finite(x) for x in (ocf, capex, fcf))
    difference = fcf - (ocf - abs(capex)) if comparable else None
    tolerance = max(1.0, abs(ocf)*0.001) if comparable else None
    reconciles = comparable and abs(difference) <= tolerance
    return {"period":period,"currency":data.get("currency") or "Unconfirmed",
            "ocf":ocf,"capex":-abs(capex) if capex is not None else None,
            "fcf":fcf,"fcf_derived":derived,"reconciles":reconciles,
            "difference":difference,"tolerance":tolerance,
            "note":("FCF is derived from operating cash flow less absolute capital expenditure."
                    if derived else "Provider FCF compared with operating cash flow less absolute capital expenditure."
                    if comparable else "Insufficient comparable cash-flow data for a complete bridge."),
            "allocation_available":False}

def confidence(data):
    checks = validate(data)
    counts = summary(checks)
    passed = counts.get("Pass",0)
    mismatches = counts.get("Mismatch",0)+counts.get("Definition differs",0)+counts.get("Invalid",0)
    provider = counts.get("Provider-reported",0)
    filing_links = 0 # Only count issuer- and period-matched, verified filing references.
    return {"passed":passed,"mismatches":mismatches,"provider_reported":provider,
            "filing_links":filing_links,"not_testable":counts.get("Not testable",0),
            "provisional":counts.get("Provisional",0),"unconfirmed":counts.get("Unconfirmed",0),
            "checks":checks,"provider":data.get("provider") or "Provider unspecified",
            "filing_verified":False}

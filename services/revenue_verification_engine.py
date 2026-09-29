"""Conservative, on-demand SEC reconciliation for annual US issuer revenue.

Never infer issuer identity from an ambiguous ticker or claim revenue is a live quote.
Network failures, unmatched dates, currency, concepts or periods fail closed.
"""
from datetime import date, datetime, timezone
from math import isfinite
import os
import requests

SEC = "https://data.sec.gov"
HEADERS = {"User-Agent": os.getenv("AXIA_SEC_USER_AGENT", "AXIA Research contact research@axiaindex.com"),
           "Accept-Encoding": "gzip, deflate", "Host": "data.sec.gov"}
CONCEPTS = ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet")
TOLERANCE = 0.005


def _valid(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and isfinite(v)


def _result(status, reason, **extra):
    return {"status": status, "reason": reason, **extra}


def reconcile_annual_revenue(ticker, data, get=None):
    """Return three evidence-backed statuses for one exact US listing/period."""
    get = get or requests.get
    periods = data.get("periods") or []
    period = str(periods[0]) if periods else ""
    revenue = ((data.get("statements") or {}).get("Income Statement") or {}).get("Revenue", {}).get(period)
    currency = str(data.get("currency") or "")
    checked = datetime.now(timezone.utc).isoformat()
    base = {"ticker": ticker, "period": period, "currency": currency, "checked_at": checked,
            "independent": _result("Unavailable", "No independent evidence obtained."),
            "filing": _result("Pending", "No matching official filing reconciled."),
            "snapshot": _result("Not tested", "Revenue is a periodic filing metric, not a live quote.")}
    if not _valid(revenue) or not period:
        base["filing"]["reason"] = "No valid provider revenue and reporting period."
        return base
    if data.get("frequency") != "Annual (5Y)" or not str(ticker).upper().isalnum():
        base["independent"]["reason"] = "SEC reconciliation supports annual US listings only; exchange-specific evidence is required."
        return base
    if currency != "USD":
        base["independent"]["reason"] = "SEC comparison requires matching USD statement currency."
        return base
    try:
        target = date.fromisoformat(period)
        if not os.getenv("AXIA_SEC_USER_AGENT"):
            base["independent"]["reason"] = "Set AXIA_SEC_USER_AGENT with an identifiable application and contact before SEC requests."
            return base
        # SEC's ticker directory is an issuer identity lookup, not a revenue source.
        directory = get("https://www.sec.gov/files/company_tickers.json",
                        headers={"User-Agent": HEADERS["User-Agent"]}, timeout=12)
        directory.raise_for_status()
        matches = [v for v in directory.json().values() if str(v.get("ticker","")).upper() == str(ticker).upper()]
        if len(matches) != 1:
            base["independent"]["reason"] = "SEC ticker-to-CIK mapping is missing or ambiguous."
            return base
        cik = str(matches[0]["cik_str"]).zfill(10)
        response = get(SEC + "/api/xbrl/companyfacts/CIK" + cik + ".json",
                       headers=HEADERS, timeout=12)
        response.raise_for_status()
        facts = response.json()
        if str(facts.get("cik", "")).lstrip("0") != cik.lstrip("0"):
            base["independent"]["reason"] = "SEC issuer identity did not match the mapped CIK."
            return base
        candidates = []
        for concept in CONCEPTS:
            for item in facts.get("facts", {}).get("us-gaap", {}).get(concept, {}).get("units", {}).get("USD", []):
                if item.get("form") != "10-K" or item.get("end") != period or not _valid(item.get("val")):
                    continue
                try:
                    duration = (date.fromisoformat(item["end"]) - date.fromisoformat(item["start"])).days
                except (ValueError, KeyError, TypeError):
                    continue
                if not 330 <= duration <= 380 or not item.get("accn") or not item.get("filed"):
                    continue
                candidates.append((item["filed"], concept, item))
        if not candidates:
            base["independent"]["reason"] = "No matching full-year USD revenue fact in an SEC 10-K for this period."
            return base
        _, concept, fact = max(candidates, key=lambda x: x[0])
        filing_url = "https://www.sec.gov/Archives/edgar/data/" + str(int(cik)) + "/" + fact["accn"].replace("-", "") + "/"
        base["independent"] = _result("Available", "Independent official SEC companyfacts revenue retrieved.",
                                       source="SEC EDGAR companyfacts", concept=concept, cik=cik, url=filing_url)
        difference = abs(float(revenue) - float(fact["val"]))
        tolerance = max(1.0, abs(float(fact["val"])) * TOLERANCE)
        base["filing"] = _result("Verified" if difference <= tolerance else "Mismatch",
                                 "Provider revenue reconciles to the matching SEC annual fact within 0.5%." if difference <= tolerance else "Provider and SEC revenue differ beyond 0.5%; inspect revenue definitions and filing.",
                                 provider_value=float(revenue), official_value=fact["val"], difference=difference,
                                 tolerance=tolerance, period=period, currency="USD", filed=fact["filed"], url=filing_url)
        base["snapshot"] = _result("Not applicable", "Annual revenue cannot be confirmed as a live quote; the SEC filing is a dated financial report.")
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        base["independent"]["reason"] = "SEC retrieval or parsing failed: " + type(exc).__name__
    return base

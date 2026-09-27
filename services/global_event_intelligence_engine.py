"""AXÍA V23.8.3: evidence-gated global-event exposure and attention routing.

Pure Python; provider adapters supply sourced event records. No fabricated live
events, predictions, political conclusions or arbitrary numeric impact scores.
"""
from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import urlparse
from difflib import SequenceMatcher

EVENT_TYPES={"government_policy","central_bank","geopolitical","economic","commodity_energy","supply_chain","climate_disaster","technology_systemic"}
POLICY_STATES={"proposed","passed","effective","withdrawn","not_applicable"}
CHANNELS={"funding_cost","consumer_demand","foreign_exchange","commodity_cost","supply_chain","regulatory_compliance","revenue_exposure","asset_exposure"}
def _domain(url):
    try:
        p=urlparse(str(url or ""))
        return p.hostname if p.scheme=="https" and p.hostname else None
    except (ValueError,TypeError): return None

def normalize_global_event(raw):
    e=dict(raw)
    kind=str(e.get("event_type") or "").lower()
    title=str(e.get("title") or "").strip()
    url=str(e.get("source_url") or "").strip()
    published=str(e.get("published_at") or "").strip()
    if kind not in EVENT_TYPES or not title or not _domain(url) or not published:
        return None
    try:
        dt=datetime.fromisoformat(published.replace("Z","+00:00"))
        if dt.tzinfo is None: return None
    except (ValueError,TypeError): return None
    state=str(e.get("policy_status") or "not_applicable").lower()
    if kind=="government_policy" and state not in POLICY_STATES: return None
    return {"title":title,"event_type":kind,"source_url":url,
            "source_name":str(e.get("source_name") or _domain(url)),
            "published_at":dt.astimezone(timezone.utc).isoformat(),
            "policy_status":state if kind=="government_policy" else "not_applicable",
            "jurisdictions":tuple(str(x).upper() for x in (e.get("jurisdictions") or [])),
            "event_id":str(e.get("event_id") or url),
            "evidence_status":"source_linked_not_independently_verified"}

def map_company_exposure(event, company):
    """Only explicit company exposure channels qualify; no headline-only guessing."""
    countries={str(x).upper() for x in company.get("operating_countries",[]) or []}
    jurisdictions=set(event["jurisdictions"])
    if jurisdictions and not (countries & jurisdictions): return []
    mapped=[]
    for item in company.get("exposures",[]) or []:
        channel=str(item.get("channel") or "")
        if channel not in CHANNELS: continue
        applicable=set(item.get("event_types") or [])
        if event["event_type"] not in applicable: continue
        evidence=item.get("evidence_url")
        if not _domain(evidence): continue
        mapped.append({"channel":channel,"mechanism":str(item.get("mechanism") or "Exposure requires review"),
                       "company_evidence_url":evidence,"event_source_url":event["source_url"],
                       "assessment":"potential_exposure_not_quantified"})
    return mapped

def attention_from_global_events(ticker, company, events, limit=5):
    out=[]
    for raw in events or []:
        event=normalize_global_event(raw)
        if not event: continue
        for exposure in map_company_exposure(event,company):
            out.append({"ticker":ticker,"title":event["title"],
                        "detail":exposure["mechanism"],"category":event["event_type"],
                        "status":"Review","source_url":event["source_url"],
                        "company_evidence_url":exposure["company_evidence_url"],
                        "published_at":event["published_at"],
                        "policy_status":event["policy_status"],
                        "assessment":exposure["assessment"],"event_id":event["event_id"]})
    unique=[]
    for row in out:
        if any(x["event_id"]==row["event_id"] and x["category"]==row["category"] and x["detail"]==row["detail"] for x in unique):continue
        unique.append(row)
    unique.sort(key=lambda x:x["published_at"],reverse=True)
    return unique[:max(0,int(limit))]

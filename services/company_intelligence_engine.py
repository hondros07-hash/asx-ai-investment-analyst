"""AXÍA V23.7.0: evidence-first orchestration; no headline-only causal claims."""
from services.exposure_registry import DEFAULT_EXPOSURE_RULES
from services.intelligence_event_gateway import normalize_event
from services.thesis_status_engine import calculate_thesis_status

def orchestrate_company_synthesis(ticker, sector='', raw_event=None, exposures=(), thesis_conditions=(), previous_kpis=None, latest_kpis=None):
    raw_event=raw_event or {}
    event=normalize_event(raw_event)
    verified=[x for x in exposures if x.get('verified') is True and x.get('source') and x.get('evidence_id') and x.get('exposure_key')]
    missing=[]
    if event.get('status')!='accepted': missing.append('structured event classification')
    if not verified: missing.append('verified company exposure mapping')
    if not (raw_event.get('verified') is True and raw_event.get('source') and raw_event.get('evidence_id')): missing.append('verified event source and evidence identifier')
    if raw_event.get('ticker') and str(raw_event['ticker']).upper()!=str(ticker).upper(): missing.append('matching company ticker')
    rules=[r for r in DEFAULT_EXPOSURE_RULES if r.exposure_key in {x['exposure_key'] for x in verified} and event.get('event_key') in r.event_keys]
    if not rules: missing.append('verified event-to-exposure mapping')
    if missing:
        return {'status':'insufficient_evidence','what_changed':'No material company-specific change has been established from verified inputs.', 'why_it_matters':'A sourced event and verified company exposure are required before mapping financial implications.', 'affected_kpis':[], 'thesis_impact':'unknown','thesis_status_change':'unknown','directional_pressure':'unknown','magnitude':'unknown','what_to_watch_next':missing,'what_would_change_the_thesis':['New verified evidence linking a material event to an existing thesis condition.'],'valuation_link':{'status':'not_established'},'missing_evidence':missing,'provenance':{'ai_calculated_math':False}}
    kpis=list(dict.fromkeys(k for r in rules for k in r.affected_kpis))
    watched=list(dict.fromkeys(k for r in rules for k in r.monitoring_items))
    direction=event.get('direction')
    pressures={'positive' if direction==r.positive_when else 'negative' if direction==r.negative_when else 'unknown' for r in rules}
    known=pressures-{'unknown'}
    pressure=next(iter(known)) if len(known)==1 else 'mixed' if len(known)>1 else 'unknown'
    states=calculate_thesis_status(thesis_conditions)['conditions']
    linked={c for r in rules for c in r.thesis_conditions}
    relevant=[c for c in states if c['metric'] in linked]
    impact='unknown' if not relevant else 'watch' if any(c['state']=='watch' for c in relevant) else 'supported' if all(c['state']=='on_track' for c in relevant) else 'pending'
    changes=[]
    import math
    for k in kpis:
        before=(previous_kpis or {}).get(k); after=(latest_kpis or {}).get(k)
        if type(before) in (int,float) and type(after) in (int,float) and math.isfinite(before) and math.isfinite(after):
            changes.append({'kpi':k,'previous':before,'latest':after,'absolute_change':after-before,'comparison_period':raw_event.get('comparison_period')})
    return {'status':'mapped','what_changed':event.get('what_changed') or str(raw_event.get('fact') or ''),'why_it_matters':' '.join(r.impact_channel for r in rules),'affected_kpis':kpis,'thesis_impact':impact,'thesis_status_change':impact,'directional_pressure':pressure,'magnitude':'unknown','what_to_watch_next':watched,'what_would_change_the_thesis':['A subsequent verified report establishing the direction and size of affected KPIs.'],'valuation_link':{'status':'not_established'},'kpi_changes':changes,'missing_evidence':[] if pressure!='unknown' else ['verified event direction'],'provenance':{'source':raw_event['source'],'evidence_id':raw_event['evidence_id'],'published_at':raw_event.get('published_at'),'url':raw_event.get('url'),'company_exposure_sources':[x['source'] for x in verified],'ai_calculated_math':False}}

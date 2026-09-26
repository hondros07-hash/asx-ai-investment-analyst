"""V23.4.6: presentation-only adapter for the canonical deterministic DCF result.

Never estimates missing scenarios, invents FX, or changes underlying assumptions.
"""
from datetime import datetime, timezone
import math


def finite(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError, OverflowError):
        return None


INPUT_LABELS = {
    'fcf': 'Free cash flow', 'shares': 'Shares outstanding',
    'cash': 'Cash balance', 'debt': 'Total debt',
    'financial_currency': 'Financial statement currency',
    'listing_currency': 'Listing currency',
}

def valuation_diagnostics(result):
    """Explain evidence coverage without manufacturing missing financial inputs."""
    result = result if isinstance(result, dict) else {}
    audit = result.get('audit') or {}
    inputs = audit.get('inputs') or {}
    rows = []
    for key, label in INPUT_LABELS.items():
        item = inputs.get(key) or {}
        value = finite(item.get('value')) if key not in ('financial_currency', 'listing_currency') else item.get('value')
        status = item.get('status') or 'missing'
        if key == 'fcf' and value is not None and value <= 0:
            status = 'non_positive'
        if key == 'shares' and value is not None and value <= 0:
            status = 'invalid'
        rows.append({'key': key, 'label': label, 'status': status,
                     'source': item.get('source'), 'value': value,
                     'period': item.get('period'), 'reason': item.get('reason')})
    blockers = list(audit.get('blocking_reasons') or [])
    if result.get('reason') and result['reason'] not in blockers:
        blockers.append(str(result['reason']))
    if not blockers and result.get('status') != 'success':
        blockers.append('Complete, verified valuation evidence is not available.')
    missing = [r['label'] for r in rows if r['status'] in ('missing', 'non_positive', 'invalid')]
    return {'inputs': rows, 'blockers': blockers, 'missing': missing,
            'cash_or_debt_assumed_zero': any(r['status'] == 'missing' for r in rows if r['key'] in ('cash', 'debt')),
            'fx': audit.get('fx') or {}, 'bridge': audit.get('primary_listing_bridge') or {},
            'ready': result.get('status') == 'success'}

def summarize_valuation(result, reference_price=None, ticker=None):
    result = result if isinstance(result, dict) else {}
    scenarios = result.get('scenarios') or {}
    price = finite(reference_price)
    if price is None or price <= 0:
        price = None
    values = {}
    for name in ('Bear', 'Base', 'Bull'):
        source = scenarios.get(name) or {}
        value = finite(source.get('value_per_share'))
        values[name.lower()] = {
            'price': value,
            'delta_pct': (value / price - 1) * 100 if value is not None and price else None,
            'assumptions': source.get('assumptions') if value is not None else None,
            'status': 'available' if value is not None else 'unavailable',
        }
    available = [x['price'] for x in values.values() if x['price'] is not None]
    lo, hi = (min(available), max(available)) if available else (None, None)
    # A single-valued range has no meaningful proportional placement.
    positions = {k: (max(0., min(100., (v['price']-lo)/(hi-lo)*100))
                     if v['price'] is not None and lo is not None and hi > lo else None)
                 for k,v in values.items()}
    diagnostics = valuation_diagnostics(result)
    missing = []
    if len(available) != 3: missing.append('complete_bear_base_bull_model_results')
    if price is None: missing.append('verified_positive_reference_price')
    if not result.get('listing_currency'): missing.append('verified_listing_currency')
    state = ('unsupported' if result.get('status') == 'unsupported' else
             'available' if len(available) == 3 else 'partial' if available else 'insufficient_evidence')
    return {
        'status': state, 'ticker': ticker or result.get('security'),
        'bear_price': values['bear']['price'], 'bear_delta_pct': values['bear']['delta_pct'],
        'base_price': values['base']['price'], 'base_delta_pct': values['base']['delta_pct'],
        'bull_price': values['bull']['price'], 'bull_delta_pct': values['bull']['delta_pct'],
        'scenarios': values, 'marker_positions_pct': positions,
        'reference_price': price, 'currency': result.get('listing_currency'),
        'financial_currency': result.get('financial_currency'),
        'methodology': result.get('methodology'), 'assumption_template': result.get('assumption_template'),
        'assumptions_are_model_templates': True,
        'provenance': result.get('audit') or {}, 'reason': result.get('reason'),
        'missing_inputs': missing, 'diagnostics': diagnostics, 'calculated_at': datetime.now(timezone.utc).isoformat(),
        'ai_calculated_math': False,
    }

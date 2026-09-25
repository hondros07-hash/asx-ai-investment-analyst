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
        'missing_inputs': missing, 'calculated_at': datetime.now(timezone.utc).isoformat(),
        'ai_calculated_math': False,
    }

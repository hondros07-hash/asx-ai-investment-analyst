"""Verified relationship templates for the synthesis core.

These are relationship schemas, not claims that any specific company has the exposure.
A company must separately carry a verified exposure_key before a rule can be used.
"""
from services.synthesis_core import ExposureRule

DEFAULT_EXPOSURE_RULES=[
    ExposureRule(
        exposure_key="fuel_cost_sensitive",
        event_keys=["crude_oil_price","jet_fuel_price"],
        affected_kpis=["fuel_expense","operating_margin","free_cash_flow"],
        impact_channel="Higher verified fuel input costs can pressure operating costs when the company has material unhedged fuel exposure; lower costs can relieve that pressure.",
        positive_when="down", negative_when="up",
        thesis_conditions=["cost_control","operating_margin"],
        valuation_variables=["operating_margin","free_cash_flow"],
        monitoring_items=["fuel hedging disclosures","fuel expense","operating margin"]
    ),
    ExposureRule(
        exposure_key="consumer_credit_loss_sensitive",
        event_keys=["consumer_delinquency","unemployment","credit_loss_rate"],
        affected_kpis=["credit_losses","transaction_margin","cash_ebitda"],
        impact_channel="Deteriorating verified consumer credit conditions can pressure credit-loss metrics where the company has relevant consumer receivables exposure.",
        positive_when="down", negative_when="up",
        thesis_conditions=["credit_losses_remain_controlled"],
        valuation_variables=["cash_ebitda","free_cash_flow"],
        monitoring_items=["credit loss rate","arrears/delinquency disclosures","transaction margin","cash EBITDA"]
    ),
    ExposureRule(
        exposure_key="interest_rate_sensitive_funding",
        event_keys=["policy_rate","market_interest_rate","funding_spread"],
        affected_kpis=["funding_cost","net_interest_expense","free_cash_flow"],
        impact_channel="Higher verified rates or funding spreads can increase financing costs where floating-rate or refinancing exposure is material.",
        positive_when="down", negative_when="up",
        thesis_conditions=["funding_cost_control"],
        valuation_variables=["free_cash_flow","discount_rate"],
        monitoring_items=["debt maturity profile","funding cost","refinancing disclosures"]
    ),
]

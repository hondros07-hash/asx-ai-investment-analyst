from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List

@dataclass(frozen=True)
class ThesisCriterion:
    key: str
    label: str
    evidence_type: str

TEMPLATES: Dict[str, List[ThesisCriterion]] = {
    "bank": [
        ThesisCriterion("net_interest_margin","Net interest margin","reported_kpi"),
        ThesisCriterion("cet1","CET1 / capital strength","reported_kpi"),
        ThesisCriterion("revenue_growth","Revenue growth","financial_statement"),
        ThesisCriterion("earnings_growth","Earnings growth","financial_statement"),
        ThesisCriterion("credit_losses","Credit losses / bad debts","reported_kpi"),
        ThesisCriterion("roe","Return on equity","financial_statement"),
    ],
    "airline": [
        ThesisCriterion("revenue_growth","Revenue growth","financial_statement"),
        ThesisCriterion("operating_margin","Operating margin","calculated"),
        ThesisCriterion("free_cash_flow","Free cash flow health","financial_statement"),
        ThesisCriterion("capacity_demand","Capacity / demand trend","reported_kpi"),
        ThesisCriterion("fuel_cost","Fuel cost discipline","reported_kpi"),
        ThesisCriterion("leverage","Balance-sheet leverage","provider_metric"),
    ],
    "consumer_brand": [
        ThesisCriterion("revenue_growth","Revenue growth","financial_statement"),
        ThesisCriterion("earnings_growth","Earnings growth","financial_statement"),
        ThesisCriterion("operating_margin","Operating margin","calculated"),
        ThesisCriterion("inventory_health","Inventory health","financial_statement"),
        ThesisCriterion("free_cash_flow","Free cash flow health","financial_statement"),
        ThesisCriterion("roe","Return on equity","financial_statement"),
    ],
    "technology": [
        ThesisCriterion("revenue_growth","Revenue growth","financial_statement"),
        ThesisCriterion("earnings_growth","Earnings growth","financial_statement"),
        ThesisCriterion("operating_margin","Operating margin","calculated"),
        ThesisCriterion("free_cash_flow","Free cash flow health","financial_statement"),
        ThesisCriterion("roe","Return on equity","financial_statement"),
        ThesisCriterion("guidance","Guidance / product execution","event_evidence"),
    ],
    "mining": [
        ThesisCriterion("production","Production trend","reported_kpi"),
        ThesisCriterion("unit_costs","Unit costs / AISC","reported_kpi"),
        ThesisCriterion("revenue_growth","Revenue growth","financial_statement"),
        ThesisCriterion("operating_margin","Operating margin","calculated"),
        ThesisCriterion("free_cash_flow","Free cash flow health","financial_statement"),
        ThesisCriterion("reserves","Reserves / resource quality","reported_kpi"),
    ],
    "reit": [
        ThesisCriterion("ffo","FFO / AFFO growth","reported_kpi"),
        ThesisCriterion("occupancy","Occupancy","reported_kpi"),
        ThesisCriterion("wale","WALE / lease quality","reported_kpi"),
        ThesisCriterion("free_cash_flow","Cash flow health","financial_statement"),
        ThesisCriterion("gearing","Gearing","reported_kpi"),
        ThesisCriterion("distribution","Distribution sustainability","reported_kpi"),
    ],
    "payments": [
        ThesisCriterion("revenue_growth","Revenue / transaction growth","financial_statement"),
        ThesisCriterion("earnings_growth","Earnings growth","financial_statement"),
        ThesisCriterion("operating_margin","Operating margin","calculated"),
        ThesisCriterion("credit_losses","Credit losses / bad debts","reported_kpi"),
        ThesisCriterion("free_cash_flow","Free cash flow health","financial_statement"),
        ThesisCriterion("guidance","Guidance / catalyst execution","event_evidence"),
    ],
    "corporate": [
        ThesisCriterion("revenue_growth","Revenue growth","financial_statement"),
        ThesisCriterion("earnings_growth","Earnings growth","financial_statement"),
        ThesisCriterion("operating_margin","Operating margin","calculated"),
        ThesisCriterion("free_cash_flow","Free cash flow health","financial_statement"),
        ThesisCriterion("roe","Return on equity","financial_statement"),
        ThesisCriterion("guidance","Guidance / catalyst execution","event_evidence"),
    ],
}

def classify_thesis_template(ticker: str, company_name: str = "", sector: str = "", industry: str = "") -> str:
    """Deterministic business-model classifier. No AI and no financial scoring."""
    x=" ".join(map(str,(ticker,company_name,sector,industry))).lower()
    if any(k in x for k in ("bank","banking","credit union")): return "bank"
    if any(k in x for k in ("airline","air transportation","qantas","aviation")): return "airline"
    if any(k in x for k in ("reit","real estate investment trust")): return "reit"
    if any(k in x for k in ("mining","miner","gold","copper","lithium","metals & mining")): return "mining"
    if any(k in x for k in ("payments","buy now pay later","bnpl","consumer finance","zip co")): return "payments"
    if any(k in x for k in ("software","semiconductor","technology","internet content","consumer electronics")): return "technology"
    if any(k in x for k in ("footwear","apparel","luxury goods","restaurants","retail","consumer cyclical","consumer defensive","beverage")): return "consumer_brand"
    return "corporate"

def get_thesis_template(ticker: str, company_name: str = "", sector: str = "", industry: str = "") -> dict:
    template=classify_thesis_template(ticker,company_name,sector,industry)
    return {"template":template,"criteria":[asdict(x) for x in TEMPLATES[template]],"total_conditions":6,"ai_calculated":False}

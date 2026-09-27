"""AXÍA V23.8.4: portable portfolio position accounting foundation.

Costs are in quote currency; fees included in acquisition basis if provided.
No inferred tax status, FX conversions, or beta estimates.
"""
from datetime import date
from math import isfinite

def position_summary(lots, price=None, portfolio_value=None, as_of=None):
    as_of=as_of or date.today()
    if isinstance(as_of,str): as_of=date.fromisoformat(as_of)
    quantity=cost=0.0
    tax_lots=[]
    for lot in lots or []:
        q=float(lot["quantity"]); unit=float(lot["unit_cost"]); fees=float(lot.get("fees",0))
        if not all(isfinite(x) for x in (q,unit,fees)) or q<=0 or unit<0 or fees<0:
            raise ValueError("Invalid acquisition lot")
        basis=q*unit+fees
        quantity+=q; cost+=basis
        acquired=lot.get("acquired_on")
        holding_days=None
        if acquired:
            d=date.fromisoformat(str(acquired))
            holding_days=(as_of-d).days
            if holding_days<0: raise ValueError("Acquisition date is in the future")
        tax_lots.append({"quantity":q,"basis":basis,"acquired_on":acquired,
                         "holding_days":holding_days,"potential_12_month_status":
                         "review_eligibility" if holding_days is not None and holding_days>365 else
                         "not_yet_or_unknown"})
    market=None; pnl=None; weight=None
    if price is not None:
        p=float(price)
        if not isfinite(p) or p<0: raise ValueError("Invalid price")
        market=quantity*p; pnl=market-cost
        if portfolio_value is not None:
            total=float(portfolio_value)
            if not isfinite(total) or total<=0: raise ValueError("Invalid portfolio value")
            weight=market/total
    return {"shares":quantity,"cost_basis":cost,"average_cost":cost/quantity if quantity else None,
            "market_value":market,"unrealised_pnl":pnl,"portfolio_weight":weight,
            "tax_lots":tax_lots,"tax_note":"Holding period alone does not establish CGT discount eligibility.",
            "risk_contribution":None,"risk_status":"requires portfolio return/covariance data"}

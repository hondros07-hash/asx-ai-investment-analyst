
import numpy as np
import pandas as pd

def dcf(fcf, shares, net_debt=0, growth_1_5=.10, wacc=.10, terminal_growth=.03, years=5):
    if wacc <= terminal_growth:
        raise ValueError("WACC must be greater than terminal growth.")
    flows=[]
    cur=float(fcf)
    pv=0.0
    for y in range(1,years+1):
        cur*=1+growth_1_5
        discounted=cur/((1+wacc)**y)
        pv+=discounted
        flows.append({"year":y,"fcf":cur,"pv":discounted})
    terminal=cur*(1+terminal_growth)/(wacc-terminal_growth)
    terminal_pv=terminal/((1+wacc)**years)
    enterprise=pv+terminal_pv
    equity=enterprise-float(net_debt)
    per_share=equity/float(shares) if shares else np.nan
    return {"enterprise_value":enterprise,"equity_value":equity,
            "value_per_share":per_share,"terminal_value":terminal,
            "terminal_pv":terminal_pv,"cashflows":pd.DataFrame(flows)}

def scenarios(fcf,shares,net_debt,assumptions):
    rows=[]
    for name,a in assumptions.items():
        r=dcf(fcf,shares,net_debt,a["growth"],a["wacc"],a["terminal_growth"])
        rows.append({"scenario":name,"growth":a["growth"],"wacc":a["wacc"],
                     "terminal_growth":a["terminal_growth"],"value_per_share":r["value_per_share"]})
    return pd.DataFrame(rows)

def multiples_value(metric, peer_multiple, shares=None):
    ev=float(metric)*float(peer_multiple)
    return ev if not shares else ev/float(shares)

def margin_of_safety(price,intrinsic):
    return intrinsic/price-1 if price else np.nan


import numpy as np
from valuation_lab import dcf

def implied_growth(price, fcf, shares, net_debt=0, wacc=.10, terminal_growth=.03,
                   low=-.30, high=.80, iterations=100):
    """
    Solves for constant 5-year FCF growth required for DCF value ~= current price.
    """
    if price<=0 or fcf<=0 or shares<=0:
        return np.nan
    lo,hi=low,high
    for _ in range(iterations):
        mid=(lo+hi)/2
        val=dcf(fcf,shares,net_debt,mid,wacc,terminal_growth)["value_per_share"]
        if val < price: lo=mid
        else: hi=mid
    return (lo+hi)/2

def expectations_gap(implied, historical):
    if implied is None or historical is None:
        return np.nan
    try:return float(implied)-float(historical)
    except:return np.nan

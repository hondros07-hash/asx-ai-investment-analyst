
import numpy as np
import pandas as pd

def liquidity_cost_bps(adv_dollars, order_dollars, base_bps=8, impact_bps=35):
    if not adv_dollars or adv_dollars<=0:return np.nan
    participation=max(float(order_dollars)/float(adv_dollars),0)
    return float(base_bps + impact_bps*np.sqrt(participation))

def apply_cost(ret, turnover, cost_bps):
    return float(ret) - float(turnover)*float(cost_bps)/10000

def adjusted_total_return(close, dividends=None):
    r=close.pct_change()
    if dividends is not None:
        d=dividends.reindex(close.index).fillna(0)
        r=r+d/close.shift(1)
    return r

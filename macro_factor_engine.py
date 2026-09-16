
"""
V9 Macro / Commodity feature helpers.
Input series must themselves be historically dated and point-in-time safe.
"""

import numpy as np
import pandas as pd

def macro_panel(series_map):
    """
    series_map: dict name -> pandas Series with DatetimeIndex.
    Joins series, forward fills only AFTER observations exist, then derives changes.
    """
    if not series_map:
        return pd.DataFrame()
    x=pd.concat([s.rename(k) for k,s in series_map.items()],axis=1).sort_index()
    x=x.ffill()
    for c in list(x.columns):
        if c in ["cash_rate","au_10y_yield","inflation_yoy","unemployment","market_volatility"]:
            x[c+"_chg_3m"]=x[c].diff(63)
        else:
            x[c+"_ret_1m"]=x[c].pct_change(21)
            x[c+"_ret_3m"]=x[c].pct_change(63)
            x[c+"_ret_6m"]=x[c].pct_change(126)
    x["date"]=x.index
    return x.reset_index(drop=True)

def join_macro(market_panel, macro):
    if macro is None or macro.empty:
        return market_panel
    left=market_panel.copy()
    left["date"]=pd.to_datetime(left["date"])
    right=macro.copy()
    right["date"]=pd.to_datetime(right["date"])
    return left.merge(right,on="date",how="left")

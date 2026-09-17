
"""
V9 Point-in-Time Evidence Engine

Purpose
-------
Create a clean interface for dated fundamental, valuation, revisions and macro data.
The engine only makes a row available AFTER its `available_date`.

This is the crucial bridge between V8's price-only ML and a future
Fundamental + Valuation + Quant + Technical + Macro ensemble.

No current financial statement is silently copied backwards through history.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd

FUNDAMENTAL_FIELDS = [
    "revenue_growth","eps_growth","ebitda_margin","operating_margin",
    "fcf_margin","roe","roic","net_debt_ebitda","current_ratio",
    "cash_conversion"
]
VALUATION_FIELDS = [
    "pe","forward_pe","ev_ebitda","price_sales","price_book",
    "fcf_yield","dividend_yield"
]
REVISION_FIELDS = [
    "eps_revision_1m","eps_revision_3m","revenue_revision_3m",
    "target_price_revision_3m"
]
MACRO_FIELDS = [
    "cash_rate","au_10y_yield","audusd","inflation_yoy","unemployment",
    "oil_return_3m","gold_return_3m","copper_return_3m",
    "iron_ore_return_3m","market_volatility"
]

def validate_pit_table(df, name="PIT table"):
    required={"ticker","period_end","available_date"}
    missing=required-set(df.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")
    x=df.copy()
    x["ticker"]=x["ticker"].astype(str).str.upper()
    x["period_end"]=pd.to_datetime(x["period_end"], errors="coerce")
    x["available_date"]=pd.to_datetime(x["available_date"], errors="coerce")
    if x[["period_end","available_date"]].isna().any().any():
        raise ValueError(f"{name} contains invalid dates")
    bad=x["available_date"] < x["period_end"]
    if bad.any():
        raise ValueError(f"{name} has rows available before period_end")
    return x.sort_values(["ticker","available_date","period_end"])

def point_in_time_join(market_panel, pit_table, fields=None):
    """
    For every ticker/date in market_panel, attach the latest record whose
    available_date <= market date. Uses merge_asof independently by ticker.
    """
    m=market_panel.copy()
    m["ticker"]=m["ticker"].astype(str).str.upper()
    m["date"]=pd.to_datetime(m["date"])
    p=validate_pit_table(pit_table)
    fields=fields or [c for c in p.columns if c not in
                      ["ticker","period_end","available_date"]]
    keep=["ticker","period_end","available_date"]+fields
    p=p[keep]
    out=[]
    for ticker,g in m.groupby("ticker"):
        left=g.sort_values("date")
        right=p[p.ticker==ticker].sort_values("available_date")
        if right.empty:
            out.append(left)
            continue
        joined=pd.merge_asof(
            left, right.drop(columns=["ticker"]),
            left_on="date", right_on="available_date",
            direction="backward", allow_exact_matches=True
        )
        out.append(joined)
    return pd.concat(out,ignore_index=True).sort_values(["date","ticker"])

def freshness_days(panel):
    x=panel.copy()
    if "available_date" in x:
        x["fundamental_age_days"]=(pd.to_datetime(x.date)-pd.to_datetime(x.available_date)).dt.days
    return x

def winsorize_cross_section(panel, cols, lower=.02, upper=.98):
    x=panel.copy()
    for c in cols:
        if c not in x: continue
        def cap(s):
            lo=s.quantile(lower); hi=s.quantile(upper)
            return s.clip(lo,hi)
        x[c]=x.groupby("date")[c].transform(cap)
    return x

def sector_neutral_zscores(panel, cols):
    x=panel.copy()
    groups=["date","sector"] if "sector" in x.columns else ["date"]
    for c in cols:
        if c not in x: continue
        def z(s):
            sd=s.std()
            return (s-s.mean())/sd if pd.notna(sd) and sd>0 else s*0
        x[f"z_{c}"]=x.groupby(groups,dropna=False)[c].transform(z)
    return x

def derive_fundamental_factors(panel):
    x=panel.copy()
    def mean_existing(names):
        cols=[n for n in names if n in x]
        return x[cols].mean(axis=1) if cols else pd.Series(np.nan,index=x.index)

    # Higher is better. Leverage is inverted.
    quality=[]
    for c in ["roe","roic","operating_margin","fcf_margin","cash_conversion"]:
        z=f"z_{c}"
        if z in x: quality.append(z)
    if "z_net_debt_ebitda" in x:
        x["z_inv_leverage"]=-x["z_net_debt_ebitda"]; quality.append("z_inv_leverage")
    x["fundamental_quality"]=mean_existing(quality)

    growth=[f"z_{c}" for c in ["revenue_growth","eps_growth"] if f"z_{c}" in x]
    x["fundamental_growth"]=mean_existing(growth)

    # Lower valuation multiples are generally more attractive; yields are positive.
    value=[]
    for c in ["pe","forward_pe","ev_ebitda","price_sales","price_book"]:
        z=f"z_{c}"
        if z in x:
            inv=f"z_inv_{c}"; x[inv]=-x[z]; value.append(inv)
    for c in ["fcf_yield","dividend_yield"]:
        z=f"z_{c}"
        if z in x:value.append(z)
    x["valuation_factor"]=mean_existing(value)

    rev=[f"z_{c}" for c in REVISION_FIELDS if f"z_{c}" in x]
    x["revision_factor"]=mean_existing(rev)
    return x

def load_pit_csv(path_or_buffer):
    x=pd.read_csv(path_or_buffer)
    return validate_pit_table(x)

def template():
    cols=["ticker","period_end","available_date"]+FUNDAMENTAL_FIELDS+VALUATION_FIELDS+REVISION_FIELDS
    return pd.DataFrame(columns=cols)


"""
V9 Extended Ensemble
Adds point-in-time fundamental/valuation/revision/macro factors to V8 models
when those fields are genuinely available.
"""

import numpy as np
import pandas as pd
from ensemble_engine import train_competing_models

BASE_PRICE = [
    "mom1","mom3","mom6","mom12","vol20","vol60",
    "dist50","dist200","rsi","volume_ratio","drawdown","rel3"
]
PIT_FACTORS = [
    "fundamental_quality","fundamental_growth",
    "valuation_factor","revision_factor"
]
MACRO_CANDIDATES = [
    "cash_rate","cash_rate_chg_3m","au_10y_yield","au_10y_yield_chg_3m",
    "audusd_ret_1m","audusd_ret_3m","inflation_yoy","inflation_yoy_chg_3m",
    "unemployment","unemployment_chg_3m","oil_ret_3m","gold_ret_3m",
    "copper_ret_3m","iron_ore_ret_3m","market_volatility"
]

def available_features(panel):
    candidates=BASE_PRICE+PIT_FACTORS+MACRO_CANDIDATES
    return [c for c in candidates if c in panel.columns and panel[c].notna().sum()>=100]

def train_v9(panel,horizon="3M",objective="outperform"):
    feats=available_features(panel)
    result=train_competing_models(panel,horizon=horizon,objective=objective,feature_cols=feats)
    if result is not None:
        result["v9_feature_groups"]={
            "price":[c for c in feats if c in BASE_PRICE],
            "fundamental":[c for c in feats if c in PIT_FACTORS],
            "macro":[c for c in feats if c in MACRO_CANDIDATES]
        }
    return result

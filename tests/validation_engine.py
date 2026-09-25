
from __future__ import annotations
import numpy as np, pandas as pd

def purged_chronological_split(df, train_frac=.6, val_frac=.2, horizon_days=21):
    """Chronological train/validation/test split with a purge gap around boundaries.
    horizon_days must match the forward-label horizon so training labels cannot
    reach into validation/test periods.
    """
    n=len(df)
    a=int(n*train_frac); b=int(n*(train_frac+val_frac)); g=int(horizon_days)
    train=df.iloc[:max(0,a-g)].copy()
    val=df.iloc[min(n,a+g):max(min(n,b-g),min(n,a+g))].copy()
    test=df.iloc[min(n,b+g):].copy()
    return train,val,test

def non_overlapping_forward_returns(close, horizon):
    """Forward returns sampled at non-overlapping horizon boundaries."""
    s=pd.Series(close).dropna()
    starts=np.arange(0,max(0,len(s)-horizon),horizon)
    rows=[]
    for i in starts:
        j=i+horizon
        if j<len(s):
            rows.append((s.index[i],float(s.iloc[j]/s.iloc[i]-1)))
    return pd.Series(dict(rows),name=f"fwd_{horizon}")

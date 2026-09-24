
import numpy as np
import pandas as pd

def surprise(actual, consensus):
    if actual is None or consensus in (None, 0) or pd.isna(actual) or pd.isna(consensus):
        return np.nan
    return (float(actual)-float(consensus))/abs(float(consensus))

def earnings_surprise_table(rows):
    """
    rows: iterable of dicts with metric, consensus, actual and optional higher_is_better.
    """
    out=[]
    for r in rows:
        s=surprise(r.get("actual"),r.get("consensus"))
        hib=r.get("higher_is_better",True)
        adjusted=s if hib else (-s if pd.notna(s) else s)
        out.append({**r,"surprise_pct":s,"quality_adjusted_surprise":adjusted})
    return pd.DataFrame(out)

def surprise_score(df):
    if df is None or df.empty or "quality_adjusted_surprise" not in df:
        return np.nan
    x=df["quality_adjusted_surprise"].dropna().clip(-.50,.50)
    if x.empty:return np.nan
    # descriptive score, not a return prediction
    return float(np.clip(x.mean()/0.05,-1,1)*10)

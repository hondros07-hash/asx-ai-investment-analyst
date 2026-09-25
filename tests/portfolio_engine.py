
import numpy as np, pandas as pd

def portfolio_analytics(price_frame, weights, benchmark=None):
    rets=price_frame.pct_change().dropna(how="all")
    w=pd.Series(weights,dtype=float).reindex(rets.columns).fillna(0)
    if w.sum()!=0:w=w/w.sum()
    pr=rets.mul(w,axis=1).sum(axis=1)
    ann_return=(1+pr.mean())**252-1
    ann_vol=pr.std()*np.sqrt(252)
    curve=(1+pr).cumprod()
    dd=curve/curve.cummax()-1
    out={"annualised_return":ann_return,"annualised_volatility":ann_vol,
         "max_drawdown":dd.min(),"correlation":rets.corr(),
         "weights":w,"portfolio_returns":pr}
    if benchmark is not None:
        b=benchmark.pct_change().reindex(pr.index).dropna()
        aligned=pd.concat([pr,b],axis=1).dropna()
        if len(aligned)>20:
            cov=aligned.cov().iloc[0,1]
            var=aligned.iloc[:,1].var()
            out["beta"]=cov/var if var else np.nan
    return out

def concentration(weights):
    w=np.array(list(weights.values()),dtype=float)
    w=w/w.sum() if w.sum() else w
    return float(np.sum(w*w))

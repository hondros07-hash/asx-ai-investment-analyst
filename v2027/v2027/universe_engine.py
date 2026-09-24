
import numpy as np
import pandas as pd
import yfinance as yf

HORIZONS = {"1M":21, "3M":63, "6M":126}

def normalize_tickers(tickers):
    out=[]
    for t in tickers:
        t=t.strip().upper()
        if not t: continue
        out.append(t if "." in t or t.startswith("^") else t+".AX")
    return list(dict.fromkeys(out))

def download_universe(tickers, period="10y"):
    tickers=normalize_tickers(tickers)
    raw=yf.download(tickers, period=period, interval="1d", auto_adjust=True,
                    group_by="ticker", threads=True, progress=False)
    frames={}
    if len(tickers)==1:
        x=raw.copy()
        if not x.empty: frames[tickers[0]]=x
    else:
        for t in tickers:
            try:
                x=raw[t].dropna(how="all").copy()
                if not x.empty: frames[t]=x
            except: pass
    return frames

def _rsi(s,n=14):
    d=s.diff()
    g=d.clip(lower=0).rolling(n).mean()
    l=(-d.clip(upper=0)).rolling(n).mean()
    return 100-(100/(1+g/l.replace(0,np.nan)))

def make_features(df, benchmark=None):
    x=df.copy().sort_index()
    x["ret1"]=x.Close.pct_change()
    x["mom1"]=x.Close.pct_change(21)
    x["mom3"]=x.Close.pct_change(63)
    x["mom6"]=x.Close.pct_change(126)
    x["mom12"]=x.Close.pct_change(252)
    x["vol20"]=x.ret1.rolling(20).std()*np.sqrt(252)
    x["vol60"]=x.ret1.rolling(60).std()*np.sqrt(252)
    x["sma50"]=x.Close.rolling(50).mean()
    x["sma200"]=x.Close.rolling(200).mean()
    x["dist50"]=x.Close/x.sma50-1
    x["dist200"]=x.Close/x.sma200-1
    x["rsi"]= _rsi(x.Close)
    x["volume_ratio"]=x.Volume/x.Volume.rolling(20).mean()
    x["drawdown"]=x.Close/x.Close.cummax()-1
    if benchmark is not None and not benchmark.empty:
        b=benchmark.Close.reindex(x.index).ffill()
        x["benchmark3"]=b.pct_change(63)
        x["rel3"]=x.mom3-x.benchmark3
    else: x["rel3"]=np.nan
    for h,d in HORIZONS.items():
        x[f"fwd_{h}"]=x.Close.shift(-d)/x.Close-1
    return x

FEATURES=["mom1","mom3","mom6","mom12","vol20","vol60","dist50","dist200","rsi","volume_ratio","drawdown","rel3"]

def build_panel(frames, benchmark=None):
    parts=[]
    for ticker,df in frames.items():
        if len(df)<300: continue
        x=make_features(df,benchmark)
        x["ticker"]=ticker
        x["date"]=x.index
        parts.append(x.reset_index(drop=True))
    return pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()

def cross_sectional_scores(panel):
    x=panel.copy()
    # percentile ranks by date prevent comparing raw factor magnitudes across eras.
    rank_specs={
        "value_proxy":"dist200",       # cheaper relative to own long trend (prototype proxy)
        "momentum":"mom6",
        "quality_proxy":"rel3",        # placeholder until PIT fundamentals arrive
        "growth_proxy":"mom12",        # placeholder until PIT earnings growth arrives
        "low_vol":"vol60"
    }
    for name,col in rank_specs.items():
        if col not in x: continue
        ascending = name=="low_vol"
        r=x.groupby("date")[col].rank(pct=True,ascending=not ascending)
        # For low vol, lower raw vol should score higher.
        if name=="low_vol": r=x.groupby("date")[col].rank(pct=True,ascending=False)
        x[name+"_score"]=r
    score_cols=[c for c in x.columns if c.endswith("_score")]
    x["qvm_score"]=x[[c for c in score_cols if c in ["value_proxy_score","momentum_score","low_vol_score"]]].mean(axis=1)
    x["multi_factor_score"]=x[score_cols].mean(axis=1)
    return x

def strategy_backtest(panel, horizon="3M", score="multi_factor_score",
                      top_quantile=.20, rebalance_days=21, cost_bps=10):
    target=f"fwd_{horizon}"
    x=panel.dropna(subset=[score,target]).sort_values("date").copy()
    dates=pd.Index(sorted(x.date.unique()))
    dates=dates[::rebalance_days]
    rows=[]
    cost=cost_bps/10000
    for dt in dates:
        day=x[x.date==dt].copy()
        if len(day)<5: continue
        cutoff=day[score].quantile(1-top_quantile)
        selected=day[day[score]>=cutoff]
        if selected.empty: continue
        gross=selected[target].mean()
        rows.append({"date":dt,"n":len(selected),"gross_return":gross,
                     "net_return":gross-cost,"hit_rate":(selected[target]>0).mean(),
                     "avg_score":selected[score].mean()})
    return pd.DataFrame(rows)

def strategy_summary(bt):
    if bt.empty:return {}
    r=bt.net_return.dropna()
    curve=(1+r).cumprod()
    dd=curve/curve.cummax()-1
    return {
        "periods":len(r),
        "mean_period_return":float(r.mean()),
        "median_period_return":float(r.median()),
        "hit_rate":float((r>0).mean()),
        "total_compounded_return":float(curve.iloc[-1]-1) if len(curve) else np.nan,
        "max_drawdown":float(dd.min()) if len(dd) else np.nan,
        "avg_names":float(bt.n.mean())
    }

def universe_latest(panel, score="multi_factor_score", n=20):
    if panel.empty:return pd.DataFrame()
    dt=panel.date.max()
    cols=["ticker","date",score,"mom1","mom3","mom6","mom12","vol60","rsi","drawdown","rel3"]
    return panel[panel.date==dt].dropna(subset=[score]).sort_values(score,ascending=False)[cols].head(n)

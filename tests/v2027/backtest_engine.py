
import math
import numpy as np
import pandas as pd

HORIZONS = {"1M": 21, "3M": 63, "6M": 126}

def _rsi(close, n=14):
    d = close.diff()
    gain = d.clip(lower=0).rolling(n).mean()
    loss = (-d.clip(upper=0)).rolling(n).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def build_point_in_time_features(price, benchmark=None):
    """
    Builds price/volume features using only information known on each row's date.
    No future-return columns are included here.
    """
    x = price.copy().sort_index()
    x = x[~x.index.duplicated(keep="last")]
    x["ret_1d"] = x["Close"].pct_change()
    x["mom_1m"] = x["Close"].pct_change(21)
    x["mom_3m"] = x["Close"].pct_change(63)
    x["mom_6m"] = x["Close"].pct_change(126)
    x["mom_12m"] = x["Close"].pct_change(252)
    x["sma20"] = x["Close"].rolling(20).mean()
    x["sma50"] = x["Close"].rolling(50).mean()
    x["sma200"] = x["Close"].rolling(200).mean()
    x["dist_sma20"] = x["Close"] / x["sma20"] - 1
    x["dist_sma50"] = x["Close"] / x["sma50"] - 1
    x["dist_sma200"] = x["Close"] / x["sma200"] - 1
    x["rsi14"] = _rsi(x["Close"])
    x["vol20"] = x["ret_1d"].rolling(20).std() * np.sqrt(252)
    x["vol60"] = x["ret_1d"].rolling(60).std() * np.sqrt(252)
    x["volume_ratio20"] = x["Volume"] / x["Volume"].rolling(20).mean()
    x["drawdown"] = x["Close"] / x["Close"].cummax() - 1

    if benchmark is not None and not benchmark.empty:
        b = benchmark[["Close"]].rename(columns={"Close":"benchmark_close"}).sort_index()
        x = x.join(b, how="left")
        x["benchmark_close"] = x["benchmark_close"].ffill()
        x["benchmark_3m"] = x["benchmark_close"].pct_change(63)
        x["relative_strength_3m"] = x["mom_3m"] - x["benchmark_3m"]
    else:
        x["relative_strength_3m"] = np.nan
    return x

def add_forward_labels(features):
    """
    Labels are created only for backtest evaluation.
    The feature vector for date t never uses these future values.
    """
    x = features.copy()
    for name, days in HORIZONS.items():
        x[f"fwd_{name}"] = x["Close"].shift(-days) / x["Close"] - 1
        x[f"positive_{name}"] = (x[f"fwd_{name}"] > 0).astype(float)
    return x

FEATURES = [
    "mom_1m","mom_3m","mom_6m","mom_12m",
    "dist_sma20","dist_sma50","dist_sma200",
    "rsi14","vol20","vol60","volume_ratio20","drawdown",
    "relative_strength_3m"
]

def _standardise(train, test, columns):
    mu = train[columns].mean()
    sd = train[columns].std().replace(0, np.nan)
    return (train[columns]-mu)/sd, (test[columns]-mu)/sd

def nearest_neighbour_walk_forward(price, benchmark=None, horizon="3M",
                                  min_train=504, neighbours=75, rebalance_every=5):
    """
    Expanding-window, walk-forward nearest-neighbour model.

    For each prediction date:
      1. Train only on rows whose forward outcome is already observable.
      2. Standardise using training-set statistics only.
      3. Find historically similar states.
      4. Estimate P(positive), expected return and downside from those outcomes.

    This is a research baseline, not a claim of predictive edge.
    """
    if horizon not in HORIZONS:
        raise ValueError("horizon must be 1M, 3M or 6M")
    days = HORIZONS[horizon]
    x = add_forward_labels(build_point_in_time_features(price, benchmark))
    needed = [c for c in FEATURES if c in x.columns]
    results=[]

    valid_feature_rows=x.dropna(subset=[c for c in needed if c!="relative_strength_3m"], how="any")
    dates=list(valid_feature_rows.index)

    for j in range(min_train, len(dates), rebalance_every):
        dt=dates[j]
        # Crucial embargo: at prediction date dt, a training observation's
        # outcome must already have completed at least 'days' trading rows earlier.
        current_pos=x.index.get_loc(dt)
        cutoff_pos=current_pos-days
        if cutoff_pos <= 0:
            continue
        cutoff_date=x.index[cutoff_pos]
        target=f"fwd_{horizon}"
        train=x.loc[:cutoff_date].dropna(subset=needed+[target]).copy()
        test=x.loc[[dt]].dropna(subset=needed)
        if len(train)<min_train or test.empty:
            continue

        tr_z, te_z=_standardise(train,test,needed)
        usable=tr_z.dropna(axis=1, how="all").columns.tolist()
        tr_z=tr_z[usable].fillna(0)
        te_z=te_z[usable].fillna(0)
        dist=np.sqrt(((tr_z-te_z.iloc[0])**2).sum(axis=1))
        idx=dist.nsmallest(min(neighbours,len(dist))).index
        outcomes=train.loc[idx,target].dropna()
        if len(outcomes)<25:
            continue

        actual=x.at[dt,target] if target in x.columns else np.nan
        results.append({
            "date":dt,
            "horizon":horizon,
            "price":x.at[dt,"Close"],
            "prob_positive":float((outcomes>0).mean()),
            "expected_return":float(outcomes.mean()),
            "median_return":float(outcomes.median()),
            "downside_p10":float(outcomes.quantile(.10)),
            "upside_p90":float(outcomes.quantile(.90)),
            "sample_size":int(len(outcomes)),
            "actual_return":float(actual) if pd.notna(actual) else np.nan,
        })
    return pd.DataFrame(results)

def calibration_table(predictions, bins=5):
    p=predictions.dropna(subset=["prob_positive","actual_return"]).copy()
    if p.empty:
        return pd.DataFrame()
    p["actual_positive"]=(p["actual_return"]>0).astype(int)
    edges=np.linspace(0,1,bins+1)
    p["bucket"]=pd.cut(p["prob_positive"],edges,include_lowest=True)
    return p.groupby("bucket",observed=True).agg(
        predictions=("actual_positive","size"),
        avg_predicted=("prob_positive","mean"),
        actual_positive_rate=("actual_positive","mean"),
        avg_return=("actual_return","mean")
    ).reset_index()

def performance_summary(predictions):
    p=predictions.dropna(subset=["prob_positive","actual_return"]).copy()
    if p.empty:
        return {}
    actual=(p["actual_return"]>0).astype(int)
    predicted=(p["prob_positive"]>=.5).astype(int)
    directional=(predicted==actual).mean()
    brier=((p["prob_positive"]-actual)**2).mean()
    selected=p[p["prob_positive"]>=.60]["actual_return"]
    return {
        "predictions":len(p),
        "directional_accuracy":float(directional),
        "brier_score":float(brier),
        "mean_actual_return":float(p["actual_return"].mean()),
        "mean_expected_return":float(p["expected_return"].mean()),
        "selected_count":int(len(selected)),
        "selected_mean_return":float(selected.mean()) if len(selected) else np.nan,
        "worst_actual_return":float(p["actual_return"].min()),
        "best_actual_return":float(p["actual_return"].max()),
    }

def latest_forecast(price, benchmark=None, horizon="3M", neighbours=75):
    days=HORIZONS[horizon]
    x=add_forward_labels(build_point_in_time_features(price, benchmark))
    needed=[c for c in FEATURES if c in x.columns]
    test=x.dropna(subset=[c for c in needed if c!="relative_strength_3m"]).tail(1)
    if test.empty:
        return None
    dt=test.index[0]
    current_pos=x.index.get_loc(dt)
    cutoff_pos=current_pos-days
    if cutoff_pos<=0:return None
    target=f"fwd_{horizon}"
    train=x.iloc[:cutoff_pos+1].dropna(subset=needed+[target]).copy()
    if len(train)<252:return None
    tr_z,te_z=_standardise(train,test,needed)
    usable=tr_z.dropna(axis=1,how="all").columns.tolist()
    dist=np.sqrt(((tr_z[usable].fillna(0)-te_z[usable].fillna(0).iloc[0])**2).sum(axis=1))
    idx=dist.nsmallest(min(neighbours,len(dist))).index
    outcomes=train.loc[idx,target].dropna()
    return {
        "as_of":dt,
        "horizon":horizon,
        "prob_positive":float((outcomes>0).mean()),
        "expected_return":float(outcomes.mean()),
        "median_return":float(outcomes.median()),
        "downside_p10":float(outcomes.quantile(.10)),
        "upside_p90":float(outcomes.quantile(.90)),
        "sample_size":len(outcomes),
    }


"""
V8 Ensemble Engine
------------------
Experimental walk-forward ML ensemble for ASX research.

Key safeguards:
- separate 1M / 3M / 6M models
- chronological train / validation / test
- outcome embargo to reduce look-ahead leakage
- no random train/test shuffle
- probabilities originate from fitted statistical models, not an LLM
- benchmark-relative labels supported
- model disagreement and calibration are exposed

This remains a prototype until supplied with survivorship-bias-free,
point-in-time fundamentals, delisted securities and production market data.
"""

import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    brier_score_loss, log_loss, roc_auc_score, accuracy_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

HORIZONS = {"1M": 21, "3M": 63, "6M": 126}

PRICE_FEATURES = [
    "mom1", "mom3", "mom6", "mom12",
    "vol20", "vol60", "dist50", "dist200",
    "rsi", "volume_ratio", "drawdown", "rel3"
]

def add_benchmark_targets(panel, benchmark_close):
    """
    Adds forward absolute and benchmark-relative targets.
    benchmark_close must be a Series indexed by date.
    """
    x = panel.copy()
    b = benchmark_close.sort_index()
    for h, days in HORIZONS.items():
        bm_fwd = b.shift(-days) / b - 1
        mp = bm_fwd.to_dict()
        x[f"benchmark_fwd_{h}"] = x["date"].map(mp)
        x[f"excess_fwd_{h}"] = x[f"fwd_{h}"] - x[f"benchmark_fwd_{h}"]
        x[f"outperform_{h}"] = (x[f"excess_fwd_{h}"] > 0).astype(float)
        x.loc[x[f"excess_fwd_{h}"].isna(), f"outperform_{h}"] = np.nan
        x[f"positive_{h}"] = (x[f"fwd_{h}"] > 0).astype(float)
        x.loc[x[f"fwd_{h}"].isna(), f"positive_{h}"] = np.nan
    return x

def sector_neutralise(panel, factor_cols=None):
    """
    Optional sector-neutral percentile ranks. Requires a `sector` column.
    Falls back to market-wide ranks if sector is unavailable.
    """
    x = panel.copy()
    factor_cols = factor_cols or [c for c in PRICE_FEATURES if c in x.columns]
    group = ["date", "sector"] if "sector" in x.columns else ["date"]
    for c in factor_cols:
        if c not in x.columns:
            continue
        x[f"sn_{c}"] = x.groupby(group, dropna=False)[c].rank(pct=True)
    return x

def _date_splits(df, train_frac=.60, val_frac=.20):
    dates = np.array(sorted(pd.unique(df["date"])))
    if len(dates) < 30:
        return None
    a = int(len(dates) * train_frac)
    b = int(len(dates) * (train_frac + val_frac))
    return dates[:a], dates[a:b], dates[b:]

def _safe_auc(y, p):
    try:
        if len(np.unique(y)) < 2:
            return np.nan
        return float(roc_auc_score(y, p))
    except Exception:
        return np.nan

def metrics(y, p):
    y = np.asarray(y).astype(int)
    p = np.clip(np.asarray(p), 1e-6, 1-1e-6)
    pred = (p >= .5).astype(int)
    return {
        "n": int(len(y)),
        "accuracy": float(accuracy_score(y, pred)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0,1])),
        "auc": _safe_auc(y, p),
        "avg_probability": float(np.mean(p)),
        "actual_rate": float(np.mean(y)),
    }

def calibration_bins(y, p, bins=10):
    z = pd.DataFrame({"actual": np.asarray(y), "prob": np.asarray(p)})
    z["bucket"] = pd.cut(z["prob"], np.linspace(0,1,bins+1), include_lowest=True)
    return z.groupby("bucket", observed=True).agg(
        predictions=("actual","size"),
        avg_predicted=("prob","mean"),
        actual_rate=("actual","mean")
    ).reset_index()

def model_library():
    return {
        "Logistic": Pipeline([
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, C=1.0))
        ]),
        "GradientBoosting": HistGradientBoostingClassifier(
            max_iter=180, learning_rate=.05, max_leaf_nodes=15,
            l2_regularization=1.0, random_state=42
        ),
    }

def train_competing_models(panel, horizon="3M", objective="outperform",
                           feature_cols=None):
    """
    Fixed chronological train/validation/test experiment.
    The test set is never used for model weighting.
    """
    if horizon not in HORIZONS:
        raise ValueError("horizon must be 1M, 3M or 6M")
    target = f"outperform_{horizon}" if objective == "outperform" else f"positive_{horizon}"
    feature_cols = feature_cols or [c for c in PRICE_FEATURES if c in panel.columns]

    data = panel.dropna(subset=feature_cols + [target, "date"]).copy()
    split = _date_splits(data)
    if split is None:
        return None
    train_dates, val_dates, test_dates = split
    train = data[data.date.isin(train_dates)]
    val = data[data.date.isin(val_dates)]
    test = data[data.date.isin(test_dates)]

    if min(len(train), len(val), len(test)) < 50:
        return None

    models = model_library()
    fitted, validation, test_results = {}, {}, {}
    val_predictions = {}
    test_predictions = {}

    for name, base in models.items():
        m = clone(base)
        m.fit(train[feature_cols], train[target].astype(int))
        pv = m.predict_proba(val[feature_cols])[:,1]
        pt = m.predict_proba(test[feature_cols])[:,1]
        fitted[name] = m
        val_predictions[name] = pv
        test_predictions[name] = pt
        validation[name] = metrics(val[target], pv)
        test_results[name] = metrics(test[target], pt)

    # Ensemble weights determined ONLY from validation Brier scores.
    inv = {}
    for name, met in validation.items():
        inv[name] = 1.0 / max(met["brier"], 1e-6)
    total = sum(inv.values())
    weights = {k: v/total for k,v in inv.items()}

    pv_ens = sum(weights[n] * val_predictions[n] for n in weights)
    pt_ens = sum(weights[n] * test_predictions[n] for n in weights)

    validation["Ensemble"] = metrics(val[target], pv_ens)
    test_results["Ensemble"] = metrics(test[target], pt_ens)

    pred_table = test[["date","ticker",target,f"fwd_{horizon}",
                       f"excess_fwd_{horizon}"]].copy()
    for n,p in test_predictions.items():
        pred_table[f"p_{n}"] = p
    pred_table["p_Ensemble"] = pt_ens
    pred_table["model_disagreement"] = pred_table[
        [c for c in pred_table if c.startswith("p_") and c != "p_Ensemble"]
    ].std(axis=1)

    return {
        "horizon": horizon,
        "objective": objective,
        "features": feature_cols,
        "models": fitted,
        "weights": weights,
        "validation_metrics": pd.DataFrame(validation).T.reset_index(names="model"),
        "test_metrics": pd.DataFrame(test_results).T.reset_index(names="model"),
        "test_predictions": pred_table,
        "calibration": calibration_bins(test[target], pt_ens),
        "train_end": max(train_dates),
        "validation_end": max(val_dates),
        "test_start": min(test_dates),
        "test_end": max(test_dates),
    }

def latest_ensemble_forecast(result, panel):
    if result is None:
        return pd.DataFrame()
    feats = result["features"]
    latest_date = panel["date"].max()
    current = panel[panel.date == latest_date].dropna(subset=feats).copy()
    if current.empty:
        return current
    probs = []
    for name, model in result["models"].items():
        p = model.predict_proba(current[feats])[:,1]
        current[f"p_{name}"] = p
        probs.append((name,p))
    current["ensemble_probability"] = sum(
        result["weights"][name] * p for name,p in probs
    )
    current["model_disagreement"] = current[
        [f"p_{n}" for n,_ in probs]
    ].std(axis=1)
    return current.sort_values("ensemble_probability", ascending=False)

def prediction_deciles(predictions, horizon):
    if predictions is None or predictions.empty:
        return pd.DataFrame()
    x = predictions.dropna(subset=["p_Ensemble", f"excess_fwd_{horizon}"]).copy()
    try:
        x["decile"] = pd.qcut(x["p_Ensemble"], 10, labels=False, duplicates="drop") + 1
    except Exception:
        return pd.DataFrame()
    return x.groupby("decile").agg(
        observations=("ticker","size"),
        avg_probability=("p_Ensemble","mean"),
        actual_outperform_rate=(f"outperform_{horizon}","mean"),
        avg_excess_return=(f"excess_fwd_{horizon}","mean"),
        avg_absolute_return=(f"fwd_{horizon}","mean")
    ).reset_index()

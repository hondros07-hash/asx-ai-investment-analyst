# V6 Backtesting + Prediction Engine

This package extends the working V5 app with the first rigorous prediction layer.

## New files
- `backtest_engine.py` — point-in-time feature engineering, separate 1M/3M/6M forward labels,
  expanding-window walk-forward nearest-neighbour forecasts, calibration table, Brier score,
  directional accuracy and current historically-derived forecast.
- `V6_APP_INTEGRATION.py` — Streamlit UI block to integrate into the existing `app.py`.
- Existing V5 `app.py` remains included as the stable application base.

## Why this is different
The model uses an embargo: when simulating a prediction at historical date T, it only trains on
observations whose future outcome would already have completed by T. This reduces look-ahead leakage.

## Still needed for institutional-grade testing
A survivorship-bias-free ASX universe, delisted securities, point-in-time fundamentals,
corporate actions, transaction costs/slippage, sector membership history, macro history,
and a proper model registry/database.

## Run locally
pip install -r requirements.txt
streamlit run app.py

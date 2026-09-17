# V19.4 - Phase 5: Advanced Forecasting

Adds a second-generation, explainable forecasting research framework while retaining
the transparent historical scenario model.

Features:
- 1M / 3M / 6M / 12M advanced forecasts
- deterministic 3-model ensemble:
  - ridge regression
  - momentum model
  - historical median model
- lagged features only:
  - 1W / 1M / 3M / 6M / 12M returns
  - 21D / 63D annualised volatility
  - 20D / 50D / 200D moving-average gaps
  - 252D drawdown
- expanding-window walk-forward validation
- out-of-sample MAE / RMSE
- direction accuracy
- return correlation
- historical 20th / 80th outcome bands
- trend + volatility regime context
- calibration diagnostic based on historical out-of-sample observations
- no claim that historical positive frequency is a calibrated future probability
- dedicated Advanced Forecasting workspace
- integrated into Company Command Centre -> Forecasts
- integrated into Research Tools

Data-integrity decision:
Current fundamental, analyst and report fields are kept separate from the predictive
price model unless reliable point-in-time historical versions are available. This
prevents current/future information from leaking into historical backtests.

All Phase 1-4 functionality remains included.

Deployment diagnostic:
V19.4 • Market Investment Analyst • Advanced Forecasting

# Market Investment Analyst V8 — Competing ML Models + Ensemble

V8 adds the first statistical competing-model architecture.

## New engine
`ensemble_engine.py`

It implements:
- separate 1M / 3M / 6M classification targets
- positive-return or ASX-200-outperformance objectives
- chronological 60% train / 20% validation / 20% unseen test
- Logistic Regression model
- nonlinear Histogram Gradient Boosting model
- validation-Brier-weighted ensemble
- Brier score
- log loss
- ROC-AUC
- directional accuracy
- calibration bins
- probability decile analysis
- model disagreement
- latest universe probabilities
- optional sector-neutral factor ranks if sector history is supplied

## Critical limitation
This is currently a price/volume ML ensemble. It does NOT inject today's fundamentals into
historical observations. Doing so would contaminate the backtest.

## What V9 should add
1. Point-in-time financial statements and filing dates
2. Fundamental factors: ROE, ROIC, margins, FCF, leverage, accruals
3. Valuation factors: P/E, EV/EBITDA, FCF yield, P/S and sector-specific valuation
4. Earnings revisions / estimate history
5. Macro and commodity point-in-time factors
6. Sector membership history and sector-neutral modelling
7. Delisted stocks / survivorship-bias-free universe
8. Liquidity, turnover, slippage and transaction-cost modelling
9. Rolling walk-forward retraining rather than one fixed split
10. Model registry, prediction ledger and drift monitoring

The statistical probability layer should remain separate from the LLM research layer.

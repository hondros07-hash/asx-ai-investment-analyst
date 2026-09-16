# ASX AI Investment Analyst V7 — Multi-Stock Factor Lab

V7 adds a multi-stock ASX research universe and cross-sectional strategy testing.

## New
- `universe_engine.py`
  - batch multi-ticker download
  - point-in-time price/volume feature panel
  - cross-sectional percentile factor scores
  - 1M / 3M / 6M strategy tests
  - transaction-cost assumption
  - latest universe ranking
  - hit rate, compounded return and drawdown summary
- `V7_APP_INTEGRATION.py`
  - Streamlit interface block
- V6 backtester remains included.

## Methodological boundary
This version intentionally labels value/quality/growth fields as proxies where point-in-time
fundamental history is unavailable. It does not pretend current fundamentals existed historically.

## V8 target
Replace proxies with point-in-time fundamentals/valuation, add sector neutrality, delisted stocks,
survivorship-bias controls, benchmark-relative alpha, turnover, liquidity/slippage, macro regimes,
proper train/validation/test ML and calibrated ensemble probabilities.

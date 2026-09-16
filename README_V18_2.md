# V18.2 — Forecast + Analyst Consensus

Adds a Forecast Research workspace for 1M, 3M, 6M and 12M horizons, including
median scenario price, 20th/80th percentile historical cases, historical
positive-return frequency and sample size.

Adds external analyst consensus from Yahoo Finance via yfinance when available:
Strong Buy / Buy / Hold / Sell / Strong Sell counts plus low, mean, median and
high analyst price targets. The analyst label is explicitly external consensus,
not the app's recommendation.

The forecast is deliberately labelled research: it uses recency-weighted
historical forward-return distributions and does not describe historical
frequency as a calibrated probability of future returns.

Deployment diagnostic:
V18.2 • Market Investment Analyst • forecast + analyst consensus

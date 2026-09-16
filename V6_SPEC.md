# V6 FULL UPGRADE SPECIFICATION

Required engines:
- Fundamental: revenue, earnings, margins, ROE/ROIC/ROA, debt, FCF, balance sheet, growth.
- Valuation: DCF, P/E, EV/EBITDA, EV/FCF, PEG, FCF yield, peers, historical ranges.
- Quant: momentum, volatility, correlation, beta, Sharpe, Sortino, drawdown, value/quality/growth/size/momentum factors, mean reversion, relative strength.
- Technical: RSI, MACD, moving averages, Bollinger Bands, volume, trend.
- Macro/Commodity: gold, oil, copper, lithium, rates, inflation, AUD/USD, yields, economic indicators.
- AI Research: annual reports, ASX announcements, earnings, news, management commentary, industry.
- Prediction: separate 1M, 3M, 6M models; probability positive, expected return, downside, benchmark outperformance.
- Validation: training/validation/unseen test, point-in-time data, no look-ahead bias, calibration, directional accuracy, excess return, drawdown, Sharpe, Sortino, hit rate, P/L ratio, false positives/negatives.
- Competing models: fundamental, factor, technical, macro, commodity, ML, valuation, then ensemble.
- Prediction ledger and model performance dashboard.
- Explain changes in forecasts and show drivers.

Additional production requirements identified:
- licensed real-time ASX data/order book
- point-in-time ASX announcements and financial reports
- survivorship-bias-free universe including delisted securities
- corporate-action/split/dividend adjustments
- point-in-time fundamentals
- transaction costs, slippage and liquidity
- benchmark/sector-relative returns
- model drift and version registry
- source provenance and timestamps
- missing-data/confidence handling
- security/secrets, caching, retries and audit logs
- portfolio risk, correlation, concentration and alerts

Critical methodology rule:
Do not allow an LLM to invent statistical probabilities. 1/3/6-month probabilities must come from validated out-of-sample quantitative models.

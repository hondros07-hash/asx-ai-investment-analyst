# V19.1 — Phase 2 Research Intelligence

Adds the second layer of the Global Investment Research terminal.

## Deep company panel
Available from Markets and Company Command Centre with tabs for:
- Market
- Performance & Forecast
- Analysts
- Forecast Drivers
- Market Disagreement
- Evidence

## Richer analyst evidence
- analyst rating distribution
- target range
- recent dated upgrades/downgrades when supplied by Yahoo/yfinance
- external analyst evidence remains explicitly separate from app models

## Explainable forecast context
- 1M / 3M / 6M / 12M trailing momentum
- price vs 50D / 200D averages
- volume participation
- provider-reported revenue/earnings/margin/leverage observations
- no claim that these are hidden model weights

## Market disagreement
Compares market price with:
- analyst mean target
- quantitative 12M scenario
- user-model DCF
and identifies the largest measurable disagreement without declaring a winner.

## Evidence provenance
Each research panel explains where market, analyst, quant, DCF and fundamental observations come from.

Important:
- historical positive-return frequency is NOT labelled as a calibrated future probability
- DCF depends on user assumptions
- material fundamental data should be verified against company filings

Deployment diagnostic:
V19.1 • Market Investment Analyst • Phase 2 Research Intelligence

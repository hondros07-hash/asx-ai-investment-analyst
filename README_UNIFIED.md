# Market Investment Analyst — Unified Build

This package consolidates the V6–V10 research architecture and adds the remaining major
calculation/framework layers identified in the design review.

## Newly added in the Unified Build
- Earnings expectations / surprise engine
- Reverse DCF / market-implied growth
- Research confidence / data-health engine
- Thesis-change comparison engine
- Sector-specific KPI models
- Liquidity / transaction-cost helpers
- Peer-selection engine
- Market-breadth engine
- Persistent local watchlist
- Unified Streamlit `app.py`

## Retained
All V6, V7, V8, V9 and V10 engines/integration modules are retained in the package.

## Important: what cannot be truthfully bundled as code alone
Institutional-grade operation still requires external data/infrastructure:
licensed ASX real-time/order-book data, official announcement/document feeds,
survivorship-bias-free/delisted history, point-in-time fundamentals and estimates,
historical sector membership, corporate actions, short interest/director transactions,
persistent cloud database, authentication, scheduled alerts and production observability.

Those are now explicit provider/infrastructure dependencies rather than missing analytical ideas.

## Recommended next step
Run and debug the unified app in your Streamlit deployment, then connect production data providers
one by one. Do not add more model complexity until the point-in-time dataset and backtest controls
are reliable.

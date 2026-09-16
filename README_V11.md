# V11 — Serious Investment Research System

V11 moves the project from dashboard expansion toward evidence-first investment research.

## Added
- Dedicated Research Report workspace.
- Fundamental and valuation snapshot.
- Automatic sector/industry-specific KPI framework.
- Peer fundamental and valuation comparison.
- Price, momentum and risk section.
- Thesis stress-test framework.
- Evidence/data-quality register.
- Explicit research-gap reporting.
- Forecast discipline: probabilities are withheld until validated rather than invented.
- `validation_engine.py` with purged chronological splitting and non-overlapping forward-return utilities for the next modelling stage.

## Data integrity
Yahoo/yfinance remains a research/prototype source in this build. Provider fundamentals can be incomplete or differently defined and must be checked against primary filings for material decisions.

## Still required for institutional-grade production
Official ASX/SEC filings and announcements; point-in-time financials; consensus estimates; licensed production pricing; corporate actions; delisted/survivorship-safe universes; validated/calibrated forecast models; persistent production database and authentication.

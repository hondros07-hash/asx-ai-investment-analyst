# Market Investment Analyst V9

V9 builds the point-in-time data bridge required before historical fundamentals can safely enter the ML ensemble.

## Added
- `point_in_time_engine.py`
- `macro_factor_engine.py`
- `v9_ensemble_engine.py`
- `V9_APP_INTEGRATION.py`
- `point_in_time_fundamentals_TEMPLATE.csv`

## What V9 does
- Enforces `available_date >= period_end`
- Joins financial information only after it was publicly available
- Winsorises cross-sectional factor outliers
- Supports sector-neutral z-scores when sector labels exist
- Builds fundamental-quality, growth, valuation and revision factors
- Extends the V8 ensemble with genuine PIT factors when enough observations exist
- Retains chronological train / validation / unseen test evaluation
- Keeps statistical probabilities separate from the LLM

## Important
The package supplies the ENGINE and schema, not a commercial historical-fundamentals database.
Yahoo's current statements must not be backfilled into historical dates.

To make V9 fully populated across the ASX, connect a provider/database that supplies:
- historical statements
- filing/release dates
- historical valuation observations
- estimate/revision history
- delisted companies
- sector membership history
- corporate actions

## V10 target
Automated evidence ingestion + source provenance + ASX announcement/report parser +
macro/commodity historical adapters + prediction registry/drift + portfolio/watchlist monitoring.

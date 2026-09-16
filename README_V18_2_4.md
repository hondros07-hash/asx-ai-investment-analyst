# V18.2.4 — Forecast Chart Hotfix

Fixes:
ValueError: All arrays must be of the same length

Root cause:
The forecast chart always created a five-item month axis `[0,1,3,6,12]` before
checking how many forecast horizons actually had valid results. If a horizon was
unavailable, the price array was shorter and pandas raised ValueError before the
fallback code could run.

Fix:
- builds Months and Price together from only valid forecast horizons
- preserves the current price as month 0
- supports any subset of 1M / 3M / 6M / 12M
- validates equal array lengths before DataFrame creation
- gracefully omits the chart if no valid forecast path exists
- forecast table remains available
- retains V18.2.3 responsive metric-card fix and all earlier features

Deployment diagnostic:
V18.2.4 • Market Investment Analyst • forecast chart hotfix

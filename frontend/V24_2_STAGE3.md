# AXÍA V24.2 — Stage 3: Global Research Workspace

## Migrated navigation and boundaries
- Global Markets: seven exchange index snapshots from provider daily bars, explicitly not real-time.
- Screening: user-entered company discovery filtered by provider exchange/suffix. This is not exhaustive exchange coverage or a fundamentals screener.
- Research Tools: links to existing company valuation, forecast and screening workflows.
- Calendar: route to per-company provider catalysts; consolidated calendar is pending.
- Watchlist, Portfolio and Alerts: dedicated private-workspace routes with honest migration states. No cross-user or unauthenticated persistence and no invented holdings, alert execution or notification delivery.

## Acceptance
Run `python -m pytest tests/test_v242_workspace.py`, existing Python tests, then `cd frontend && npm run lint && npm run build`. Verify all seven market routes and search exchange filtering against actual listings; test API timeout, missing bars, mobile navigation and cross-market ticker identity. Check Stage 1/2 regression and that no personal records leak into static or cached pages.

## Remaining before production
Stage 4 must implement and verify authentication, per-user persistence and migration of saved watchlists, holdings, alerts and calendar entries; provider-grade market screening and a consolidated calendar also remain outstanding. Do not cut over from Streamlit or claim feature parity based on this navigation milestone.

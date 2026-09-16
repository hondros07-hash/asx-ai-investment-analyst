# V18.0.2 — Full Schema Migration Hotfix

The latest traceback occurs in `kpi_observations()` while the attention queue
loads KPI evidence. This means the deployed SQLite database contains an older
or partially-created `kpi_observations` table.

V18.0.2:
- migrates every column required by `kpi_observations`
- migrates valuation_profiles and report_reviews
- also checks V17 portfolio/thesis/review tables
- keeps the V18.0.1 catalysts/thesis/alerts migrations
- makes KPI reads fail-safe so an unexpected transitional database cannot
  crash Company Command Centre
- smoke-tested against an intentionally incomplete KPI table
- compiled with zero Python syntax errors

Version diagnostic:
V18.0.2 • Market Investment Analyst • full schema migration hotfix

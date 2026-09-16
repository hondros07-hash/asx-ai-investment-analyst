# V18.0.1 — SQLite Schema Migration Hotfix

Fixes the deployed Command Centre crash shown in the traceback when querying:
`event_date, event, category, status, source FROM catalysts`.

Cause:
An older `catalysts` table can already exist in Streamlit Cloud. SQLite
`CREATE TABLE IF NOT EXISTS` does not retrofit new columns into an existing table.

Fix:
- Adds forward-compatible column migrations for catalysts, thesis_rules and alerts.
- Adds `catalysts_safe()` so catalyst display cannot crash the Command Centre.
- Replaces direct catalyst SELECTs in Company Command Centre and Before I Invest.
- Preserves V18 features and V17 navigation/database fixes.
- Migration smoke-tested against an intentionally old SQLite catalysts schema.

Deployment diagnostic:
`V18.0.1 • Market Investment Analyst • schema migration hotfix`

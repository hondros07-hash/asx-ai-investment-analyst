# V17.1.1 — Database Hotfix

Fixes the Before I Invest / Monitor My Thesis crash where attention_items()
called thesis_table() before the V17 database-upgrade schema was guaranteed
to exist.

Changes:
- thesis_table() now self-initialises the V17 schema.
- safe empty thesis DataFrame if the table query cannot be read.
- SQLite connection timeout increased for prototype cloud robustness.
- preserves V17.1 simplified navigation.

Deployment diagnostic:
The app caption must show:
V17.1.1 • Market Investment Analyst • navigation + database hotfix

If the sidebar still shows the old long list or the caption says V17, the new
app.py has not been deployed.

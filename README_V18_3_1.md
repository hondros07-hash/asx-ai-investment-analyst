# V18.3.1 — Thesis Scorecard Hotfix

Fixes the Thesis Scorecard crash shown on Streamlit Cloud.

- Runs the V18 database migration before reading thesis rules.
- Replaces the failing pandas SQL read on this page with direct SQLite execution.
- Hardens the shared thesis loader in the same way.
- Preserves the existing database; no deletion/reset is required.
- Retains V18.3 dynamic company branding and all previous fixes.

Deployment diagnostic:
V18.3.1 • Market Investment Analyst • thesis scorecard hotfix

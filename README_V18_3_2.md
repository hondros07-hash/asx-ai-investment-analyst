# V18.3.2 — Runtime Hotfix

Fixes both Streamlit Cloud errors reported after V18.3.1.

1. Catalyst Calendar
- migrates the retained database before reading catalysts
- replaces the direct pandas SQL read with robust SQLite execution
- preserves existing catalyst records

2. Forecasts
- fixes `NameError: df is not defined`
- passes the application's loaded historical market dataframe `h` to the forecast renderer

Retains all V18.3.1 and earlier fixes.

Deployment diagnostic:
V18.3.2 • Market Investment Analyst • runtime hotfix

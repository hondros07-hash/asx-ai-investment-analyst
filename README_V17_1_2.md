# V17.1.2 — Company Command Centre Hotfix

Fixes the NameError shown on Company Command Centre:
`cls = classify_company(ticker)`

Cause:
The V16 Command Centre/KPI workflow called `classify_company()` but the
deployed app did not contain a guaranteed definition for that helper.

Fix:
- adds a stable `classify_company(ticker)` helper before page execution
- reads sector/industry/name from the existing yfinance provider when available
- safely returns blank classification metadata if the provider call fails
- preserves V17.1 simplified navigation
- preserves V17.1.1 database hotfix

Deployment diagnostic:
The app caption should show:
V17.1.2 • Market Investment Analyst • command centre hotfix

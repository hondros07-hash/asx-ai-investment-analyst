# V17.1.3 — Classification Hotfix

Fixes both NameError paths shown in:
1. Company Command Centre
2. Before I Invest → Company KPI checklist

Both pages were directly calling `classify_company(ticker)`. V17.1.3 routes
both through `safe_company_classification(ticker)`, which always returns a
valid dictionary and treats provider metadata as optional enrichment.

Also hardens the KPI template so ticker/name classification still works if
sector/industry metadata is unavailable.

Deployment diagnostic:
`V17.1.3 • Market Investment Analyst • classification hotfix`

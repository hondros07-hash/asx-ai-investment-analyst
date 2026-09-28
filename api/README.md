# AXÍA Phase 2 — FastAPI backend

The existing Streamlit application is unchanged. This API imports the Streamlit-free
`services.fundamentals_core` and existing financial calculation engines.

## Run locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --host 127.0.0.1 --port 8000
pytest -q tests/test_api_contract.py
```

Interactive OpenAPI documentation: http://127.0.0.1:8000/docs

## Endpoints

- `GET /health`
- `GET /v1/companies/search?q=QAN&limit=10`
- `GET /v1/companies/QAN.AX/financial-statements?period=Annual%20(5Y)`
- `GET /v1/companies/QAN.AX/kpis?period=Annual%20(5Y)`
- `GET /v1/companies/QAN.AX/valuation`
- `POST /v1/valuations/dcf` (explicit financial inputs; verified FX required for currency mismatch)
- `GET /v1/companies/QAN.AX/forecast`
- `POST /v1/forecasts/12m` (ticker and optional current_price)

Financial statements and KPI endpoints share a bounded one-hour in-process cache,
keyed by ticker and reporting period. A server restart resets the cache. Source and
provider-check time are included. Company valuation uses existing DCF assumptions
and may return unavailable or unsupported. Forecasts use the existing 12-month
engine and return unavailable when sufficient price history is absent. No invented
price targets, exchange listing verification or filing reconciliation.

## Production prerequisites

This is a local/development API foundation, **not** a production-ready public service.
Before exposing it to the internet add authentication, per-client rate limits,
CORS allowlist for axiaindex.com, provider request quotas, monitoring, structured
logs, secret management, shared Redis cache and worker-level request limits.
Provider requests are bounded by a 20-second caller timeout; the underlying
thread cannot forcibly interrupt an in-flight provider request. Review provider
licensing before redistribution. Run live-provider smoke tests before deployment.

The specialised Operating Income engine from PR #142 is used automatically when
that PR is merged; until then this branch uses the independent KPI implementation
currently on main. Phase 1 separation is incremental, not a claim that all
Streamlit modules have been migrated.

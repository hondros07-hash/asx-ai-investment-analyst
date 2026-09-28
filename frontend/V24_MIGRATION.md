# AXÍA V24 — Frontend migration, stage 1

The Next.js frontend is a separate deployment. The existing Streamlit app remains the production reference; **do not switch axiaindex.com to Next.js** until route parity, data verification and staging acceptance are complete.

## Connected routes
- Home → Search → exact listing Company Command Centre.
- Overview: real API KPIs and shared statement context.
- Fundamentals: annual, quarterly and TTM KPIs plus financial statements, provider provenance and integrity notices.
- Finance: financial statements and the existing valuation API output, with assumptions available for inspection.
- Forecasts: existing 12-month forecast API response with model attribution.
- Other Command Centre sections remain clearly labelled pending, with no invented figures.

## Technical boundaries
- API requests are server-side through AXIA_API_URL, never embedded credentials in the browser.
- Ticker and reporting period are URL-scoped; unsupported period values fall back to Annual (5Y).
- API failures show explicit error states rather than stale or simulated data.
- Existing FastAPI engines remain the source of calculations. The frontend does not recompute financial ratios or forecasts.
- Company research remains noindex; public SEO pages remain separate.

## Acceptance gates before production cutover
1. Run `npm install && npm run lint && npm run build` from `frontend/`; run the existing Python API tests.
2. Start API with `uvicorn api.main:app --host 127.0.0.1 --port 8000`, set AXIA_API_URL and start Next.js in staging.
3. Compare ZIP.AX, KO and QAN.AX against Streamlit and issuer disclosures for identity, currency, period labels, KPI values and source timestamps.
4. Verify empty provider data, API timeouts and unsupported tickers never display made-up numbers.
5. Test Home → Search → Overview → Fundamentals → Finance → Forecasts, including browser back/forward and mobile navigation.
6. Migrate Technical, Announcements, Report Intelligence, News, Thesis, Catalysts and Quant with independent verified API contracts before cutover.
7. Validate accessibility, performance, authentication and domain/SEO behaviour. Streamlit remains available until sign-off.

# AXÍA Phase 3 — Next.js frontend foundation

The existing Streamlit site remains unchanged. This frontend uses the Phase 2 FastAPI routes from PR #144.

## Local development

Start backend at repository root:
```bash
pip install -r requirements.txt
uvicorn api.main:app --host 127.0.0.1 --port 8000
```
Start frontend in another terminal:
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Open http://localhost:3000. Verify `npm run lint` and `npm run build` before merging.

## Migrated in this first frontend slice

- Responsive AXÍA banner, sidebar and company subnavigation with URL-based active states.
- Home and API-backed company search; company-specific document title.
- Company Command Centre route structure for 11 research sections.
- Five API-backed financial KPI cards with source dates, actual reported historical bars, local unavailable states and no synthetic numbers.
- Server-side API URL configuration and no client-exposed provider keys.

## Not yet migrated

The existing Streamlit banner/sidebar are recreated as a baseline, **not pixel-verified**. Technical, filings, reports, news, thesis, catalysts, quant, forecasts and finance routes are placeholders, not working copies. The full Home market ribbon, search Quick View, company logo resolver, DCF/forecast visual cards, and other widgets need separate component migrations. Existing Streamlit remains the reference until visual and financial parity tests pass.

## Before production

Merge PR #144 first, run both services, add frontend/backend authentication, shared rate limits and provider quotas, review data redistribution rights, configure server-only API URL, monitor API failures and verify against the current site. Do not point axiaindex.com to this scaffold yet.

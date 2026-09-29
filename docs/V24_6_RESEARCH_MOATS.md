# AXÍA V24.6 — Research Memory & Thesis Monitoring Foundation

This is an additive, non-deployed foundation. It does not change Streamlit, Next.js routes, existing API responses, DNS or production state.

## Product objective
Preserve the investor's research history and measurable thesis conditions, connect observations to source evidence, and show changes between dated snapshots. Never manufacture a buy/sell decision.

## Included
- Provider-independent evidence fingerprinting and deterministic snapshot comparison.
- Measurable condition evaluation with explicit unverified states for missing/mismatched observations.
- SQL schema for owner-scoped research snapshots, thesis conditions and observations, with Supabase row-level security.
- Unit tests for identity, currency, period, evidence and change detection.

## Not yet included — do not claim these are live
- Applied database migration or live Supabase credentials.
- Authenticated CRUD routes and UI for saved thesis conditions.
- Scheduled provider ingestion, official filing parsing or push notifications.
- Automatic migration of existing Streamlit user state.
- Full provider licensing, data provenance validation or backtest remediation.

## Next gate
Review SQL and user grants; test RLS with two distinct authenticated accounts and anon; implement token-verified API endpoints; add idempotent ingestion and source timestamps; then integrate a dedicated Thesis History view and What Changed panel. Keep all new routes behind an explicit feature flag until end-to-end security tests pass.

# AXÍA V24.7 — Authenticated Research History (integration stage)

Additive API and discoverable Research Memory page. The API is OFF by default via AXIA_RESEARCH_MEMORY_ENABLED. It uses a per-request Supabase anon/publishable client, verifies the supplied bearer token with Supabase Auth, sets that token on PostgREST, and filters owner ID in addition to database RLS. No service-role client is used.

API: GET/POST /v1/research-memory/snapshots; GET /changes; GET/POST /conditions; POST /conditions/{id}/evaluate. Evaluation is read-only and does not claim to persist monitoring. The page is an honest introduction, not a completed account interface.

**Release gates before enabling:** Apply and review V24.6 schema; verify DB grants and RLS with two real users and anonymous role; implement secure browser session flow and UI; validate source provenance and date parsing; add storage quota/rate limiting and retention policy; integration-test Supabase responses; run staging load tests. No SQL is applied and no production cutover occurs in this PR.

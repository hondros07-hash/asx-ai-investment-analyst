# AXÍA V24.9 — Personalised Research History & Switching Costs

Additive fourth moat foundation: owner-scoped thesis, note, decision and review entries, immutable revision linkage, and a per-security timeline combining journal events and dated snapshots.

API: GET/POST /v1/research-journal/entries and GET /v1/research-journal/timeline. All endpoints reuse the verified bearer-token session and AXIA_RESEARCH_MEMORY_ENABLED flag; off by default. Do not put secrets in frontend code.

The SQL migration is not applied by this PR. A browser editor, automated monitoring, account export, verified evidence attachment, and real multi-account RLS tests are not included. Do not market this as live personalisation.

Before activation: review DB grants, run two-account and anonymous RLS tests, check revision trigger permissions, implement CSRF-safe session handling, request limits, data export/deletion and retention controls. Keep existing Streamlit and production deployment unchanged.

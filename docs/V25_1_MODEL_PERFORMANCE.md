# AXÍA V25.1 — Proprietary Model Performance & Research Data

Sixth moat foundation: deterministic point-in-time forecast fingerprint, fixed issue and target dates, model version, reference price, assumptions/source digests and explicit outcome evaluation. A forecast cannot be evaluated before its horizon; an outcome must be verified, dated, currency/security matched and sourced. Missing results are not wins. Aggregate summaries show sample sizes and are descriptive only.

POST /v1/model-accountability/freeze and /evaluate are **stateless calculation endpoints**. They do not store forecasts, fetch prices, verify the contents of external URLs, or establish an actual performance record. Caller-supplied verified=true is not independent verification. Do not publish a live performance claim from these endpoints.

Next release gates: append-only authenticated storage with owner RLS, trusted historical price adapter, corporate-action adjusted prices, exchange calendars and observation windows, walk-forward model version pinning, duplicate prevention, survivor-bias audit, minimum sample sizes and performance dashboard. No production deployment or migration in this PR.

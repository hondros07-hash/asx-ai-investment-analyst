# AXÍA V24.8 — Explainable Financial Intelligence & Evidence Engine

Third moat foundation. Adds a deterministic, source-aware evidence contract and bounded arithmetic explanation API. No AI text is invented. Provider-transcribed values cannot claim issuer verification without explicit reconciliation. Missing values are unavailable, not zero. Each input includes security, metric, period, unit, source URL, observed time, verification status and deterministic fingerprint.

Endpoint: POST /v1/explainability/calculate. It performs arithmetic only on caller-supplied evidence; it does not fetch market data or validate that a submitted URL actually contains the submitted number. **It is not a trusted issuer verification service.**

Next steps: integrate evidence adapters with issuer filings and existing KPI/valuation engines, independently verify document-page references, enforce input-output unit algebra for multiplication/division, implement browser evidence drawer, and add API request throttling before public exposure. No existing widget, DNS, database schema or deployment configuration is changed.

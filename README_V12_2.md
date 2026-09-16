# V12.2 — SEC Document Retrieval Fix

Fixes the error shown when opening SEC filings such as Form 4:
- SEC `primaryDocument` values can include display/XSL paths such as `xslF345X06/form4.xml`.
- V12.2 converts those to the raw archive document (`form4.xml`) for programmatic retrieval.
- If the primary document cannot be retrieved, it falls back to the filing index.
- XML filings are converted to readable text for evidence summaries.
- SEC filing titles are human-readable (e.g. `Insider Transaction (Form 4)`).
- SEC filings display `N/A (SEC filing)` instead of implying an ASX-style price-sensitive flag.

ASX remains provider-dependent for CommSec-style complete coverage.

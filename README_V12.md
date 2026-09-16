# V12 — Announcements Intelligence Engine

Architecture:
- ASX: provider adapter first; public ASX historical archive only as fallback.
- US: SEC EDGAR.
- Normalized announcement schema: date, category, headline, price-sensitive flag, source, URL, ID.
- Filters by announcement category and free text.
- Original document retrieval.
- Evidence-based document summary.
- Download original PDF/filing.

For CommSec-style complete and reliable ASX coverage, configure an authorised ASX ComNews-capable provider:
`ASX_ANNOUNCEMENTS_API_URL` and `ASX_ANNOUNCEMENTS_API_KEY` in Streamlit Secrets.

The generic provider adapter expects JSON with a `results` or `data` array and common fields such as:
`filing_date/date`, `title/headline`, `document_type`, `pdf_url/url`, `is_price_sensitive`, `announcement_number/id`.

The public ASX archive remains a fallback, not the production-grade feed.
